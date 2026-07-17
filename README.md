# Lab 04 - Diffusers CPG Streaming Pipeline

## Repository được phân tích

- Upstream repository: `huggingface/diffusers`
- Source scope: `src/diffusers/**/*.py`

## Mục tiêu

Xây dựng pipeline xử lý tăng dần:

Python source files
→ Parser Service
→ Apache Kafka
→ Neo4j / Spark Structured Streaming
→ MongoDB

## Thành viên

| Thành viên | Nhiệm vụ |
|---|---|
| Thành viên 1 | Repository, File Discovery và Parser Service |
| Thành viên 2 | CPG Edges và Apache Kafka |
| Thành viên 3 | Neo4j Graph Ingestion |
| Thành viên 4 | Spark Structured Streaming, MongoDB và Integration |

## Các Kafka topic

- `diffusers.cpg.nodes.v1`
- `diffusers.cpg.edges.v1`
- `diffusers.source.metadata.v1`
- `diffusers.parser.errors.v1`

## Trạng thái

Đang thiết lập môi trường và kiến trúc ban đầu.
