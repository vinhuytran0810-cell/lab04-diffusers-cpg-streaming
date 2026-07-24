# BÀN GIAO PARSER SERVICE CHO CÁC THÀNH VIÊN

## 1. Thông tin chung

- **Repository nhóm:** `https://github.com/vinhuytran0810-cell/lab04-diffusers-cpg-streaming`
- **Nhánh chính:** `main`
- **Pull Request đã merge:** `#1`
- **Commit Parser Service:** `209644d`
- **Merge commit trên `main`:** `c5a74de`
- **Repository được phân tích:** `huggingface/diffusers`
- **Commit của `diffusers`:** `b48d49d87b97753bab3921bf3b7db52e8f1d3c49`
- **Phạm vi quét:** `src/diffusers/**/*.py`
- **Tổng số file Python:** `960`
- **Tổng dung lượng:** `24.914.617 bytes`

---

## 2. Phần đã hoàn thành

Parser Service hiện đã có các chức năng:

- Clone và khảo sát repository `huggingface/diffusers`.
- Tìm toàn bộ file Python trong `src/diffusers`.
- Sinh danh sách file tại `data/samples/python_files.json`.
- Tính SHA-256 cho nội dung từng file.
- Tạo stable ID cho file và AST node.
- Parse từng file Python riêng lẻ bằng thư viện `ast`.
- Trích xuất loại node, tên, qualified name, vị trí dòng/cột, `parent_id`, source rút gọn và thuộc tính bổ sung.
- Sinh `NodeEvent` dạng JSON Lines.
- Sinh `MetadataEvent` dạng JSON.
- Sinh `ParserErrorEvent` khi file lỗi cú pháp.
- Kiểm tra node ID không bị trùng.
- Kiểm tra chạy lại cùng file vẫn giữ nguyên node ID.
- Có 9 unit test và tất cả đều vượt qua.

---

## 3. Cấu trúc file đã bàn giao

```text
src/parser/
├── __init__.py
├── ast_extractor.py
├── file_discovery.py
├── id_generator.py
└── parser_service.py

tests/unit/
└── test_parser.py

data/samples/
└── python_files.json
```

| File | Chức năng |
|---|---|
| `src/parser/file_discovery.py` | Quét toàn bộ file `.py` trong repository |
| `src/parser/id_generator.py` | Tạo stable ID và content hash |
| `src/parser/ast_extractor.py` | Trích xuất AST node và quan hệ cha-con |
| `src/parser/parser_service.py` | Parse một file và sinh event đầu ra |
| `tests/unit/test_parser.py` | Unit test cho Parser Service |
| `data/samples/python_files.json` | Danh sách 960 file Python được phát hiện |

---

## 4. Chuẩn bị môi trường trên máy cá nhân

### 4.1. Clone repository nhóm

```powershell
git clone https://github.com/vinhuytran0810-cell/lab04-diffusers-cpg-streaming.git
cd lab04-diffusers-cpg-streaming
```

### 4.2. Tạo môi trường ảo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu `requirements.txt` chưa chứa `pytest`:

```powershell
python -m pip install pytest
```

### 4.3. Clone repository cần phân tích

```powershell
git clone --depth 1 https://github.com/huggingface/diffusers.git data/repos/diffusers
```

Kiểm tra:

```powershell
Test-Path data/repos/diffusers/src/diffusers
```

Kết quả phải là:

```text
True
```

Kiểm tra commit:

```powershell
git -C data/repos/diffusers rev-parse HEAD
```

Commit đang được dùng khi bàn giao:

```text
b48d49d87b97753bab3921bf3b7db52e8f1d3c49
```

---

## 5. Các thư mục không được commit

Không đưa các thư mục hoặc file sau lên GitHub:

```text
.venv/
.env
data/repos/diffusers/
data/output/
checkpoints/
.pytest_cache/
```

