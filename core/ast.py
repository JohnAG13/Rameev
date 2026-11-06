"""Abstract Syntax Tree classes for Rameev"""


class Number:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f'Number({self.value})'


class String:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f'String({self.value!r})'


class Bool:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f'Bool({self.value})'


class None_:
    def __repr__(self):
        return 'None_'


class Variable:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f'Variable({self.name!r})'


class BinOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    def __repr__(self):
        return f'BinOp({self.left!r}, {self.op!r}, {self.right!r})'


class UnaryOp:
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand
    def __repr__(self):
        return f'UnaryOp({self.op!r}, {self.operand!r})'


class Assign:
    def __init__(self, name, op, expr):
        self.name = name
        self.op = op
        self.expr = expr
    def __repr__(self):
        return f'Assign({self.name!r}, {self.op!r}, {self.expr!r})'


class Print:
    def __init__(self, args):
        self.args = args
    def __repr__(self):
        return f'Print({self.args!r})'


class Block:
    def __init__(self, statements):
        self.statements = statements
    def __repr__(self):
        return f'Block({self.statements!r})'


class If:
    def __init__(self, cond, then_block, else_block):
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block
    def __repr__(self):
        return f'If({self.cond!r}, {self.then_block!r}, {self.else_block!r})'


class While:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body
    def __repr__(self):
        return f'While({self.cond!r}, {self.body!r})'


class Break:
    def __repr__(self):
        return 'Break()'


class Continue:
    def __repr__(self):
        return 'Continue()'


# --- НОВЫЕ УЗЛЫ ---

class ListLiteral:
    def __init__(self, elements):
        self.elements = elements
    def __repr__(self):
        return f'ListLiteral({self.elements!r})'


class Index:
    def __init__(self, collection, index):
        self.collection = collection
        self.index = index
    def __repr__(self):
        return f'Index({self.collection!r}, {self.index!r})'


class Call:
    def __init__(self, name, args):
        self.name = name
        self.args = args
    def __repr__(self):
        return f'Call({self.name!r}, {self.args!r})'


class Program:
    def __init__(self, statements):
        self.statements = statements
    def __repr__(self):
        return f'Program({self.statements!r})'