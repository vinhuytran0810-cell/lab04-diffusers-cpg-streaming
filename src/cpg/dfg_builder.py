import ast

class DFGBuilder(ast.NodeVisitor):
    def __init__(self):
        self.edges = []
        self.variables = {}  # var_name -> last_ast_node_that_assigned_it

    def visit_Assign(self, node):
        # Handle the assignment targets
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables[target.id] = target
        
        # Then visit the value being assigned
        self.visit(node.value)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            # The variable is being read.
            if node.id in self.variables:
                # Add a data flow edge from the last assignment to this read
                self.edges.append({
                    'type': 'DFG_DATA_DEPENDENCY',
                    'source_ast': self.variables[node.id],
                    'target_ast': node,
                    'variable': node.id
                })
        elif isinstance(node.ctx, ast.Store):
            # The variable is being written to
            self.variables[node.id] = node

def build_dfg(tree):
    """
    Builds a basic Data Flow Graph by tracking variable assignments and usages.
    """
    builder = DFGBuilder()
    builder.visit(tree)
    return builder.edges
