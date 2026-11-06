"""Interpreter for Rameev"""

from core.ast import (
    Assign, BinOp, Block, Bool, Break, Call, Continue, If,
    Index, ListLiteral, None_, Number, Print, Program, String,
    UnaryOp, Variable, While,
)


class RuntimeError_(Exception):
    pass


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class Environment:
    def __init__(self):
        self.vars = {}

    def get(self, name):
        if name not in self.vars:
            raise RuntimeError_(f"Переменная '{name}' не определена")
        return self.vars[name]

    def set(self, name, value):
        self.vars[name] = value


def format_value(v):
    if v is None:
        return 'none'
    if v is True:
        return 'True'
    if v is False:
        return 'False'
    if isinstance(v, list):
        return '[' + ', '.join(format_value(x) for x in v) + ']'
    return str(v)


class Interpreter:
    def __init__(self):
        self.env = Environment()

    def run(self, program):
        if not isinstance(program, Program):
            raise RuntimeError_(
                f"Ожидалась Program, получено {type(program).__name__}"
            )
        for stmt in program.statements:
            self.execute(stmt)

    def execute(self, node):
        if isinstance(node, Assign):
            return self.exec_assign(node)
        if isinstance(node, Print):
            return self.exec_print(node)
        if isinstance(node, If):
            return self.exec_if(node)
        if isinstance(node, While):
            return self.exec_while(node)
        if isinstance(node, Block):
            return self.exec_block(node)
        if isinstance(node, Break):
            raise BreakException()
        if isinstance(node, Continue):
            raise ContinueException()
        if isinstance(node, Call):
            # вызов как statement: add(f, 4) на отдельной строке
            self.eval(node)
            return
        raise RuntimeError_(f"Неизвестный узел: {type(node).__name__}")

    def exec_block(self, node):
        for stmt in node.statements:
            self.execute(stmt)

    def exec_print(self, node):
        values = [self.eval(arg) for arg in node.args]
        print(' '.join(format_value(v) for v in values))

    def exec_if(self, node):
        if self._truthy(self.eval(node.cond)):
            self.exec_block(node.then_block)
        elif node.else_block is not None:
            self.exec_block(node.else_block)

    def exec_while(self, node):
        while self._truthy(self.eval(node.cond)):
            try:
                self.exec_block(node.body)
            except BreakException:
                break
            except ContinueException:
                continue

    def exec_assign(self, node):
        value = self.eval(node.expr)
        op = node.op
        if op in (':=', '='):
            new_value = value
        else:
            old = self.env.get(node.name)
            binop = {'+=': '+', '-=': '-', '*=': '*', '/=': '/'}[op]
            new_value = self._binary(binop, old, value)
        self.env.set(node.name, new_value)
        return new_value

    def eval(self, node):
        if isinstance(node, Number):
            return node.value
        if isinstance(node, String):
            return node.value
        if isinstance(node, Bool):
            return node.value
        if isinstance(node, None_):
            return None
        if isinstance(node, Variable):
            return self.env.get(node.name)
        if isinstance(node, BinOp):
            return self.eval_binop(node)
        if isinstance(node, UnaryOp):
            return self.eval_unary(node)
        if isinstance(node, ListLiteral):
            return [self.eval(e) for e in node.elements]
        if isinstance(node, Index):
            return self.eval_index(node)
        if isinstance(node, Call):
            return self.eval_call(node)
        raise RuntimeError_(f"Неизвестный узел: {type(node).__name__}")

    def eval_index(self, node):
        coll = self.eval(node.collection)
        idx = self.eval(node.index)

        if not isinstance(idx, int) or isinstance(idx, bool):
            raise RuntimeError_("Индекс должен быть целым числом")

        if isinstance(coll, list):
            if idx < 0 or idx >= len(coll):
                raise RuntimeError_(
                    f"Индекс {idx} вне диапазона [0..{len(coll) - 1}]"
                )
            return coll[idx]

        if isinstance(coll, str):
            if idx < 0 or idx >= len(coll):
                raise RuntimeError_(
                    f"Индекс {idx} вне диапазона [0..{len(coll) - 1}]"
                )
            return coll[idx]

        raise RuntimeError_(
            f"Индексация работает только для списков и строк, "
            f"получено {type(coll).__name__}"
        )

    def eval_call(self, node):
        name = node.name
        args = [self.eval(a) for a in node.args]

        if name == 'len':
            if len(args) != 1:
                raise RuntimeError_("len() принимает 1 аргумент")
            v = args[0]
            if isinstance(v, (str, list)):
                return len(v)
            raise RuntimeError_("len() работает только со строками и списками")

        if name == 'gud':
            if len(args) == 0:
                return input()
            if len(args) == 1:
                return input(format_value(args[0]))
            raise RuntimeError_("gud() принимает 0 или 1 аргумент")

        if name == 'int':
            if len(args) != 1:
                raise RuntimeError_("int() принимает 1 аргумент")
            v = args[0]
            if isinstance(v, bool):
                return 1 if v else 0
            if isinstance(v, int):
                return v
            if isinstance(v, float):
                return int(v)
            if isinstance(v, str):
                try:
                    return int(v)
                except ValueError:
                    raise RuntimeError_(
                        f"Не могу преобразовать {v!r} в целое число"
                    )
            raise RuntimeError_(f"int() не работает с {type(v).__name__}")

        if name == 'str':
            if len(args) != 1:
                raise RuntimeError_("str() принимает 1 аргумент")
            return format_value(args[0])

        if name == 'dbl':
            if len(args) != 1:
                raise RuntimeError_("dbl() принимает 1 аргумент")
            v = args[0]
            if isinstance(v, bool):
                return 1.0 if v else 0.0
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                try:
                    return float(v)
                except ValueError:
                    raise RuntimeError_(
                        f"Не могу преобразовать {v!r} в число"
                    )
            raise RuntimeError_(f"dbl() не работает с {type(v).__name__}")

        if name == 'add':
            if len(args) != 2:
                raise RuntimeError_(
                    "add() принимает 2 аргумента: add(список, значение)"
                )
            lst, val = args
            if not isinstance(lst, list):
                raise RuntimeError_("Первый аргумент add() должен быть списком")

            # Проверка типа: числовой список не принимает текст
            if lst and all(
                isinstance(x, (int, float)) and not isinstance(x, bool)
                for x in lst
            ):
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise RuntimeError_(
                        "В числовой список можно добавлять только числа"
                    )
            elif lst and all(isinstance(x, str) for x in lst):
                if not isinstance(val, str):
                    val = format_value(val)

            lst.append(val)
            return None

        if name == 'remove':
            if len(args) != 2:
                raise RuntimeError_(
                    "remove() принимает 2 аргумента: remove(список, индекс)"
                )
            lst, idx = args
            if not isinstance(lst, list):
                raise RuntimeError_("Первый аргумент remove() должен быть списком")
            if not isinstance(idx, int) or isinstance(idx, bool):
                raise RuntimeError_("Индекс должен быть целым числом")
            if idx < 0 or idx >= len(lst):
                raise RuntimeError_(
                    f"Индекс {idx} вне диапазона [0..{len(lst) - 1}]"
                )
            lst.pop(idx)
            return None

        raise RuntimeError_(f"Неизвестная функция: {name}()")

    def eval_binop(self, node):
        op = node.op
        if op == 'and':
            if not self._truthy(self.eval(node.left)):
                return False
            return self._truthy(self.eval(node.right))
        if op == 'or':
            if self._truthy(self.eval(node.left)):
                return True
            return self._truthy(self.eval(node.right))
        left = self.eval(node.left)
        right = self.eval(node.right)
        return self._binary(op, left, right)

    def eval_unary(self, node):
        operand = self.eval(node.operand)
        if node.op == 'not':
            return not self._truthy(operand)
        if node.op == '-':
            if not isinstance(operand, (int, float)) or isinstance(operand, bool):
                raise RuntimeError_("Унарный минус требует число")
            return -operand
        raise RuntimeError_(f"Неизвестный унарный оператор: {node.op!r}")

    def _truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, (str, list)):
            return len(value) > 0
        return True

    def _binary(self, op, left, right):
        # Строки: + (конкатенация), * (повторение), == / !=
        if isinstance(left, str) or isinstance(right, str):
            if op == '+':
                return format_value(left) + format_value(right)
            if op == '*':
                if isinstance(left, str) and isinstance(right, int) and not isinstance(right, bool):
                    return left * right
                if isinstance(left, int) and not isinstance(left, bool) and isinstance(right, str):
                    return left * right
                raise RuntimeError_(
                    "Умножение строки возможно только на целое число, "
                    f"получено {type(left).__name__} и {type(right).__name__}"
                )
            if op == '==':
                return left == right
            if op == '!=':
                return left != right
            raise RuntimeError_(f"Операция '{op}' не поддерживается для строк")

        # Равенство — для любых типов (числа, bool, none, списки)
        if op == '==':
            return left == right
        if op == '!=':
            return left != right

        # Арифметика и сравнение — только числа
        if not isinstance(left, (int, float)) or isinstance(left, bool) \
           or not isinstance(right, (int, float)) or isinstance(right, bool):
            raise RuntimeError_(
                f"Операция '{op}' требует числа, получено "
                f"{type(left).__name__} и {type(right).__name__}"
            )

        if op == '+':  return left + right
        if op == '-':  return left - right
        if op == '*':  return left * right
        if op == '/':
            if right == 0:
                raise RuntimeError_("Деление на ноль")
            return left / right
        if op == '<':  return left < right
        if op == '>':  return left > right
        if op == '<=': return left <= right
        if op == '>=': return left >= right
        raise RuntimeError_(f"Неизвестный оператор: {op!r}")