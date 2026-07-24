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

@dataclass
class MetadataEvent:
    filepath: str
    repo_name: str
    node_count: int
    edge_count: int
    schema_version: str = SCHEMA_VERSION_METADATA
    event_time: int = 0

    def __post_init__(self):
        if self.event_time == 0:
            self.event_time = int(time.time() * 1000)

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
