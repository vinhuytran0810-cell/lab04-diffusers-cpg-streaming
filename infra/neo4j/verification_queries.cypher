// ============================================================
// Task 4 - Verification Queries
// Chạy từng truy vấn trong Neo4j Browser và chụp kết quả.
// ============================================================

// 1. Tổng số node.
MATCH (n:CPGNode)
RETURN count(n) AS node_count;

// 2. Tổng số edge.
MATCH ()-[r]->()
RETURN count(r) AS edge_count;

// 3. Số node theo loại.
MATCH (n:CPGNode)
RETURN n.node_type AS node_type, count(*) AS total
ORDER BY total DESC, node_type;

// 4. Số edge theo loại.
MATCH ()-[r]->()
RETURN type(r) AS edge_type, count(*) AS total
ORDER BY total DESC, edge_type;

// 5. Kiểm tra duplicate node stable ID.
// Kết quả đúng: không có bản ghi.
MATCH (n:CPGNode)
WITH n.id AS id, count(*) AS total
WHERE id IS NOT NULL AND total > 1
RETURN id, total
ORDER BY total DESC;

// 6. Kiểm tra duplicate edge stable ID.
// Kết quả đúng: không có bản ghi.
MATCH ()-[r]->()
WITH r.id AS id, collect(DISTINCT type(r)) AS edge_types, count(*) AS total
WHERE id IS NOT NULL AND total > 1
RETURN id, edge_types, total
ORDER BY total DESC;

// 7. Kiểm tra placeholder còn sót.
// Kết quả lý tưởng sau khi node topic đã xử lý xong: 0.
MATCH (n:CPGNode)
WHERE coalesce(n.placeholder, false) = true
RETURN count(n) AS placeholder_count;

// 8. Kiểm tra node thiếu stable ID.
// Kết quả đúng: 0.
MATCH (n:CPGNode)
WHERE n.id IS NULL
RETURN count(n) AS nodes_without_id;

// 9. Kiểm tra edge thiếu stable ID.
// Kết quả đúng: 0.
MATCH ()-[r]->()
WHERE r.id IS NULL
RETURN count(r) AS edges_without_id;

// 10. Thống kê theo file.
MATCH (n:CPGNode)
WHERE n.file_id IS NOT NULL
OPTIONAL MATCH (n)-[r]->()
RETURN
  n.file_id AS file_id,
  max(n.file_path) AS file_path,
  count(DISTINCT n) AS node_count,
  count(DISTINCT r) AS outgoing_edge_count
ORDER BY node_count DESC;

// 11. Xem graph của một file.
// Trước khi chạy trong Neo4j Browser:
//   :param file_id => 'file:abc123'
MATCH p=(n:CPGNode)-[r*0..3]->(m:CPGNode)
WHERE n.file_id = $file_id
RETURN p
LIMIT 100;

// 12. Kiểm tra constraint và index.
SHOW CONSTRAINTS;

SHOW INDEXES;