- `.venv/`: phụ thuộc từng máy.
- `.env`: có thể chứa thông tin nhạy cảm.
- `data/repos/diffusers/`: repository ngoài, mỗi thành viên tự clone.
- `data/output/`: dữ liệu sinh tự động, có thể rất lớn.
- `checkpoints/`: dữ liệu runtime của Spark Streaming.
- `.pytest_cache/`: cache kiểm thử.

---

## 6. Đồng bộ branch của từng thành viên

Trước khi tiếp tục công việc, mỗi thành viên cần cập nhật code mới nhất từ `main`.

### Thành viên 2 — CPG Edges và Kafka

```powershell
git switch feature/kafka-cpg
git pull origin feature/kafka-cpg
git merge main
git push origin feature/kafka-cpg
```

### Thành viên 3 — Neo4j Sink

```powershell
git switch feature/neo4j-sink
git pull origin feature/neo4j-sink
git merge main
git push origin feature/neo4j-sink
```

### Thành viên 4 — Spark và MongoDB

```powershell
git switch feature/spark-mongodb
git pull origin feature/spark-mongodb
git merge main
git push origin feature/spark-mongodb
```

Kiểm tra Parser Service đã có trên branch:

```powershell
Test-Path src/parser/parser_service.py
```

Kết quả:

```text
True
```

---

## 7. Cách chạy File Discovery

```powershell
python -m src.parser.file_discovery
```

Kết quả hiện tại:

```text
Đã tìm thấy 960 file Python.
Tổng dung lượng: 24914617 bytes.
Commit hash: b48d49d87b97753bab3921bf3b7db52e8f1d3c49
```

File kết quả:

```text
data/samples/python_files.json
```

---

## 8. Cách chạy Parser Service

Parser Service chỉ xử lý **một file Python trong mỗi lần chạy**.

```powershell
python -m src.parser.parser_service `
    --file src/diffusers/configuration_utils.py
```

Một số file đã kiểm thử:

```powershell
python -m src.parser.parser_service `
    --file src/diffusers/__init__.py

python -m src.parser.parser_service `
    --file src/diffusers/configuration_utils.py

python -m src.parser.parser_service `
    --file src/diffusers/utils/import_utils.py
```

Đầu ra được sinh trong `data/output/`:

```text
<file>.nodes.jsonl
<file>.metadata.json
<file>.error.json
```

Ví dụ:

```text
data/output/src__diffusers__configuration_utils.nodes.jsonl
data/output/src__diffusers__configuration_utils.metadata.json
```

---

## 9. Kết quả kiểm thử thực tế

### `src/diffusers/__init__.py`

```text
Node count: 2871
Class count: 0
Function count: 0
Import count: 70
Call count: 168
```

### `src/diffusers/configuration_utils.py`

```text
Node count: 3216
Class count: 3
Function count: 26
Import count: 16
Call count: 201
```

### `src/diffusers/utils/import_utils.py`

```text
Node count: 3159
Class count: 3
Function count: 76
Import count: 15
Call count: 168
```

Kiểm tra ID:

```text
Total IDs: 2871
Unique IDs: 2871
Duplicate IDs: 0
```

Khi parse lại cùng một file, `Compare-Object` không trả kết quả, nghĩa là node ID vẫn giữ nguyên.

---

## 10. Schema của NodeEvent

Mỗi dòng trong file `.nodes.jsonl` là một `NodeEvent`.

```json
{
  "schema_version": "1.0",
  "event_time": "2026-07-22T11:19:01.113153Z",
  "repository": "huggingface/diffusers",
  "commit_hash": "b48d49d87b97753bab3921bf3b7db52e8f1d3c49",
  "file_id": "stable-file-id",
  "file_path": "src/diffusers/configuration_utils.py",
  "content_hash": "file-content-hash",
  "event_type": "NODE_UPSERT",
  "node": {
    "id": "stable-node-id",
    "type": "FunctionDef",
    "name": "register_to_config",
    "qualified_name": "ConfigMixin.register_to_config",
    "line": 60,
    "column": 4,
    "end_line": 80,
    "end_column": 10,
    "parent_id": "parent-node-id",
    "sequence": 28,
    "source": "def register_to_config(...):",
    "attributes": {}
  }
}
```

