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

    def print_tree(self, node, a=None):
        """Print tree"""

        if type(a).__name__ == 'FunctionDef':
            print("-" * node.depth + 'function: ', a.name)
        elif type(a).__name__ == 'arg':
            print("-" * node.depth + a.arg)
        elif type(a).__name__ == 'Name':
            print("-" * node.depth + a.id)
        elif type(a).__name__ == 'Add':
            print("-" * node.depth + '+')
        elif type(a).__name__ == 'Num':
            print("-" * node.depth + '{}'.format(a.n))
        elif type(a).__name__ == 'Assign':
            print("-" * node.depth + '=')
        elif type(a).__name__ == 'Lt':
            print("-" * node.depth + '<')
        else:
            print("-" * node.depth + node.name)

        for child, child_node in zip(node.children, node.ast_node):
            self.print_tree(child, child_node)

    def execute(self, node, local_var=None):
        """
        Restore from the AST node to the Python source code, execute through function exec,
        and get the variables to execute the code, which are returned as list of tuple:
        [(varname1, varvalue1), (varname2, varvalue2), (varname3, varvalue3), ...]
        """
        exec(astunparse.unparse(node), local_var)

        return [(i, j) for i, j in locals().items() if not i.startswith('_') and
                i != 'node' and i != 'self' and i != 'local_var']

    def visit(self, node, tree_node, depth=0):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
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

    def code_analysis(self, node):
        local_var = {}
        statement_queue = node
        ind = 1

        # 2.18 -> print current lines, print numbers
        # 2.22 close boolean operation, maybe two conditions

        while len(statement_queue):
            statement = statement_queue[0]
            if type(statement).__name__ == 'FunctionDef':
                local_var.update(visitor.execute(statement, local_var))
                statement_queue = statement_queue[1:]
            elif type(statement).__name__ == 'While':
                test = statement.test
                test_code = astunparse.unparse(test).strip('\n')
                test_bool = eval(test_code, local_var)
                test_var = []
                if hasattr(test, 'left'):
                    test_var.extend(get_test_variable(test))
                else:
                    for test_item in test.values:
                        test_var.extend(get_test_variable(test_item))
                print('The test condition of line %d: %s' % (ind, test_code), '\t',
                      'the values of test variable: ',
                      '  '.join(["{}={}".format(i, local_var[i]) for i in test_var]),
                      '\t', 'the result is: ', test_bool)

                quantity = []
                if type(test).__name__ == 'Compare':
                    quantity.append(
                        eval(astunparse.unparse(test.comparators), local_var) - eval(astunparse.unparse(test.left),
                                                                                     local_var))
                elif type(test).__name__ == 'BoolOp':
                    quantity.extend([eval(astunparse.unparse(test_item.comparators), local_var) - eval(
                        astunparse.unparse(test_item.left), local_var) for test_item in test.values])

                if test_bool:
                    if len(quantity) == 0:
                        print("\tThe bool operation is open.")
                    else:
                        print("\tThe bool operation is open, quantity is: ", end='')
                        print(*quantity, sep='  ')
                    statement_queue = statement.body + [ind] + statement_queue
                    ind += 1
                else:
                    if len(quantity) == 0:
                        print("\tThe bool operation is close")
                    else:
                        print("\tThe bool operation is close, quantity is: ", end='')
                        print(*quantity, sep='  ')
                    statement_queue = statement_queue[1:]
                    ind += 1
            elif type(statement).__name__ == 'int':
                ind = statement
                statement_queue = statement_queue[1:]
            else:
                code = astunparse.unparse(statement).strip('\n')
                print("The statement of line %d: %s" % (ind, code))
                local_var.update(visitor.execute(statement, local_var))
                print('\t', '  '.join(["{}={}".format(key, value) for key, value in local_var.items()
                                       if key != '__builtins__' and type(local_var[key]).__name__ != 'function']))
                statement_queue = statement_queue[1:]
                ind += 1


def get_test_variable(test):
    var_list = []

    def visit(test):
        for field, value in iter_fields(test):
            if field == 'id':
                var_list.append(value)
            else:
                if field == 'left':
                    visit(test.left)
                elif field == 'right':
                    visit(test.right)

    visit(test)

    return var_list


if __name__ == "__main__":
    with open('test1.txt', 'r', encoding='utf8') as reader:
        code = reader.read()
        tree = ast.parse(code)
        visitor = CustomVisitor(tree)
        visitor.visit(tree, visitor.root)
        visitor.print_tree(visitor.root)
        visitor.code_analysis(visitor.root.ast_node)
