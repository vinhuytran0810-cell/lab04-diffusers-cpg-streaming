# Graph Topology Ingestion into Neo4j

## 1. Mục tiêu

Phần này đưa trực tiếp CPG node và edge từ Apache Kafka vào Neo4j bằng Neo4j Kafka Connector Sink, không sử dụng Spark làm tầng trung gian.

Các topic:

- Node: `diffusers.cpg.nodes.v1`
- Edge: `diffusers.cpg.edges.v1`

## 2. Kiến trúc

```text
Parser/CPG Service
    ├── diffusers.cpg.nodes.v1 ──> Node Sink ──> Neo4j nodes
    └── diffusers.cpg.edges.v1 ──> Edge Sink ──> Neo4j relationships
```

## 3. Graph model

Tất cả node dùng label chung `CPGNode`; loại cụ thể nằm trong `node_type`.

Node types:

`Repository`, `File`, `Module`, `Class`, `Function`, `Variable`, `Statement`, `Expression`, `Call`.

Relationship types:

`CONTAINS`, `AST_CHILD`, `DEFINES`, `CALLS`, `CFG_NEXT`, `CFG_TRUE`, `CFG_FALSE`, `READS`, `WRITES`, `DFG_TO`.

## 4. Idempotent design

Mỗi node và edge có stable ID do Parser/CPG Service sinh ra.

Node được ghi bằng:

```cypher
MERGE (n:CPGNode {id: e.id})
```

Edge được ghi bằng:

```cypher
MERGE (source)-[r:$(e.edge_type) {id: e.id}]->(target)
```

Vì sử dụng `MERGE` theo stable ID và uniqueness constraints, phát lại cùng một event không tạo bản ghi trùng.

## 5. Constraints và indexes

File sử dụng:

`infra/neo4j/constraints.cypher`

Chèn ảnh kết quả `SHOW CONSTRAINTS` và `SHOW INDEXES` tại đây:

```text
[CHÈN ẢNH: docs/images/neo4j/01-constraints.png]
```

## 6. Node Sink Connector

File cấu hình:

`infra/neo4j/node-sink-connector.json`

Node sink đọc `diffusers.cpg.nodes.v1` và cập nhật node bằng stable ID.

## 7. Edge Sink Connector

File cấu hình:

`infra/neo4j/edge-sink-connector.json`

Edge sink đọc `diffusers.cpg.edges.v1`. Nếu edge tới trước NodeEvent, connector tạo placeholder node theo stable ID; Node Sink sẽ cập nhật placeholder khi message node tới.

Chèn ảnh trạng thái hai connector:

```text
[CHÈN ẢNH: docs/images/neo4j/02-connectors-running.png]
```

## 8. Kết quả ingestion

Chạy:

`infra/neo4j/verification_queries.cypher`

### Node count

```text
[CHÈN OUTPUT THỰC TẾ]
```

### Edge count

```text
[CHÈN OUTPUT THỰC TẾ]
```

### Node count theo loại

```text
[CHÈN OUTPUT THỰC TẾ]
```

### Edge count theo loại

```text
[CHÈN OUTPUT THỰC TẾ]
```

Chèn ảnh graph:

```text
[CHÈN ẢNH: docs/images/neo4j/03-graph-overview.png]
```

## 9. Kiểm tra duplicate

Truy vấn duplicate node ID và edge ID phải trả về không có bản ghi.

```text
[CHÈN OUTPUT THỰC TẾ]
```

Chèn ảnh:

```text
[CHÈN ẢNH: docs/images/neo4j/05-duplicate-check-before.png]
```

## 10. Replay verification

### Trước replay

| Chỉ số | Giá trị |
|---|---:|
| Node count | [ĐIỀN] |
| Edge count | [ĐIỀN] |
| Duplicate node ID | 0 |
| Duplicate edge ID | 0 |

### Replay file không đổi

Phát lại toàn bộ NodeEvent và EdgeEvent của cùng file mà không sửa nội dung.

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Node count | [ĐIỀN] | [ĐIỀN] |
| Edge count | [ĐIỀN] | [ĐIỀN] |

Kỳ vọng: count không tăng và duplicate vẫn bằng 0.

### Replay file đã sửa

1. Sửa một file Python.
2. Chạy `cleanup.cypher` với `file_id` tương ứng.
3. Parse và phát lại snapshot mới.
4. Chạy lại các truy vấn kiểm tra.

| Chỉ số | Trước sửa | Sau sửa |
|---|---:|---:|
| Node count của file | [ĐIỀN] | [ĐIỀN] |
| Edge count của file | [ĐIỀN] | [ĐIỀN] |
| Duplicate node ID | 0 | 0 |
| Duplicate edge ID | 0 | 0 |

Chèn ảnh trước/sau replay:

```text
[CHÈN ẢNH: docs/images/neo4j/04-node-edge-count-before.png]
[CHÈN ẢNH: docs/images/neo4j/06-node-edge-count-after-replay.png]
[CHÈN ẢNH: docs/images/neo4j/07-duplicate-check-after-replay.png]
```

## 11. Hạn chế

- CALLS edge chỉ chính xác khi CPG service resolve được function đích.
- Dynamic dispatch của Python có thể khiến một số lời gọi ở trạng thái unresolved.
- Cleanup hiện thay thế toàn bộ snapshot của một file theo `file_id`.

## 12. Reflection

### Điều hoạt động tốt

[VIẾT SAU KHI CHẠY THẬT]

### Lỗi đã gặp

[VIẾT SAU KHI CHẠY THẬT]

### Cách khắc phục

[VIẾT SAU KHI CHẠY THẬT]