Các trường quan trọng:

| Trường | Ý nghĩa |
|---|---|
| `schema_version` | Phiên bản schema |
| `event_time` | Thời điểm sinh event |
| `repository` | Repository nguồn |
| `commit_hash` | Commit của repository nguồn |
| `file_id` | ID ổn định của file |
| `file_path` | Đường dẫn file |
| `content_hash` | SHA-256 nội dung file |
| `event_type` | Loại event |
| `node.id` | ID ổn định của node |
| `node.parent_id` | ID của node cha |
| `node.type` | Loại AST node |
| `node.name` | Tên node |
| `node.qualified_name` | Tên đầy đủ theo scope |
| `node.sequence` | Thứ tự duyệt AST |
| `node.source` | Đoạn source rút gọn |
| `node.attributes` | Một số thuộc tính bổ sung |

---

## 11. Schema của MetadataEvent

```json
{
  "schema_version": "1.0",
  "event_time": "2026-07-22T11:19:01.113153Z",
  "repository": "huggingface/diffusers",
  "commit_hash": "b48d49d87b97753bab3921bf3b7db52e8f1d3c49",
  "file_id": "stable-file-id",
  "file_path": "src/diffusers/configuration_utils.py",
  "content_hash": "file-content-hash",
  "event_type": "SOURCE_METADATA_UPSERT",
  "metadata": {
    "size_bytes": 78643,
    "line_count": 1050,
    "node_count": 3216,
    "class_count": 3,
    "function_count": 26,
    "import_count": 16,
    "call_count": 201,
    "assignment_count": 85,
    "parse_status": "SUCCESS",
    "node_type_counts": {}
  }
}
```

Các trường quan trọng cho Spark và MongoDB:

```text
file_id
file_path
content_hash
event_time
metadata
```

Khuyến nghị:

```text
MongoDB _id = file_id
```

Việc này giúp replay cùng một file sẽ cập nhật document cũ thay vì chèn thêm document trùng.

---

## 12. Schema của ParserErrorEvent

Khi file bị lỗi cú pháp, Parser Service sinh file `.error.json`.

```json
{
  "schema_version": "1.0",
  "event_type": "PARSER_ERROR",
  "event_time": "2026-07-22T11:29:52.849483Z",
  "repository": "huggingface/diffusers",
  "commit_hash": "b48d49d87b97753bab3921bf3b7db52e8f1d3c49",
  "file_path": "tmp_invalid.py",
  "content_hash": "deefc0f9f0c86a52f2b2f8329b85308ca0c77f5a26f30814782faffe17dd373a",
  "error": {
    "type": "SyntaxError",
    "message": "'(' was never closed",
    "line": 1,
    "column": 20
  }
}
```

---

## 13. Bàn giao cho thành viên 2 — CPG Edges và Kafka

Thành viên 2 cần dùng trực tiếp các trường:

```text
node.id
node.parent_id
node.type
node.name
node.qualified_name
node.sequence
file_id
file_path
content_hash
event_time
```

### AST_CHILD

```text
node.parent_id --AST_CHILD--> node.id
```

Node `Module` gốc có `parent_id = null`, vì vậy không tạo cạnh đi vào node gốc.

### Stable Edge ID

Khuyến nghị:

```python
stable_id(
    repository,
    file_path,
    edge_type,
    source_id,
    target_id,
)
```

### Các loại cạnh cần tiếp tục

```text
AST_CHILD
CFG_NEXT
CFG_TRUE
CFG_FALSE
DEFINES
READS
WRITES
DFG_TO
CALLS
```

