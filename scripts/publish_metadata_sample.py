"""Publish one generated metadata JSON event to Kafka for integration testing."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from kafka import KafkaProducer


def main() -> None:
    load_dotenv()

    bootstrap_servers = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092",
    )

    topic = os.getenv(
        "KAFKA_METADATA_TOPIC",
        "diffusers.source.metadata.v1",
    )

    metadata_path = Path(
        "data/output/src__diffusers____init__.metadata.json"
    )

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy metadata file: {metadata_path}"
        )

    with metadata_path.open("r", encoding="utf-8") as file:
        event = json.load(file)

    file_id = event.get("file_id")

    if not file_id:
        raise ValueError("Metadata event không có file_id")

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        key_serializer=lambda value: value.encode("utf-8"),
        value_serializer=lambda value: json.dumps(
            value,
            ensure_ascii=False,
        ).encode("utf-8"),
        acks="all",
    )

    try:
        future = producer.send(
            topic,
            key=file_id,
            value=event,
        )

        result = future.get(timeout=30)

        print("Gửi metadata lên Kafka thành công")
        print(f"Topic: {result.topic}")
        print(f"Partition: {result.partition}")
        print(f"Offset: {result.offset}")
        print(f"File ID: {file_id}")
        print(f"File path: {event.get('file_path')}")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()