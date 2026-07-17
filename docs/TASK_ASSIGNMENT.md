# Phân công Lab 04

## Thành viên 1 — Parser Service

Branch: `feature/parser-service`

- Clone repository diffusers vào `data/repos/diffusers`
- Tìm các file Python
- Parse AST từng file
- Tạo stable node ID
- Tạo metadata

Trạng thái: Chưa bắt đầu

---

## Thành viên 2 — CPG và Kafka

Branch: `feature/kafka-cpg`

- Tạo AST, CFG, DFG và call edges
- Thiết kế Kafka topics
- Viết Kafka producer
- Lưu message mẫu

Trạng thái: Chưa bắt đầu

---

## Thành viên 3 — Neo4j

Branch: `feature/neo4j-sink`

- Thiết kế graph model
- Cấu hình Neo4j Kafka Connector
- Dùng MERGE chống trùng lặp
- Viết truy vấn kiểm tra

Trạng thái: Chưa bắt đầu

---

## Thành viên 4 — Spark và MongoDB

Branch: `feature/spark-mongodb`

- Spark Structured Streaming đọc metadata
- Ghi MongoDB
- Cấu hình checkpoint
- Docker Compose và replay test

Trạng thái: Chưa bắt đầu