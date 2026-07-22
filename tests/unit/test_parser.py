from __future__ import annotations

import ast
import json
from pathlib import Path

from src.parser.ast_extractor import ASTExtractor
from src.parser.id_generator import file_content_hash, stable_id
from src.parser.parser_service import parse_one_file


def test_stable_id_is_deterministic() -> None:
    first = stable_id(
        "huggingface/diffusers",
        "sample.py",
        "FunctionDef",
        1,
        0,
    )

    second = stable_id(
        "huggingface/diffusers",
        "sample.py",
        "FunctionDef",
        1,
        0,
    )

    assert first == second
    assert len(first) == 64


def test_different_input_creates_different_id() -> None:
    first = stable_id(
        "repository",
        "sample.py",
        "FunctionDef",
        1,
    )

    second = stable_id(
        "repository",
        "sample.py",
        "FunctionDef",
        2,
    )

    assert first != second


def test_file_content_hash_is_deterministic(
    tmp_path: Path,
) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "value = 10\n",
        encoding="utf-8",
    )

    first = file_content_hash(sample_file)
    second = file_content_hash(sample_file)

    assert first == second
    assert len(first) == 64


def test_file_content_hash_changes_when_file_changes(
    tmp_path: Path,
) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "value = 10\n",
        encoding="utf-8",
    )

    before = file_content_hash(sample_file)

    sample_file.write_text(
        "value = 20\n",
        encoding="utf-8",
    )

    after = file_content_hash(sample_file)

    assert before != after


def test_ast_extractor_finds_expected_nodes() -> None:
    source = """
class Student:
    def calculate_score(self, value):
        result = value + 1
        return result
"""

    result = ASTExtractor(
        repository="test/repository",
        file_path="sample.py",
        source=source,
    ).extract(ast.parse(source))

    node_types = {
        node["type"]
        for node in result.nodes
    }

    assert "Module" in node_types
    assert "ClassDef" in node_types
    assert "FunctionDef" in node_types
    assert "Assign" in node_types
    assert "Return" in node_types


def test_function_qualified_name() -> None:
    source = """
class Student:
    def calculate_score(self):
        return 10
"""

    result = ASTExtractor(
        repository="test/repository",
        file_path="sample.py",
        source=source,
    ).extract(ast.parse(source))

    function_nodes = [
        node
        for node in result.nodes
        if node["type"] == "FunctionDef"
    ]

    assert len(function_nodes) == 1
    assert (
        function_nodes[0]["qualified_name"]
        == "Student.calculate_score"
    )


def test_all_ast_node_ids_are_unique() -> None:
    source = """
def add(a, b):
    total = a + b
    return total
"""

    result = ASTExtractor(
        repository="test/repository",
        file_path="sample.py",
        source=source,
    ).extract(ast.parse(source))

    node_ids = [
        node["id"]
        for node in result.nodes
    ]

    assert len(node_ids) == len(set(node_ids))


def test_parser_service_creates_node_and_metadata_files(
    tmp_path: Path,
) -> None:
    repository_path = tmp_path / "repository"
    repository_path.mkdir()

    source_file = repository_path / "sample.py"
    source_file.write_text(
        """
class Calculator:
    def add(self, a, b):
        return a + b
""",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"

    exit_code = parse_one_file(
        repo_path=repository_path,
        requested_file="sample.py",
        output_dir=output_dir,
    )

    assert exit_code == 0

    nodes_file = output_dir / "sample.nodes.jsonl"
    metadata_file = output_dir / "sample.metadata.json"

    assert nodes_file.exists()
    assert metadata_file.exists()

    node_events = [
        json.loads(line)
        for line in nodes_file.read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    metadata_event = json.loads(
        metadata_file.read_text(
            encoding="utf-8"
        )
    )

    assert len(node_events) > 0
    assert all(
        event["event_type"] == "NODE_UPSERT"
        for event in node_events
    )

    assert (
        metadata_event["event_type"]
        == "SOURCE_METADATA_UPSERT"
    )

    assert (
        metadata_event["metadata"]["parse_status"]
        == "SUCCESS"
    )

    assert (
        metadata_event["metadata"]["class_count"]
        == 1
    )

    assert (
        metadata_event["metadata"]["function_count"]
        == 1
    )


def test_parser_service_creates_error_event(
    tmp_path: Path,
) -> None:
    repository_path = tmp_path / "repository"
    repository_path.mkdir()

    broken_file = repository_path / "broken.py"
    broken_file.write_text(
        "def broken(\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"

    exit_code = parse_one_file(
        repo_path=repository_path,
        requested_file="broken.py",
        output_dir=output_dir,
    )

    assert exit_code == 1

    error_file = output_dir / "broken.error.json"

    assert error_file.exists()

    error_event = json.loads(
        error_file.read_text(
            encoding="utf-8"
        )
    )

    assert error_event["event_type"] == "PARSER_ERROR"
    assert error_event["error"]["type"] == "SyntaxError"