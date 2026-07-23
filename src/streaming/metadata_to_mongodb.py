"""Read source metadata events from Kafka and upsert them into MongoDB."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, from_json
from pyspark.sql.types import (
    LongType,
    MapType,
    StringType,
    StructField,
    StructType,
)


def get_env(name: str, default: str) -> str:
    """Read a configuration value from the environment."""

    value = os.getenv(name, default).strip()

    if not value:
        raise ValueError(f"Biến môi trường {name} không được để trống")

    return value


def build_metadata_schema() -> StructType:
    """Define the schema of the metadata section."""

    return StructType(
        [
            StructField("size_bytes", LongType(), True),
            StructField("line_count", LongType(), True),
            StructField("node_count", LongType(), True),
            StructField("class_count", LongType(), True),
            StructField("function_count", LongType(), True),
            StructField("import_count", LongType(), True),
            StructField("call_count", LongType(), True),
            StructField("assignment_count", LongType(), True),
            StructField("parse_status", StringType(), True),
            StructField(
                "node_type_counts",
                MapType(StringType(), LongType()),
                True,
            ),
        ]
    )


def build_event_schema() -> StructType:
    """Define the schema of SOURCE_METADATA_UPSERT events."""

    return StructType(
        [
            StructField("schema_version", StringType(), False),
            StructField("event_time", StringType(), False),
            StructField("repository", StringType(), False),
            StructField("commit_hash", StringType(), True),
            StructField("file_id", StringType(), False),
            StructField("file_path", StringType(), False),
            StructField("content_hash", StringType(), False),
            StructField("event_type", StringType(), False),
            StructField("metadata", build_metadata_schema(), False),
        ]
    )


def main() -> None:
    load_dotenv()

    kafka_bootstrap_servers = get_env(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092",
    )
    kafka_metadata_topic = get_env(
        "KAFKA_METADATA_TOPIC",
        "diffusers.source.metadata.v1",
    )

    mongodb_uri = get_env(
        "MONGODB_URI",
        "mongodb://localhost:27017",
    )
    mongodb_database = get_env(
        "MONGODB_DATABASE",
        "bigdata_lab04",
    )
    mongodb_collection = get_env(
        "MONGODB_COLLECTION",
        "source_metadata",
    )

    checkpoint_location = Path(
        get_env(
            "SPARK_CHECKPOINT_PATH",
            "checkpoints/metadata_stream",
        )
    ).resolve()

    checkpoint_location.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("diffusers-metadata-to-mongodb")
        .config("spark.sql.session.timeZone", "UTC")
        .config(
            "spark.mongodb.write.connection.uri",
            mongodb_uri,
        )
        .config(
            "spark.mongodb.write.database",
            mongodb_database,
        )
        .config(
            "spark.mongodb.write.collection",
            mongodb_collection,
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    kafka_stream = (
        spark.readStream
        .format("kafka")
        .option(
            "kafka.bootstrap.servers",
            kafka_bootstrap_servers,
        )
        .option(
            "subscribe",
            kafka_metadata_topic,
        )
        # Chỉ áp dụng khi thư mục checkpoint chưa tồn tại.
        .option(
            "startingOffsets",
            "earliest",
        )
        .option(
            "failOnDataLoss",
            "false",
        )
        .load()
    )

    parsed_stream = kafka_stream.select(
        col("key").cast("string").alias("kafka_key"),
        col("topic").alias("kafka_topic"),
        col("partition").alias("kafka_partition"),
        col("offset").alias("kafka_offset"),
        col("timestamp").alias("kafka_timestamp"),
        from_json(
            col("value").cast("string"),
            build_event_schema(),
        ).alias("event"),
    )

    valid_events = parsed_stream.filter(
        col("event").isNotNull()
        & (col("event.event_type") == "SOURCE_METADATA_UPSERT")
        & col("event.file_id").isNotNull()
    )

    mongo_documents = valid_events.select(
        # Dùng stable file_id làm MongoDB _id để tránh document trùng.
        col("event.file_id").alias("_id"),
        col("event.file_id").alias("file_id"),
        col("event.file_path").alias("file_path"),
        col("event.repository").alias("repository"),
        col("event.commit_hash").alias("commit_hash"),
        col("event.content_hash").alias("content_hash"),
        col("event.schema_version").alias("schema_version"),
        col("event.event_time").alias("event_time"),
        col("event.event_type").alias("event_type"),
        col("event.metadata").alias("metadata"),
        col("kafka_key"),
        col("kafka_topic"),
        col("kafka_partition"),
        col("kafka_offset"),
        col("kafka_timestamp"),
        current_timestamp().alias("ingested_at"),
    )

    query = (
        mongo_documents.writeStream
        .queryName("diffusers_metadata_to_mongodb")
        .format("mongodb")
        .outputMode("append")
        .option(
            "checkpointLocation",
            str(checkpoint_location),
        )
        .option(
            "database",
            mongodb_database,
        )
        .option(
            "collection",
            mongodb_collection,
        )
        .option(
            "operationType",
            "replace",
        )
        .option(
            "upsertDocument",
            "true",
        )
        .option(
            "idFieldList",
            "_id",
        )
        .trigger(processingTime="5 seconds")
        .start()
    )

    print("=" * 70)
    print("Spark Structured Streaming đã khởi động")
    print(f"Kafka: {kafka_bootstrap_servers}")
    print(f"Topic: {kafka_metadata_topic}")
    print(
        f"MongoDB: {mongodb_database}.{mongodb_collection}"
    )
    print(f"Checkpoint: {checkpoint_location}")
    print("=" * 70)

    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("Đang dừng Spark Streaming...")
        query.stop()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()