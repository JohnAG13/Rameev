"""
Rameev to C Compiler & Runner (rameew)
Usage:
    python rameew.py <file.rmv>
    python rameew.py <file.rmv> --c-only
"""

import sys
import os
import subprocess
import shutil

sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import from core and rameev_c
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAMEEV_C_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from core.lexer import lex
from core.parser import Parser
from rameev_c.transpiler import CTranspiler


def find_c_compiler():
    compilers = ['gcc', 'clang', 'tcc', 'cl']
    for comp in compilers:
        if shutil.which(comp) is not None:
            return comp
    return None


def compile_and_run(rmv_path, c_only=False):
    if not os.path.exists(rmv_path):
        print(f"Ошибка: файл '{rmv_path}' не найден.", file=sys.stderr)
        sys.exit(1)

    with open(rmv_path, 'r', encoding='utf-8') as f:
        code = f.read()

    # 1. Лексический и синтаксический анализ
    try:
        tokens = list(lex(code))
        parser = Parser(tokens)
        ast = parser.parse()
    except SyntaxError as e:
        print(f"Синтаксическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Трансляция AST в C
    try:
        transpiler = CTranspiler()
        c_code = transpiler.transpile(ast)
    except Exception as e:
        print(f"Ошибка трансляции в C: {e}", file=sys.stderr)
        sys.exit(1)

    # Сохраняем .c файл
    base_name = os.path.splitext(os.path.basename(rmv_path))[0]
    output_dir = os.path.dirname(os.path.abspath(rmv_path))
    c_path = os.path.join(output_dir, f"{base_name}.c")
    exe_path = os.path.join(output_dir, f"{base_name}.exe")

    with open(c_path, 'w', encoding='utf-8') as f:
        f.write(c_code)

    print(f"[Rameev -> C] Сгенерирован Си-код: {c_path}")

    if c_only:
        return

    # 3. Поиск C-компилятора и сборка .exe
    compiler = find_c_compiler()

    if compiler is None:
        print("\n[!] Си-код успешно создан, но C-компилятор (gcc, clang, cl или tcc) не найден в PATH.")
        print(f"    Чтобы скомпилировать вручную, установите MinGW/GCC или TCC и выполните:")
        print(f'    gcc -I "{RAMEEV_C_DIR}" "{c_path}" -o "{exe_path}"')
        print(f'    "{exe_path}"')
        return

    print(f"[Rameev -> C] Компиляция через {compiler}...")

    if compiler in ('gcc', 'clang', 'tcc'):
        cmd = [compiler, f"-I{RAMEEV_C_DIR}", c_path, "-o", exe_path]
    elif compiler == 'cl':
        cmd = ['cl', f"/I{RAMEEV_C_DIR}", c_path, f"/Fe:{exe_path}"]

    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("[!] Ошибка компиляции C-кода.", file=sys.stderr)
        sys.exit(res.returncode)

    print(f"[Rameev -> C] Скомпилирован исполняемый файл: {exe_path}")
    print("[Rameev -> C] Запуск программы...\n" + "-" * 40)

    run_res = subprocess.run([exe_path])
    print("-" * 40 + f"\n[Rameev -> C] Программа завершилась с кодом {run_res.returncode}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python rameew.py <файл.rmv> [--c-only]")
        print("Пример: python rameew.py ../main.rmv")
        sys.exit(1)

    c_only_flag = '--c-only' in sys.argv
    file_arg = [arg for arg in sys.argv[1:] if not arg.startswith('--')][0]
    compile_and_run(file_arg, c_only=c_only_flag)

