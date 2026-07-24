import ast
import hashlib
import time
from .cfg_builder import build_cfg
from .dfg_builder import build_dfg

def generate_stable_id(filepath, node_type, lineno, col_offset):
    """
    Generates a stable identifier for a node based on its properties.
    This ensures idempotency upon replay.
    """
    raw_str = f"{filepath}:{node_type}:{lineno}:{col_offset}"
    return hashlib.md5(raw_str.encode('utf-8')).hexdigest()

def get_node_details(node):
    if hasattr(node, 'lineno'):
        return node.lineno, node.col_offset
    return -1, -1

class ASTEdgeExtractor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.nodes = []
        self.edges = []
        self.call_edges = []
        self.node_id_map = {} # Maps ast object to its stable ID

    def get_or_create_id(self, node):
        if id(node) in self.node_id_map:
            return self.node_id_map[id(node)]
        
        lineno, col_offset = get_node_details(node)
        node_type = type(node).__name__
        node_id = generate_stable_id(self.filepath, node_type, lineno, col_offset)
        
        self.node_id_map[id(node)] = node_id
        
        # Add to nodes list
        self.nodes.append({
            'id': node_id,
            'filepath': self.filepath,
            'type': node_type,
            'lineno': lineno,
            'col_offset': col_offset
        })
        return node_id

    def visit(self, node):
        node_id = self.get_or_create_id(node)
        
        # Check for call edges
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                self.call_edges.append({
                    'type': 'CALL_EDGE',
                    'source_id': node_id,
                    'target_name': node.func.id
                })

        # Traverse children and create AST edges
        for child in ast.iter_child_nodes(node):
            child_id = self.get_or_create_id(child)
            self.edges.append({
                'id': hashlib.md5(f"AST:{node_id}:{child_id}".encode()).hexdigest(),
                'type': 'AST_PARENT_OF',
                'source_id': node_id,
                'target_id': child_id
            })
            self.visit(child)

def extract_cpg(filepath):
    """
    Parses a python file and extracts nodes and edges for the CPG.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except Exception as e:
        return {'nodes': [], 'edges': [], 'error': str(e)}

    # Extract AST nodes and edges
    extractor = ASTEdgeExtractor(filepath)
    extractor.visit(tree)

    nodes = extractor.nodes
    edges = extractor.edges

    # Add Call Edges
    for c_edge in extractor.call_edges:
        edges.append({
            'id': hashlib.md5(f"CALL:{c_edge['source_id']}:{c_edge['target_name']}".encode()).hexdigest(),
            'type': c_edge['type'],
            'source_id': c_edge['source_id'],
            'target_id': c_edge['target_name'] # Note: In a real CPG, this points to the function def node
        })

    # Add CFG edges
    cfg_edges_raw = build_cfg(tree)
    for cfg in cfg_edges_raw:
        src_id = extractor.get_or_create_id(cfg['source_ast'])
        tgt_id = extractor.get_or_create_id(cfg['target_ast'])
        edges.append({
            'id': hashlib.md5(f"CFG:{src_id}:{tgt_id}".encode()).hexdigest(),
            'type': cfg['type'],
            'source_id': src_id,
            'target_id': tgt_id
        })

    # Add DFG edges
    dfg_edges_raw = build_dfg(tree)
    for dfg in dfg_edges_raw:
        src_id = extractor.get_or_create_id(dfg['source_ast'])
        tgt_id = extractor.get_or_create_id(dfg['target_ast'])
        edges.append({
            'id': hashlib.md5(f"DFG:{src_id}:{tgt_id}:{dfg['variable']}".encode()).hexdigest(),
            'type': dfg['type'],
            'source_id': src_id,
            'target_id': tgt_id,
            'variable': dfg['variable']
        })

    # Compute metadata stats
    node_type_counts = {}
    for n in nodes:
        t = n['type']
        node_type_counts[t] = node_type_counts.get(t, 0) + 1

    class_count = node_type_counts.get('ClassDef', 0)
    function_count = node_type_counts.get('FunctionDef', 0) + node_type_counts.get('AsyncFunctionDef', 0)
    import_count = node_type_counts.get('Import', 0) + node_type_counts.get('ImportFrom', 0)
    call_count = node_type_counts.get('Call', 0)
    assignment_count = node_type_counts.get('Assign', 0) + node_type_counts.get('AnnAssign', 0) + node_type_counts.get('AugAssign', 0)

    metadata = {
        'size_bytes': len(source.encode('utf-8')),
        'line_count': len(source.splitlines()),
        'node_count': len(nodes),
        'class_count': class_count,
        'function_count': function_count,
        'import_count': import_count,
        'call_count': call_count,
        'assignment_count': assignment_count,
        'parse_status': 'SUCCESS',
        'node_type_counts': node_type_counts
    }

    return {
        'nodes': nodes,
        'edges': edges,
        'metadata': metadata,
        'content': source
    }
