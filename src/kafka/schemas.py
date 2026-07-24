from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from src.config import (
    SCHEMA_VERSION_EDGE,
    SCHEMA_VERSION_ERROR,
    SCHEMA_VERSION_METADATA,
    SCHEMA_VERSION_NODE,
)


def utc_now() -> str:
    """Trả về thời gian UTC theo định dạng ISO-8601."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class NodeEvent:
    repository: str
    commit_hash: str
    file_id: str
    file_path: str
    content_hash: str
    node: dict[str, Any]

    schema_version: str = SCHEMA_VERSION_NODE
    event_type: str = "NODE_UPSERT"
    event_time: str = ""

    def __post_init__(self) -> None:
        if not self.event_time:
            self.event_time = utc_now()

    def to_json(self) -> str:
        return json.dumps(
            asdict(self),
            ensure_ascii=False,
            separators=(",", ":"),
        )


@dataclass
class EdgeEvent:
    repository: str
    commit_hash: str
    file_id: str
    file_path: str
    content_hash: str
    edge: dict[str, Any]

    schema_version: str = SCHEMA_VERSION_EDGE
    event_type: str = "EDGE_UPSERT"
    event_time: str = ""

    def __post_init__(self) -> None:
        if not self.event_time:
            self.event_time = utc_now()

    def to_json(self) -> str:
        return json.dumps(
            asdict(self),
            ensure_ascii=False,
            separators=(",", ":"),
        )


@dataclass
class MetadataPayload:
    size_bytes: int
    line_count: int
    node_count: int
    class_count: int
    function_count: int
    import_count: int
    call_count: int
    assignment_count: int
    parse_status: str
    node_type_counts: dict[str, int]


@dataclass
class MetadataEvent:
    repository: str
    commit_hash: str
    file_id: str
    file_path: str
    content_hash: str
    metadata: MetadataPayload

    schema_version: str = SCHEMA_VERSION_METADATA
    event_type: str = "SOURCE_METADATA_UPSERT"
    event_time: str = ""

    def __post_init__(self) -> None:
        if not self.event_time:
            self.event_time = utc_now()

    def to_json(self) -> str:
        return json.dumps(
            asdict(self),
            ensure_ascii=False,
            separators=(",", ":"),
        )


@dataclass
class ErrorEvent:
    repository: str
    commit_hash: str
    file_path: str
    error_type: str
    error_message: str
    content_hash: str | None = None
    line: int | None = None
    column: int | None = None

    schema_version: str = SCHEMA_VERSION_ERROR
    event_type: str = "PARSER_ERROR"
    event_time: str = ""

    def __post_init__(self) -> None:
        if not self.event_time:
            self.event_time = utc_now()

    def to_json(self) -> str:
        return json.dumps(
            asdict(self),
            ensure_ascii=False,
            separators=(",", ":"),
        )