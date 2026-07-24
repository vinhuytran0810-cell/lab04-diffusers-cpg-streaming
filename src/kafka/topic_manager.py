import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from src.config import KAFKA_BROKER, TOPIC_NODES, TOPIC_EDGES, TOPIC_METADATA, TOPIC_ERRORS

def create_topics():
    """
    Programmatically creates the required Kafka topics.
    This assumes `kafka-python` is installed.
    """
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=KAFKA_BROKER, 
            client_id='cpg-topic-manager'
        )
    except Exception as e:
        print(f"Failed to connect to Kafka Broker at {KAFKA_BROKER}: {e}")
        return

    topic_names = [TOPIC_NODES, TOPIC_EDGES, TOPIC_METADATA, TOPIC_ERRORS]
    existing_topics = admin_client.list_topics()

    topic_list = []
    for t_name in topic_names:
        if t_name not in existing_topics:
            # Create topic with 1 partition and replication factor of 1 (suitable for local dev)
            topic_list.append(NewTopic(name=t_name, num_partitions=1, replication_factor=1))
        else:
            print(f"Topic '{t_name}' already exists.")

    if topic_list:
        try:
            admin_client.create_topics(new_topics=topic_list, validate_only=False)
            print(f"Successfully created topics: {[t.name for t in topic_list]}")
        except TopicAlreadyExistsError:
            pass
        except Exception as e:
            print(f"Failed to create topics: {e}")

if __name__ == "__main__":
    create_topics()
