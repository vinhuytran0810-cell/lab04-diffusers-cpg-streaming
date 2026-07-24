from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


# Kafka broker
KAFKA_BROKER = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)


# Kafka topics
TOPIC_NODES = os.getenv(
    "KAFKA_NODE_TOPIC",
    "diffusers.cpg.nodes.v1",
)

TOPIC_EDGES = os.getenv(
    "KAFKA_EDGE_TOPIC",
    "diffusers.cpg.edges.v1",
)

TOPIC_METADATA = os.getenv(
    "KAFKA_METADATA_TOPIC",
    "diffusers.source.metadata.v1",
)

TOPIC_ERRORS = os.getenv(
    "KAFKA_ERROR_TOPIC",
    "diffusers.parser.errors.v1",
)


# Schema versions
SCHEMA_VERSION_NODE = os.getenv(
    "SCHEMA_VERSION_NODE",
    "1.0",
)

SCHEMA_VERSION_EDGE = os.getenv(
    "SCHEMA_VERSION_EDGE",
    "1.0",
)

SCHEMA_VERSION_METADATA = os.getenv(
    "SCHEMA_VERSION_METADATA",
    "1.0",
)

SCHEMA_VERSION_ERROR = os.getenv(
    "SCHEMA_VERSION_ERROR",
    "1.0",
)


# Repository
REPO_NAME = os.getenv(
    "REPOSITORY_NAME",
    "huggingface/diffusers",
)