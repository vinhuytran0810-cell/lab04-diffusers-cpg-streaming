from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

from .id_generator import stable_id


@dataclass
class ExtractionResult:
    """Kết quả trích xuất AST của một file Python."""

    nodes: list[dict[str, Any]]


class ASTExtractor:
    """
    Trích xuất các node AST từ một file Python.

    Mỗi node được gán:
    - ID ổn định
    - Loại node
    - Tên node
    - Vị trí dòng/cột
    - ID node cha
    - Qualified name
    - Một số thuộc tính cần thiết
    """

    def __init__(
        self,
        repository: str,
        file_path: str,
        source: str,
    ) -> None:
        self.repository = repository
        self.file_path = file_path
        self.source = source

        self.nodes: list[dict[str, Any]] = []
        self.scope_stack: list[str] = []
        self.sequence = 0

    def extract(self, tree: ast.AST) -> ExtractionResult:
        """Bắt đầu duyệt cây AST."""

        self._visit(
            node=tree,
            parent_id=None,
        )

        return ExtractionResult(nodes=self.nodes)

    def _visit(
        self,
        node: ast.AST,
        parent_id: str | None,
    ) -> None:
        """Duyệt node hiện tại và toàn bộ node con."""

        sequence = self.sequence
        self.sequence += 1

        node_type = type(node).__name__
        name = self._node_name(node)

        line = getattr(node, "lineno", None)
        column = getattr(node, "col_offset", None)
        end_line = getattr(node, "end_lineno", None)
        end_column = getattr(node, "end_col_offset", None)

        qualified_name = self._qualified_name(
            node=node,
            name=name,
        )

        node_id = stable_id(
            self.repository,
            self.file_path,
            node_type,
            line,
            column,
            end_line,
            end_column,
            name,
            sequence,
        )

        source_segment = ast.get_source_segment(
            self.source,
            node,
        )

        if source_segment:
            source_segment = " ".join(
                source_segment.strip().split()
            )[:240]

        self.nodes.append(
            {
                "id": node_id,
                "type": node_type,
                "name": name,
                "qualified_name": qualified_name,
                "line": line,
                "column": column,
                "end_line": end_line,
                "end_column": end_column,
                "parent_id": parent_id,
                "sequence": sequence,
                "source": source_segment,
                "attributes": self._selected_attributes(node),
            }
        )

        scope_name = self._scope_name(
            node=node,
            name=name,
        )

        if scope_name is not None:
            self.scope_stack.append(scope_name)

        for child in ast.iter_child_nodes(node):
            self._visit(
                node=child,
                parent_id=node_id,
            )

        if scope_name is not None:
            self.scope_stack.pop()

    def _qualified_name(
        self,
        node: ast.AST,
        name: str | None,
    ) -> str:
        """
        Ví dụ:

        Class Student
            def calculate_score()

        qualified_name của hàm sẽ là:
        Student.calculate_score
        """

        if isinstance(
            node,
            (
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.Lambda,
            ),
        ):
            scope_name = (
                self._scope_name(node, name)
                or "<anonymous>"
            )

            return ".".join(
                [
                    *self.scope_stack,
                    scope_name,
                ]
            )

        if self.scope_stack:
            return ".".join(self.scope_stack)

        return "<module>"

    @staticmethod
    def _scope_name(
        node: ast.AST,
        name: str | None,
    ) -> str | None:
        """Trả về tên scope nếu node mở một scope mới."""

        if isinstance(node, ast.Lambda):
            line = getattr(node, "lineno", 0)
            return f"<lambda@{line}>"

        if isinstance(
            node,
            (
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            return name or "<anonymous>"

        return None

    @staticmethod
    def _node_name(node: ast.AST) -> str | None:
        """Lấy tên có ý nghĩa từ từng loại node."""

        if isinstance(
            node,
            (
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            return node.name

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.arg):
            return node.arg

        if isinstance(node, ast.Attribute):
            return node.attr

        if isinstance(node, ast.alias):
            return node.asname or node.name

        if isinstance(node, ast.Constant):
            return repr(node.value)[:80]

        if isinstance(node, ast.Call):
            return ASTExtractor._call_name(node.func)

        return None

    @staticmethod
    def _call_name(node: ast.AST) -> str | None:
        """
        Lấy tên hàm được gọi.

        Ví dụ:
        print()           -> print
        os.path.join()    -> os.path.join
        """

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            parent_name = ASTExtractor._call_name(
                node.value
            )

            if parent_name:
                return f"{parent_name}.{node.attr}"

            return node.attr

        return None

    @staticmethod
    def _selected_attributes(
        node: ast.AST,
    ) -> dict[str, Any]:
        """
        Lấy một số thuộc tính quan trọng thay vì serialize
        toàn bộ object AST.
        """

        attributes: dict[str, Any] = {}

        if isinstance(node, ast.Import):
            attributes["modules"] = [
                alias.name
                for alias in node.names
            ]

        elif isinstance(node, ast.ImportFrom):
            attributes["module"] = node.module
            attributes["level"] = node.level
            attributes["names"] = [
                alias.name
                for alias in node.names
            ]

        elif isinstance(node, ast.Constant):
            attributes["value_type"] = (
                type(node.value).__name__
            )

        elif isinstance(node, ast.Name):
            attributes["context"] = (
                type(node.ctx).__name__
            )

        elif isinstance(node, ast.Attribute):
            attributes["context"] = (
                type(node.ctx).__name__
            )

        return attributes