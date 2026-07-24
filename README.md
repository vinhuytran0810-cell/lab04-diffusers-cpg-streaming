# Lab 04 - Diffusers CPG Streaming Pipeline

## Repository được phân tích

- Upstream repository: `huggingface/diffusers`
- Source scope: `src/diffusers/**/*.py`

## Mục tiêu

Xây dựng pipeline xử lý tăng dần:

```text
Python source files
→ Parser Service
→ Apache Kafka
→ Neo4j / Spark Structured Streaming
→ MongoDB
```

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

Pipeline Parser, Kafka, Spark Structured Streaming và MongoDB đã được kiểm thử độc lập.

Phần Neo4j và tích hợp end-to-end đang được hoàn thiện.

## Khởi động hạ tầng

### Yêu cầu

- Docker Desktop
- PowerShell
- Python 3.11
- File `.env` được tạo từ `.env.example`

Khởi động Kafka và MongoDB:

```powershell
docker compose up -d
```

Kiểm tra container:

```powershell
docker compose ps
```

Kết quả cần có hai container:

```text
lab04-kafka
lab04-mongodb
```

## Tạo Kafka topics

Chạy script:

```powershell
.\scripts\setup_kafka_topics.ps1
```

Script sẽ tạo các topic nếu chưa tồn tại và không tạo trùng topic cũ.

## Chạy Spark Structured Streaming

Chạy:

```powershell
.\scripts\run_spark_stream.ps1
```

Spark Structured Streaming sẽ:

1. Đọc metadata từ topic `diffusers.source.metadata.v1`.
2. Parse dữ liệu JSON theo metadata schema.
3. Dùng `file_id` làm MongoDB `_id`.
4. Ghi dữ liệu vào collection `bigdata_lab04.source_metadata`.
5. Lưu checkpoint tại `checkpoints/metadata_stream`.

Để dừng Spark từ một terminal khác:

```powershell
docker stop lab04-spark-stream
```

## Gửi metadata mẫu

Script này chỉ dùng để kiểm thử trước khi producer Kafka chính thức được tích hợp:

```powershell
python scripts\publish_metadata_sample.py
```

Metadata đầu vào mặc định được đọc từ:

```text
data/output/src__diffusers____init__.metadata.json
```

## Kiểm tra MongoDB

Kiểm tra document theo `file_id`:

```powershell
.\scripts\verify_mongodb.ps1 `
  -FileId "<FILE_ID>"
```

Kiểm tra thêm `content_hash` và Kafka offset:

```powershell
.\scripts\verify_mongodb.ps1 `
  -FileId "<FILE_ID>" `
  -ExpectedHash "<CONTENT_HASH>" `
  -ExpectedOffset <OFFSET>
```

Ví dụ:

```powershell
.\scripts\verify_mongodb.ps1 `
  -FileId "8a339a58f1ab78abde1c9a607e8973281b922ccb6d5b12ead5550af3e9d16283" `
  -ExpectedHash "1a6afe68b9d2353ab8f2401cc6396be2f68688c4ab7ad0f8562b25cb2c17308e" `
  -ExpectedOffset 3
```

Script kiểm tra:

- Có đúng một document theo `file_id`.
- `content_hash` khớp giá trị mong đợi.
- Kafka offset khớp giá trị mong đợi.
- Giá trị `node_count`.
- Giá trị `function_count`.

## Idempotency

MongoDB sử dụng `file_id` làm `_id`.

Khi metadata của cùng một file được gửi lại, document hiện tại sẽ được cập nhật thay vì tạo document trùng.

Kết quả kiểm thử:

```text
Kafka offset 0 → MongoDB có 1 document
Kafka offset 1 → MongoDB vẫn có 1 document
Kafka offset 2 → document được cập nhật
Kafka offset 3 → MongoDB vẫn có 1 document
```

## Spark checkpoint

Spark sử dụng checkpoint để lưu Kafka offset đã xử lý:

```text
checkpoints/metadata_stream
```

Khi Spark được khởi động lại với cùng checkpoint, các Kafka offset cũ sẽ không bị xử lý lại.

## Luồng tích hợp hiện tại

```text
Parser Service
→ Metadata JSON
→ Kafka metadata topic
→ Spark Structured Streaming
→ MongoDB
```

## Pipeline đầy đủ dự kiến

Khi Kafka producer và Neo4j ingestion được hoàn thiện:

```text
Python source files
→ Parser Service
→ Kafka nodes / edges / metadata
→ Neo4j + Spark Structured Streaming
→ MongoDB
```