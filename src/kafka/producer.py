import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import glob
import time
from kafka import KafkaProducer

from src.cpg.edge_extractor import extract_cpg
from src.kafka.schemas import NodeEvent, EdgeEvent, MetadataEvent, ErrorEvent
from src.config import KAFKA_BROKER, TOPIC_NODES, TOPIC_EDGES, TOPIC_METADATA, TOPIC_ERRORS, REPO_NAME

def get_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: v.encode('utf-8'),
            # Retries and idempotence can be configured here for robust streaming
        )
    except Exception as e:
        print(f"Failed to connect Kafka Producer to {KAFKA_BROKER}: {e}")
        return None

def process_file(filepath, producer):
    print(f"Processing: {filepath}")
    
    # 1. Extract CPG (Bounded memory: processes one file at a time)
    cpg_data = extract_cpg(filepath)
    
    if 'error' in cpg_data:
        # Handle Parser Errors
        err_event = ErrorEvent(
            filepath=filepath,
            error_message=cpg_data['error']
        )
        producer.send(TOPIC_ERRORS, value=err_event.to_json())
        print(f"  -> Error: {cpg_data['error']}")
        return

    nodes = cpg_data['nodes']
    edges = cpg_data['edges']

    # 2. Emit Node Events
    for n in nodes:
        event = NodeEvent(
            id=n['id'],
            filepath=n['filepath'],
            type=n['type'],
            lineno=n['lineno'],
            col_offset=n['col_offset']
        )
        # Using node ID as the Kafka message key to ensure ordered processing per node if needed
        producer.send(TOPIC_NODES, key=n['id'].encode('utf-8'), value=event.to_json())

    # 3. Emit Edge Events
    for e in edges:
        event = EdgeEvent(
            id=e['id'],
            type=e['type'],
            source_id=e['source_id'],
            target_id=e['target_id'],
            variable=e.get('variable')
        )
        producer.send(TOPIC_EDGES, key=e['id'].encode('utf-8'), value=event.to_json())

    # 4. Emit Metadata Event
    meta_event = MetadataEvent(
        filepath=filepath,
        repo_name=REPO_NAME,
        node_count=len(nodes),
        edge_count=len(edges)
    )
    # Using filepath as key for metadata so updates to the same file go to the same partition
    producer.send(TOPIC_METADATA, key=filepath.encode('utf-8'), value=meta_event.to_json())

    print(f"  -> Emitted {len(nodes)} nodes and {len(edges)} edges.")

def main():
    producer = get_producer()
    if not producer:
        return

    # Assuming the script is run from the lab4 directory
    target_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'example_py', '*.py')
    files_to_process = glob.glob(target_dir)

    if not files_to_process:
        print(f"No python files found in {target_dir}")
        return

    for filepath in files_to_process:
        process_file(filepath, producer)
        # Optional: Add small sleep to avoid overwhelming local broker during tests
        time.sleep(0.1)

    producer.flush()
    print("All files processed and messages flushed to Kafka.")

if __name__ == "__main__":
    main()
