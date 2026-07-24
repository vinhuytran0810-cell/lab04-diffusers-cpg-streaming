import ast

class CFGBuilder(ast.NodeVisitor):
    def __init__(self):
        self.edges = []
        self.previous_node = None

    def visit(self, node):
        """Override visit to add sequential CFG edges."""
        if isinstance(node, (ast.stmt, ast.expr)):
            if self.previous_node:
                self.edges.append({
                    'type': 'CFG_NEXT',
                    'source_ast': self.previous_node,
                    'target_ast': node
                })
            self.previous_node = node
        
        # Continue traversing
        super().visit(node)

def build_cfg(tree):
    """
    Builds a basic Control Flow Graph.
    Note: For a full CFG, we would need to handle branching, loops, and jumps.
    This provides a simplified sequential flow for the lab's educational purposes.
    """
    builder = CFGBuilder()
    builder.visit(tree)
    return builder.edges