### Bốn Kafka topic dự kiến

```text
diffusers.cpg.nodes.v1
diffusers.cpg.edges.v1
diffusers.source.metadata.v1
diffusers.parser.errors.v1
```

### Yêu cầu producer

- Gửi `NodeEvent` vào topic node.
- Gửi `EdgeEvent` vào topic edge.
- Gửi `MetadataEvent` vào topic metadata.
- Gửi `ParserErrorEvent` vào topic lỗi.
- Mỗi message phải có `schema_version`, `event_time`, định danh file và stable ID.
- Kafka key khuyến nghị:
  - Node topic: `node.id`.
  - Edge topic: `edge.id`.
  - Metadata topic: `file_id`.
  - Error topic: `file_path`.

---

## 14. Bàn giao cho thành viên 3 — Neo4j Sink

Thành viên Neo4j cần đọc:

```text
diffusers.cpg.nodes.v1
diffusers.cpg.edges.v1
```

### Node upsert

```cypher
MERGE (n:CPGNode {id: $node_id})
SET n.type = $node_type,
    n.name = $node_name,
    n.qualified_name = $qualified_name,
    n.file_id = $file_id,
    n.file_path = $file_path,
    n.content_hash = $content_hash,
    n.updated_at = $event_time
```

### Relationship upsert

Dựa vào:

```text
edge.id
edge.type
edge.source_id
edge.target_id
```

Yêu cầu:

- `MERGE` node theo `node.id`.
- `MERGE` relationship theo stable edge ID.
- Không dùng `CREATE` thuần túy cho dữ liệu replay.
- Chạy lại cùng event không được làm tăng số node hoặc edge.
- Cần có index hoặc constraint cho `CPGNode.id`.

```cypher
CREATE CONSTRAINT cpg_node_id_unique IF NOT EXISTS
FOR (n:CPGNode)
REQUIRE n.id IS UNIQUE
```

---

## 15. Bàn giao cho thành viên 4 — Spark và MongoDB

Thành viên Spark đọc topic:

```text
diffusers.source.metadata.v1
```

Yêu cầu:

- Dùng Spark Structured Streaming.
- Parse JSON theo schema rõ ràng.
- Ghi metadata vào MongoDB.
- Bật checkpoint.
- Dùng `file_id` làm khóa upsert.
- Replay cùng một file không được tạo document trùng.

Các trường chính:

```text
file_id
file_path
content_hash
commit_hash
event_time
metadata.size_bytes
metadata.line_count
metadata.node_count
metadata.class_count
metadata.function_count
metadata.import_count
metadata.call_count
metadata.assignment_count
metadata.parse_status
metadata.node_type_counts
```

Khuyến nghị document MongoDB:

```json
{
  "_id": "file_id",
  "repository": "huggingface/diffusers",
  "file_path": "src/diffusers/configuration_utils.py",
  "commit_hash": "...",
  "content_hash": "...",
  "event_time": "...",
  "metadata": {
    "node_count": 3216,
    "class_count": 3,
    "function_count": 26
  }
}
```

---

## 16. Chạy unit test

```powershell
python -m pytest tests/unit -v
```

Kết quả hiện tại:

```text
9 passed
```

Các nhóm kiểm thử đã có:

- Stable ID deterministic.
- Input khác tạo ID khác.
- Content hash deterministic.
- Content hash thay đổi khi nội dung thay đổi.
- AST extractor nhận diện đúng node.
- Qualified name đúng.
- Node ID không trùng.
- Parser Service sinh node và metadata.
- Parser Service sinh error event khi lỗi cú pháp.

---

## 17. Quy trình Git cho từng thành viên

Mỗi thành viên chỉ làm trên branch của mình.

### Trước khi làm

```powershell
git switch <branch-cua-minh>
git pull origin <branch-cua-minh>
git merge main
```

### Sau khi hoàn thành một phần

