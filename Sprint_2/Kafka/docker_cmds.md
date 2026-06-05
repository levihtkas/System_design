# Kafka KRaft & Docker: Comprehensive Technical Notes

## 1. The Docker Command Breakdown
When running a Kafka instance in KRaft mode (without Zookeeper), the configuration focuses on consolidating roles and defining network boundaries.

```bash
docker run -d \
  --name kafka-server \
  -p 9092:9092 \
  -e KAFKA_NODE_ID=1 \
  -e KAFKA_PROCESS_ROLES=broker,controller \
  -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
  apache/kafka:latest


  docker exec kafka-server \
  /opt/kafka/bin/kafka-topics.sh --create \
  --topic flight-data \
  --partitions 3 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092

docker exec -it kafka-server /opt/kafka/bin/kafka-console-producer.sh --topic flight-data --bootstrap-server localhost:9092

  docker exec -it kafka-server \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --topic flight-data \
  --from-beginning \
  --bootstrap-server localhost:9092