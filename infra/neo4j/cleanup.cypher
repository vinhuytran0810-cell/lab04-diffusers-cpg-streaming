// ============================================================
// Xóa snapshot CPG cũ của đúng một file trước khi parse lại.
// Truyền tham số $file_id khi chạy.
// Ví dụ trong Neo4j Browser:
//   :param file_id => 'file:abc123'
// Sau đó chạy phần Cypher bên dưới.
// ============================================================

MATCH (n:CPGNode)
WHERE n.file_id = $file_id
DETACH DELETE n;
