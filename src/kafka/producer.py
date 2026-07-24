from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

from kafka import KafkaProducer

from src.config import (
    KAFKA_BROKER,
    REPO_NAME,
    TOPIC_EDGES,
    TOPIC_ERRORS,
    TOPIC_METADATA,
    TOPIC_NODES,
)
from src.cpg.edge_extractor import extract_cpg
from src.kafka.schemas import (
    EdgeEvent,
    ErrorEvent,
    MetadataEvent,
    MetadataPayload,
    NodeEvent,
)
from src.parser.id_generator import (
    file_content_hash,
    stable_id,
)


def get_git_commit(repo_path: Path) -> str:
    """Lấy commit hiện tại của repository được phân tích."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_path),
                "rev-parse",
                "HEAD",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
    ):
        return "UNKNOWN"


def create_producer(
    bootstrap_servers: str,
) -> KafkaProducer:
    """
    Tạo Kafka producer.

    Message key và value được chuyển thành bytes trước khi gọi send,
    nên không cần serializer riêng.
    """
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        acks="all",
        retries=5,
        max_in_flight_requests_per_connection=1,
    )


def send_message(
    producer: KafkaProducer,
    topic: str,
    key: str,
    value: str,
) -> None:
    """Gửi một Kafka message và chờ broker xác nhận."""
    producer.send(
        topic,
        key=key.encode("utf-8"),
        value=value.encode("utf-8"),
    )


def build_metadata_payload(
    metadata: dict[str, Any],
) -> MetadataPayload:
    """Chuyển metadata dictionary thành MetadataPayload."""
    return MetadataPayload(
        size_bytes=metadata["size_bytes"],
        line_count=metadata["line_count"],
        node_count=metadata["node_count"],
        class_count=metadata["class_count"],
        function_count=metadata["function_count"],
        import_count=metadata["import_count"],
        call_count=metadata["call_count"],
        assignment_count=metadata["assignment_count"],
        parse_status=metadata["parse_status"],
        node_type_counts=metadata["node_type_counts"],
    )


def process_file(
    repo_path: Path,
    requested_file: str,
    producer: KafkaProducer,
) -> int:
    """Parse một file rồi gửi node, edge và metadata lên Kafka."""
    repository_path = repo_path.resolve()

    source_path = Path(requested_file)

    if not source_path.is_absolute():
        source_path = repository_path / source_path

    source_path = source_path.resolve()

    try:
        relative_file = (
            source_path
            .relative_to(repository_path)
            .as_posix()
        )

    except ValueError:
        print(
            "ERROR: File phải nằm bên trong repository "
            f"{repository_path}"
        )
        return 2

    if not source_path.exists():
        print(f"ERROR: File không tồn tại: {source_path}")
        return 2

    if not source_path.is_file():
        print(f"ERROR: Đường dẫn không phải file: {source_path}")
        return 2

    if source_path.suffix.lower() != ".py":
        print(f"ERROR: Không phải file Python: {source_path}")
        return 2

    commit_hash = get_git_commit(repository_path)
    content_hash = file_content_hash(source_path)

    file_id = stable_id(
        REPO_NAME,
        relative_file,
    )

    print(f"Processing: {relative_file}")
    print(f"Repository: {REPO_NAME}")
    print(f"Commit: {commit_hash}")
    print(f"File ID: {file_id}")
    print(f"Content hash: {content_hash}")

    cpg_data = extract_cpg(
        filepath=source_path,
        repo_path=repository_path,
        repository=REPO_NAME,
    )

    if "error" in cpg_data:
        error_event = ErrorEvent(
            repository=REPO_NAME,
            commit_hash=commit_hash,
            file_path=relative_file,
            content_hash=content_hash,
            error_type="CPGExtractionError",
            error_message=cpg_data["error"],
        )

        send_message(
            producer=producer,
            topic=TOPIC_ERRORS,
            key=relative_file,
            value=error_event.to_json(),
        )

        producer.flush()

        print(f"ERROR: {cpg_data['error']}")
        return 1

    nodes = cpg_data["nodes"]
    edges = cpg_data["edges"]
    metadata = cpg_data["metadata"]

    for node in nodes:
        node_event = NodeEvent(
            repository=REPO_NAME,
            commit_hash=commit_hash,
            file_id=file_id,
            file_path=relative_file,
            content_hash=content_hash,
            node=node,
        )

        send_message(
            producer=producer,
            topic=TOPIC_NODES,
            key=node["id"],
            value=node_event.to_json(),
        )

    for edge in edges:
        edge_event = EdgeEvent(
            repository=REPO_NAME,
            commit_hash=commit_hash,
            file_id=file_id,
            file_path=relative_file,
            content_hash=content_hash,
            edge=edge,
        )

        send_message(
            producer=producer,
            topic=TOPIC_EDGES,
            key=edge["id"],
            value=edge_event.to_json(),
        )

    metadata_event = MetadataEvent(
        repository=REPO_NAME,
        commit_hash=commit_hash,
        file_id=file_id,
        file_path=relative_file,
        content_hash=content_hash,
        metadata=build_metadata_payload(metadata),
    )

    send_message(
        producer=producer,
        topic=TOPIC_METADATA,
        key=file_id,
        value=metadata_event.to_json(),
    )

    producer.flush()

    print("")
    print("Kafka publishing completed:")
    print(f"  Nodes:    {len(nodes)}")
    print(f"  Edges:    {len(edges)}")
    print("  Metadata: 1")
    print("")
    print("Topics:")
    print(f"  {TOPIC_NODES}")
    print(f"  {TOPIC_EDGES}")
    print(f"  {TOPIC_METADATA}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse one Python file and publish CPG "
            "nodes, edges and metadata to Kafka."
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
        "--bootstrap-servers",
        default=KAFKA_BROKER,
        help="Kafka bootstrap servers.",
    )

    args = parser.parse_args()

    producer: KafkaProducer | None = None

    try:
        producer = create_producer(
            bootstrap_servers=args.bootstrap_servers,
        )

        return process_file(
            repo_path=Path(args.repo_path),
            requested_file=args.file,
            producer=producer,
        )

    except Exception as error:
        print(
            f"ERROR: Kafka publishing failed: "
            f"{type(error).__name__}: {error}"
        )
        return 1

    finally:
        if producer is not None:
            producer.close()


if __name__ == "__main__":
    raise SystemExit(main())