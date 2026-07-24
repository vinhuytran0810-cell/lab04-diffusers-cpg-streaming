from __future__ import annotations

import ast
import tokenize
from pathlib import Path
from typing import Any, Iterator

from src.parser.ast_extractor import ASTExtractor
from src.parser.id_generator import stable_id
from src.parser.parser_service import REPOSITORY_NAME, build_metadata

from .cfg_builder import build_cfg
from .dfg_builder import build_dfg


def _walk_preorder(node: ast.AST) -> Iterator[ast.AST]:
    """
    Duyệt AST theo đúng thứ tự mà ASTExtractor sử dụng:
    node hiện tại trước, sau đó lần lượt các node con.
    """
    yield node

    for child in ast.iter_child_nodes(node):
        yield from _walk_preorder(child)


def _iter_children_with_context(
    node: ast.AST,
) -> Iterator[tuple[str, int | None, ast.AST]]:
    """
    Trả về node con cùng tên field và vị trí trong danh sách.
    """
    for field_name, value in ast.iter_fields(node):
        if isinstance(value, ast.AST):
            yield field_name, None, value

        elif isinstance(value, list):
            for child_index, item in enumerate(value):
                if isinstance(item, ast.AST):
                    yield field_name, child_index, item


def _call_name(node: ast.AST) -> str | None:
    """
    Lấy tên hàm từ biểu thức gọi hàm.

    Ví dụ:
    print()        -> print
    os.path.join() -> os.path.join
    """
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent_name = _call_name(node.value)

        if parent_name:
            return f"{parent_name}.{node.attr}"

        return node.attr

    return None


def extract_cpg(
    filepath: str | Path,
    repo_path: str | Path,
    repository: str = REPOSITORY_NAME,
) -> dict[str, Any]:
    """
    Parse một file Python và tạo:

    - Node theo đúng schema và ID của Parser Service
    - AST edges
    - CFG edges
    - DFG edges
    - CALL edges nội bộ nếu xác định được duy nhất hàm đích
    - Metadata
    """
    source_path = Path(filepath).resolve()
    repository_path = Path(repo_path).resolve()

    try:
        relative_file = (
            source_path
            .relative_to(repository_path)
            .as_posix()
        )

        with tokenize.open(source_path) as source_file:
            source = source_file.read()

        tree = ast.parse(
            source,
            filename=relative_file,
            type_comments=True,
        )

    except (
        SyntaxError,
        UnicodeDecodeError,
        OSError,
        ValueError,
    ) as error:
        return {
            "nodes": [],
            "edges": [],
            "error": str(error),
        }

    extraction_result = ASTExtractor(
        repository=repository,
        file_path=relative_file,
        source=source,
    ).extract(tree)

    nodes = extraction_result.nodes
    ast_objects = list(_walk_preorder(tree))

    if len(ast_objects) != len(nodes):
        return {
            "nodes": [],
            "edges": [],
            "error": (
                "AST object count does not match "
                "Parser Service node count."
            ),
        }

    node_id_by_object: dict[int, str] = {
        id(ast_node): node_data["id"]
        for ast_node, node_data in zip(
            ast_objects,
            nodes,
        )
    }

    node_data_by_object: dict[int, dict[str, Any]] = {
        id(ast_node): node_data
        for ast_node, node_data in zip(
            ast_objects,
            nodes,
        )
    }

    edges: list[dict[str, Any]] = []

    # AST edges
    ast_ordinal = 0

    for parent_ast in ast_objects:
        source_id = node_id_by_object[id(parent_ast)]

        for field_name, child_index, child_ast in (
            _iter_children_with_context(parent_ast)
        ):
            target_id = node_id_by_object[id(child_ast)]

            edge_type = "AST_PARENT_OF"

            edge_id = stable_id(
                repository,
                relative_file,
                edge_type,
                source_id,
                target_id,
                field_name,
                child_index,
            )

            edges.append(
                {
                    "id": edge_id,
                    "edge_type": edge_type,
                    "source_id": source_id,
                    "target_id": target_id,
                    "ordinal": ast_ordinal,
                    "field": field_name,
                    "child_index": child_index,
                }
            )

            ast_ordinal += 1

    # CFG edges
    for ordinal, cfg_edge in enumerate(build_cfg(tree)):
        source_id = node_id_by_object[
            id(cfg_edge["source_ast"])
        ]

        target_id = node_id_by_object[
            id(cfg_edge["target_ast"])
        ]

        edge_type = cfg_edge["type"]

        edge_id = stable_id(
            repository,
            relative_file,
            edge_type,
            source_id,
            target_id,
            ordinal,
        )

        edges.append(
            {
                "id": edge_id,
                "edge_type": edge_type,
                "source_id": source_id,
                "target_id": target_id,
                "ordinal": ordinal,
            }
        )

    # DFG edges
    for ordinal, dfg_edge in enumerate(build_dfg(tree)):
        source_id = node_id_by_object[
            id(dfg_edge["source_ast"])
        ]

        target_id = node_id_by_object[
            id(dfg_edge["target_ast"])
        ]

        edge_type = dfg_edge["type"]
        variable = dfg_edge["variable"]

        edge_id = stable_id(
            repository,
            relative_file,
            edge_type,
            source_id,
            target_id,
            variable,
            ordinal,
        )

        edges.append(
            {
                "id": edge_id,
                "edge_type": edge_type,
                "source_id": source_id,
                "target_id": target_id,
                "ordinal": ordinal,
                "variable": variable,
            }
        )

    # Các FunctionDef trong cùng file để giải quyết CALL edge
    function_targets: dict[str, list[str]] = {}

    for ast_node in ast_objects:
        if isinstance(
            ast_node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            node_data = node_data_by_object[id(ast_node)]

            function_targets.setdefault(
                ast_node.name,
                [],
            ).append(node_data["id"])

    call_ordinal = 0

    for ast_node in ast_objects:
        if not isinstance(ast_node, ast.Call):
            continue

        called_name = _call_name(ast_node.func)

        if not called_name:
            continue

        simple_name = called_name.split(".")[-1]
        targets = function_targets.get(simple_name, [])

        # Chỉ tạo CALL edge khi xác định duy nhất hàm đích.
        if len(targets) != 1:
            continue

        source_id = node_id_by_object[id(ast_node)]
        target_id = targets[0]
        edge_type = "CALL"

        edge_id = stable_id(
            repository,
            relative_file,
            edge_type,
            source_id,
            target_id,
            call_ordinal,
        )

        edges.append(
            {
                "id": edge_id,
                "edge_type": edge_type,
                "source_id": source_id,
                "target_id": target_id,
                "ordinal": call_ordinal,
                "called_name": called_name,
            }
        )

        call_ordinal += 1

    metadata = build_metadata(
        source=source,
        file_path=source_path,
        nodes=nodes,
    )

    return {
        "repository": repository,
        "file_path": relative_file,
        "nodes": nodes,
        "edges": edges,
        "metadata": metadata,
        "content": source,
    }