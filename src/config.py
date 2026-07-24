import os

# Kafka Broker
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

# Topic Names
TOPIC_NODES = "cpg.nodes.v1"
TOPIC_EDGES = "cpg.edges.v1"
TOPIC_METADATA = "source.metadata.v1"
TOPIC_ERRORS = "parser.errors.v1"

# Schema Versions
SCHEMA_VERSION_NODE = "v1.0"
SCHEMA_VERSION_EDGE = "v1.0"
SCHEMA_VERSION_METADATA = "v1.0"
SCHEMA_VERSION_ERROR = "v1.0"

# Parser config
REPO_NAME = "huggingface/diffusers"
