import sys

sys.stdout.reconfigure(encoding='utf-8')   # ← добавь эту строку

from core.lexer import lex
from core.parser import Parser
from core.interpreter import Interpreter, RuntimeError_


def run_file(path):
    with open(path, 'r', encoding='utf-8') as f:   # ← и здесь encoding
        code = f.read()

    try:
        tokens = list(lex(code))
        parser = Parser(tokens)
        ast = parser.parse()
    except SyntaxError as e:
        print(f"Синтаксическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        Interpreter().run(ast)
    except RuntimeError_ as e:
        print(f"Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python main.py <файл.rmv>", file=sys.stderr)
        sys.exit(1)
    run_file(sys.argv[1])