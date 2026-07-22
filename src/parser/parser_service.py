from __future__ import annotations

import argparse
import ast
import json
import subprocess
import tokenize
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ast_extractor import ASTExtractor
from .id_generator import file_content_hash, stable_id


REPOSITORY_NAME = "huggingface/diffusers"
SCHEMA_VERSION = "1.0"


def utc_now() -> str:
    """Trả về thời gian UTC theo định dạng ISO-8601."""
    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def get_git_commit(repo_path: Path) -> str:
    """Lấy commit hash hiện tại của repository cần phân tích."""
    try:
        return subprocess.check_output(
            [
                "git",
                "-C",
                str(repo_path),
                "rev-parse",
                "HEAD",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def safe_output_name(relative_file: str) -> str:
    """
    Chuyển đường dẫn thành tên file output an toàn.

    Ví dụ:
    src/diffusers/utils/import_utils.py

    thành:
    src__diffusers__utils__import_utils
    """
    result = (
        relative_file
        .replace("\\", "__")
        .replace("/", "__")
    )

    if result.endswith(".py"):
        result = result[:-3]

    return result


def write_json(
    output_path: Path,
    payload: dict[str, Any],
) -> None:
    """Ghi một object JSON vào file."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def write_jsonl(
    output_path: Path,
    events: list[dict[str, Any]],
) -> None:
    """
    Ghi danh sách event theo định dạng JSON Lines.

    Mỗi dòng là một event riêng, thuận tiện để Kafka producer
    đọc và gửi từng message.
    """
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as output_file:
        for event in events:
            output_file.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                )
                + "\n"
            )


def build_metadata(
    source: str,
    file_path: Path,
    nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Tạo metadata thống kê cho một file Python."""
    node_type_counts = Counter(
        node["type"]
        for node in nodes
    )

    return {
        "size_bytes": file_path.stat().st_size,
        "line_count": len(source.splitlines()),
        "node_count": len(nodes),
        "class_count": node_type_counts["ClassDef"],
        "function_count": (
            node_type_counts["FunctionDef"]
            + node_type_counts["AsyncFunctionDef"]
        ),
        "import_count": (
            node_type_counts["Import"]
            + node_type_counts["ImportFrom"]
        ),
        "call_count": node_type_counts["Call"],
        "assignment_count": (
            node_type_counts["Assign"]
            + node_type_counts["AnnAssign"]
            + node_type_counts["AugAssign"]
        ),
        "parse_status": "SUCCESS",
        "node_type_counts": dict(
            sorted(node_type_counts.items())
        ),
    }


def parse_one_file(
    repo_path: Path,
    requested_file: str,
    output_dir: Path,
) -> int:
    """
    Parse đúng một file Python trong mỗi lần thực thi.

    Kết quả:
    - Một file NodeEvent dạng JSONL
    - Một file MetadataEvent dạng JSON
    - Hoặc một ParserErrorEvent nếu parse thất bại
    """
    repo_path = repo_path.resolve()
    output_dir = output_dir.resolve()

    file_path = Path(requested_file)

    if not file_path.is_absolute():
        file_path = repo_path / file_path

    file_path = file_path.resolve()

    if not file_path.exists():
        print(f"File does not exist: {file_path}")
        return 2

    if not file_path.is_file():
        print(f"Path is not a file: {file_path}")
        return 2

    if file_path.suffix.lower() != ".py":
        print(f"File is not a Python file: {file_path}")
        return 2

    try:
        relative_file = (
            file_path
            .relative_to(repo_path)
            .as_posix()
        )

    except ValueError:
        print(
            "The Python file must be located inside "
            "the diffusers repository."
        )
        return 2

    event_time = utc_now()
    commit_hash = get_git_commit(repo_path)
    output_name = safe_output_name(relative_file)

    content_hash: str | None = None

    try:
        content_hash = file_content_hash(file_path)

        # tokenize.open đọc đúng encoding khai báo trong file Python.
        with tokenize.open(file_path) as source_file:
            source = source_file.read()

        tree = ast.parse(
            source,
            filename=relative_file,
            type_comments=True,
        )

        extraction_result = ASTExtractor(
            repository=REPOSITORY_NAME,
            file_path=relative_file,
            source=source,
        ).extract(tree)

        nodes = extraction_result.nodes

        metadata = build_metadata(
            source=source,
            file_path=file_path,
            nodes=nodes,
        )

        file_id = stable_id(
            REPOSITORY_NAME,
            relative_file,
        )

        common_fields = {
            "schema_version": SCHEMA_VERSION,
            "event_time": event_time,
            "repository": REPOSITORY_NAME,
            "commit_hash": commit_hash,
            "file_id": file_id,
            "file_path": relative_file,
            "content_hash": content_hash,
        }

        node_events = [
            {
                **common_fields,
                "event_type": "NODE_UPSERT",
                "node": node,
            }
            for node in nodes
        ]

        metadata_event = {
            **common_fields,
            "event_type": "SOURCE_METADATA_UPSERT",
            "metadata": metadata,
        }

        nodes_output = (
            output_dir
            / f"{output_name}.nodes.jsonl"
        )

        metadata_output = (
            output_dir
            / f"{output_name}.metadata.json"
        )

        write_jsonl(
            output_path=nodes_output,
            events=node_events,
        )

        write_json(
            output_path=metadata_output,
            payload=metadata_event,
        )

        print(f"Parse successful: {relative_file}")
        print(f"Content hash: {content_hash}")
        print(f"Node count: {metadata['node_count']}")
        print(f"Class count: {metadata['class_count']}")
        print(
            f"Function count: "
            f"{metadata['function_count']}"
        )
        print(f"Import count: {metadata['import_count']}")
        print(f"Call count: {metadata['call_count']}")
        print(f"Nodes output: {nodes_output}")
        print(f"Metadata output: {metadata_output}")

        return 0

    except (
        SyntaxError,
        UnicodeDecodeError,
        OSError,
    ) as error:
        error_event = {
            "schema_version": SCHEMA_VERSION,
            "event_type": "PARSER_ERROR",
            "event_time": event_time,
            "repository": REPOSITORY_NAME,
            "commit_hash": commit_hash,
            "file_path": relative_file,
            "content_hash": content_hash,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "line": getattr(
                    error,
                    "lineno",
                    None,
                ),
                "column": getattr(
                    error,
                    "offset",
                    None,
                ),
            },
        }

        error_output = (
            output_dir
            / f"{output_name}.error.json"
        )

        write_json(
            output_path=error_output,
            payload=error_event,
        )

        print(f"Parse failed: {relative_file}")
        print(f"Error type: {type(error).__name__}")
        print(f"Error message: {error}")
        print(f"Error output: {error_output}")

        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse one Python file and generate "
            "CPG node events and source metadata."
        )
    )

    parser.add_argument(
        "--repo-path",
        default="data/repos/diffusers",
        help="Path to the cloned diffusers repository.",
    )

    parser.add_argument(
        "--file",
        required=True,
        help=(
            "Python file path relative to the "
            "diffusers repository."
        ),
    )

    parser.add_argument(
        "--output-dir",
        default="data/output",
        help="Directory used to store generated events.",
    )

    args = parser.parse_args()

    return parse_one_file(
        repo_path=Path(args.repo_path),
        requested_file=args.file,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    raise SystemExit(main())