# -*- coding: UTF-8 -*-
import ast
from ast import iter_fields, AST
import astunparse


class Node:
    def __init__(self, name, depth=0):
        self.name = name
        self.depth = depth
        self.children = []
        self.ast_node = []


class CustomVisitor:

    def __init__(self, node):
        self.root = Node(type(node).__name__)

    def print_tree(self, node):
        print("--" * node.depth + node.name)
        for child in node.children:
            self.print_tree(child)

    def execute(self, node, local_var=None):
        # [(varname1, varvalue1), (varname2, varvalue2), (varname3, varvalue3), ...]
        exec(astunparse.unparse(node), local_var)

        return [(i, j) for i, j in locals().items() if  # __**__
                not i.startswith('_') and i != 'node' and i != 'self' and i != 'local_var']

    def visit(self, node, tree_node, depth=0):
        """Visit a node."""
        method = node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node, tree_node, depth)

    def generic_visit(self, node, tree_node, depth):
        depth += 1  # Denotes node depth
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        child = Node(type(item).__name__, depth)
                        tree_node.children.append(child)
                        tree_node.ast_node.append(item)
                        self.visit(item, child, depth)
            elif isinstance(value, AST):
                if type(value).__name__ == "Load" or type(value).__name__ == "Store":
                    continue
                child = Node(type(value).__name__, depth)
                tree_node.children.append(child)
                tree_node.ast_node.append(value)
                self.visit(value, child, depth)


if __name__ == "__main__":
    with open('test1.txt', 'r', encoding='utf8') as reader:
        code = reader.read()
        tree = ast.parse(code)
        visitor = CustomVisitor(tree)
        visitor.visit(tree, visitor.root)
        visitor.print_tree(visitor.root)
        local_var = {}
        for ind, statement in enumerate(visitor.root.ast_node):
            print("Local variable value after statement %s execution：" % (ind+1))
            local_var.update(visitor.execute(statement, local_var))
            print([(key, value) for key, value in local_var.items() if key != '__builtins__'])
