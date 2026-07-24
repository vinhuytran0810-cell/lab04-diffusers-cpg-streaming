import json
import time
from dataclasses import dataclass, asdict
from typing import Optional

from src.config import SCHEMA_VERSION_NODE, SCHEMA_VERSION_EDGE, SCHEMA_VERSION_METADATA, SCHEMA_VERSION_ERROR

@dataclass
class NodeEvent:
    id: str
    filepath: str
    type: str
    lineno: int
    col_offset: int
    schema_version: str = SCHEMA_VERSION_NODE
    event_time: int = 0

    def __post_init__(self):
        if self.event_time == 0:
            self.event_time = int(time.time() * 1000)

    def to_json(self):
        return json.dumps(asdict(self))

@dataclass
class EdgeEvent:
    id: str
    type: str
    source_id: str
    target_id: str
    variable: Optional[str] = None
    schema_version: str = SCHEMA_VERSION_EDGE
    event_time: int = 0

    def __post_init__(self):
        if self.event_time == 0:
            self.event_time = int(time.time() * 1000)

    def to_json(self):
        return json.dumps(asdict(self))

from datetime import datetime, timezone

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
    node_type_counts: dict

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

    def __post_init__(self):
        if not self.event_time:
            self.event_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_json(self):
        return json.dumps(asdict(self))

@dataclass
class ErrorEvent:
    filepath: str
    error_message: str
    schema_version: str = SCHEMA_VERSION_ERROR
    event_time: int = 0

    def __post_init__(self):
        if self.event_time == 0:
            self.event_time = int(time.time() * 1000)

    def to_json(self):
        return json.dumps(asdict(self))
