# Task 4 — Neo4j Graph Ingestion Deliverables

Gói này chứa các sản phẩm bàn giao cho phần **Graph Topology Ingestion into Neo4j**.

## File chính

- `infra/neo4j/node-sink-connector.json`
- `infra/neo4j/edge-sink-connector.json`
- `infra/neo4j/constraints.cypher`
- `infra/neo4j/cleanup.cypher`
- `infra/neo4j/verification_queries.cypher`
- `book/neo4j_graph_ingestion.md`
- `docs/images/neo4j/.gitkeep`

## Giả định schema

Node topic:

`diffusers.cpg.nodes.v1`

Edge topic:

`diffusers.cpg.edges.v1`

NodeEvent tối thiểu:

- `id`
- `node_type`
- `file_id`
- `file_path`

EdgeEvent tối thiểu:

- `id`
- `edge_type`
- `source_id`
- `target_id`
- `file_id`
- `ordinal`

Kafka value là JSON thuần, không kèm Kafka Connect schema.

## Việc phải sửa trước khi đăng ký connector

Trong hai file connector, thay:

`CHANGE_ME`

bằng mật khẩu Neo4j ở máy chạy Kafka Connect.

Không commit mật khẩu thật lên GitHub.

Nếu Kafka Connect không nằm cùng Docker network với Neo4j, đổi:

`neo4j://neo4j:7687`

thành địa chỉ mà Kafka Connect có thể truy cập.

## Đăng ký connector

Khi Kafka Connect đã chạy ở cổng 8083:

```powershell
curl.exe -X POST http://localhost:8083/connectors `
  -H "Content-Type: application/json" `
  --data-binary "@infra/neo4j/node-sink-connector.json"

curl.exe -X POST http://localhost:8083/connectors `
  -H "Content-Type: application/json" `
  --data-binary "@infra/neo4j/edge-sink-connector.json"
```

Kiểm tra trạng thái:

```powershell
curl.exe http://localhost:8083/connectors/diffusers-cpg-node-sink/status
curl.exe http://localhost:8083/connectors/diffusers-cpg-edge-sink/status
```

## Thứ tự chạy

1. Chạy `constraints.cypher`.
2. Khởi động Kafka, Kafka Connect và Neo4j.
3. Đăng ký node sink.
4. Đăng ký edge sink.
5. Producer phát NodeEvent và EdgeEvent.
6. Chạy `verification_queries.cypher`.
7. Chụp ảnh Neo4j Browser.
8. Replay file không đổi và kiểm tra count không tăng.
9. Khi file thay đổi, chạy `cleanup.cypher` theo `file_id`, rồi phát snapshot mới.

## Ảnh cần bàn giao

Lưu vào `docs/images/neo4j/`:

- `01-constraints.png`
- `02-connectors-running.png`
- `03-graph-overview.png`
- `04-node-edge-count-before.png`
- `05-duplicate-check-before.png`
- `06-node-edge-count-after-replay.png`
- `07-duplicate-check-after-replay.png`

Các ảnh và số liệu phải được chụp từ lần chạy thật. Gói này không tạo kết quả giả.
