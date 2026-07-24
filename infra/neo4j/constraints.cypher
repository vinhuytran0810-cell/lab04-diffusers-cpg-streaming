// ============================================================
// CPG GRAPH CONSTRAINTS AND INDEXES
// Repository: huggingface/diffusers
// Schema version: 1.0
// ============================================================


// ------------------------------------------------------------
// 1. UNIQUE CONSTRAINT FOR CPG NODE ID
// ------------------------------------------------------------
// Mỗi CPGNode chỉ được có một stable ID duy nhất.
//
// Constraint này ngăn việc tồn tại hai node có cùng id
// khi cùng một file được parse và replay nhiều lần.

CREATE CONSTRAINT cpg_node_id_unique IF NOT EXISTS
FOR (n:CPGNode)
REQUIRE n.id IS UNIQUE;


// ------------------------------------------------------------
// 2. INDEX FOR FILE ID
// ------------------------------------------------------------
// Dùng để:
// - tìm tất cả node thuộc một file;
// - cleanup dữ liệu cũ của file;
// - kiểm tra graph theo file;
// - hỗ trợ idempotent replay.

CREATE INDEX cpg_node_file_id_index IF NOT EXISTS
FOR (n:CPGNode)
ON (n.file_id);


// ------------------------------------------------------------
// 3. INDEX FOR NODE TYPE
// ------------------------------------------------------------
// Dùng khi đếm hoặc truy vấn theo loại node:
//
// Function, Class, Statement, Expression, Call,...

CREATE INDEX cpg_node_type_index IF NOT EXISTS
FOR (n:CPGNode)
ON (n.node_type);


// ------------------------------------------------------------
// 4. INDEX FOR FILE PATH
// ------------------------------------------------------------
// Dùng để tìm dữ liệu graph theo đường dẫn file Python.

CREATE INDEX cpg_node_file_path_index IF NOT EXISTS
FOR (n:CPGNode)
ON (n.file_path);


// ------------------------------------------------------------
// 5. INDEX FOR REPOSITORY
// ------------------------------------------------------------
// Hỗ trợ truy vấn dữ liệu theo repository.

CREATE INDEX cpg_node_repository_index IF NOT EXISTS
FOR (n:CPGNode)
ON (n.repository);