```powershell
git status
git add <cac-file-can-commit>
git commit -m "feat(...): ..."
git push origin <branch-cua-minh>
```

Sau đó tạo Pull Request:

```text
branch cá nhân → main
```

Không push trực tiếp code đang phát triển vào `main`.

---

## 18. Quy ước phối hợp

Trước khi thay đổi schema event, cần báo cho cả nhóm.

Không tự ý đổi tên các trường sau:

```text
schema_version
event_time
repository
commit_hash
file_id
file_path
content_hash
event_type
node.id
node.parent_id
edge.id
edge.source_id
edge.target_id
```

Nếu cần đổi schema:

1. Thảo luận với các thành viên phụ thuộc.
2. Tăng `schema_version`.
3. Cập nhật producer.
4. Cập nhật Neo4j sink.
5. Cập nhật Spark schema.
6. Cập nhật notebook và tài liệu.

---

## 19. Phần notebook và Jupyter Book

Source code được đặt trong `src/`, còn notebook dùng để:

- Giải thích cách triển khai.
- Import code từ `src/`.
- Chạy thử.
- Hiển thị output thực tế.
- Ghi nhận lỗi và cách xử lý.
- Viết reflection.

Không chép toàn bộ source code vào notebook.

Các notebook dự kiến:

```text
book/
├── 01_repository_cloning_and_discovery.ipynb
├── 02_incremental_parser_service.ipynb
├── 03_cpg_edges_and_kafka.ipynb
├── 04_neo4j_sink.ipynb
├── 05_spark_mongodb.ipynb
└── 06_replay_and_idempotency.ipynb
```

---

## 20. Checklist bàn giao

### Thành viên 2

- [ ] Đã merge `main` vào `feature/kafka-cpg`.
- [ ] Chạy được Parser Service.
- [ ] Đọc được file `.nodes.jsonl`.
- [ ] Hiểu `node.id` và `node.parent_id`.
- [ ] Tạo được `AST_CHILD`.
- [ ] Hoàn thiện CFG, DFG và call edge.
- [ ] Gửi event lên bốn Kafka topic.

### Thành viên 3

- [ ] Đã merge `main` vào `feature/neo4j-sink`.
- [ ] Nắm schema NodeEvent.
- [ ] Chờ schema EdgeEvent chính thức.
- [ ] Tạo constraint cho node ID.
- [ ] Dùng `MERGE` để bảo đảm idempotency.
- [ ] Kiểm tra replay không tăng node/edge.

### Thành viên 4

- [ ] Đã merge `main` vào `feature/spark-mongodb`.
- [ ] Nắm schema MetadataEvent.
- [ ] Đọc topic metadata bằng Spark.
- [ ] Ghi MongoDB bằng upsert.
- [ ] Dùng `file_id` làm `_id`.
- [ ] Bật checkpoint.
- [ ] Kiểm tra replay không tạo document trùng.

---

## 21. Thông tin cần gửi khi gặp lỗi tích hợp

```text
1. Branch đang dùng
2. Commit hiện tại
3. Lệnh đã chạy
4. Toàn bộ thông báo lỗi
5. Schema event thực tế
6. Một message mẫu
7. Kết quả git status
```

Lệnh hỗ trợ:

```powershell
git branch --show-current
git log --oneline -5
git status
python --version
python -m pytest tests/unit -v
```

---

## 22. Trạng thái bàn giao

```text
[x] File Discovery
[x] Stable ID
[x] Content Hash
[x] AST Extraction
[x] NodeEvent
[x] MetadataEvent
[x] ParserErrorEvent
[x] Unit Test
[x] Merge vào main
[x] Đồng bộ feature/kafka-cpg
[ ] CPG Edges
[ ] Kafka Producer
[ ] Neo4j Sink
[ ] Spark Streaming
[ ] MongoDB Sink
[ ] Replay toàn pipeline
[ ] Jupyter Book
[ ] GitHub Pages
```
