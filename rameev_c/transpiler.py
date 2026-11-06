"""
Transpiler: Rameev -> C
Translates Rameev AST into pure, portable C99 code.
"""

import sys
import os

# Allow importing core from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ast import (
    Assign, BinOp, Block, Bool, Break, Call, Continue, If,
    Index, ListLiteral, None_, Number, Print, Program, String,
    UnaryOp, Variable, While,
)


class CTranspiler:
    def __init__(self):
        self.variables = set()
        self.indent_level = 1

    def indent(self):
        return "    " * self.indent_level

    def transpile(self, program: Program) -> str:
        # Pass 1: collect all variables
        self.collect_variables(program)

        # Pass 2: generate statements
        body_lines = []
        for stmt in program.statements:
            code = self.gen_statement(stmt)
            if code:
                body_lines.append(code)

        # Build full C file
        var_decls = []
        for v in sorted(self.variables):
            var_decls.append(f"    RValue rv_{v} = r_none();")

        vars_section = "\n".join(var_decls)
        if vars_section:
            vars_section += "\n"

        body_section = "\n".join(body_lines)

        c_code = f"""/* Generated automatically by Rameev C Transpiler */
#include "rameev_runtime.h"

int main(int argc, char** argv) {{
{vars_section}{body_section}
    return 0;
}}
"""
        return c_code

    def collect_variables(self, node):
        if isinstance(node, Program) or isinstance(node, Block):
            for stmt in node.statements:
                self.collect_variables(stmt)
        elif isinstance(node, Assign):
            self.variables.add(node.name)
            self.collect_variables(node.expr)
        elif isinstance(node, If):
            self.collect_variables(node.cond)
            self.collect_variables(node.then_block)
            if node.else_block:
                self.collect_variables(node.else_block)
        elif isinstance(node, While):
            self.collect_variables(node.cond)
            self.collect_variables(node.body)
        elif isinstance(node, Print):
            for a in node.args:
                self.collect_variables(a)
        elif isinstance(node, BinOp):
            self.collect_variables(node.left)
            self.collect_variables(node.right)
        elif isinstance(node, UnaryOp):
            self.collect_variables(node.operand)
        elif isinstance(node, Call):
            for a in node.args:
                self.collect_variables(a)
        elif isinstance(node, ListLiteral):
            for el in node.elements:
                self.collect_variables(el)
        elif isinstance(node, Index):
            self.collect_variables(node.collection)
            self.collect_variables(node.index)
        elif isinstance(node, Variable):
            self.variables.add(node.name)

    def gen_statement(self, stmt) -> str:
        ind = self.indent()
        if isinstance(stmt, Assign):
            var_name = f"rv_{stmt.name}"
            expr_c = self.gen_expr(stmt.expr)
            if stmt.op in ('=', ':='):
                return f"{ind}{var_name} = {expr_c};"
            elif stmt.op == '+=':
                return f"{ind}{var_name} = r_add({var_name}, {expr_c});"
            elif stmt.op == '-=':
                return f"{ind}{var_name} = r_sub({var_name}, {expr_c});"
            elif stmt.op == '*=':
                return f"{ind}{var_name} = r_mul({var_name}, {expr_c});"
            elif stmt.op == '/=':
                return f"{ind}{var_name} = r_div({var_name}, {expr_c});"
            raise NotImplementedError(f"Unknown assign op: {stmt.op}")

        if isinstance(stmt, Print):
            count = len(stmt.args)
            if count == 0:
                return f"{ind}r_print(0);"
            args_c = ", ".join(self.gen_expr(a) for a in stmt.args)
            return f"{ind}r_print({count}, {args_c});"

        if isinstance(stmt, If):
            cond_c = self.gen_expr(stmt.cond)
            res = [f"{ind}if (r_truthy({cond_c})) {{"]
            self.indent_level += 1
            for s in stmt.then_block.statements:
                res.append(self.gen_statement(s))
            self.indent_level -= 1
            if stmt.else_block:
                res.append(f"{ind}}} else {{")
                self.indent_level += 1
                for s in stmt.else_block.statements:
                    res.append(self.gen_statement(s))
                self.indent_level -= 1
            res.append(f"{ind}}}")
            return "\n".join(res)

        if isinstance(stmt, While):
            cond_c = self.gen_expr(stmt.cond)
            res = [f"{ind}while (r_truthy({cond_c})) {{"]
            self.indent_level += 1
            for s in stmt.body.statements:
                res.append(self.gen_statement(s))
            self.indent_level -= 1
            res.append(f"{ind}}}")
            return "\n".join(res)

        if isinstance(stmt, Break):
            return f"{ind}break;"

        if isinstance(stmt, Continue):
            return f"{ind}continue;"

        if isinstance(stmt, Call):
            return f"{ind}{self.gen_expr(stmt)};"

        if isinstance(stmt, Block):
            res = [f"{ind}{{"]
            self.indent_level += 1
            for s in stmt.statements:
                res.append(self.gen_statement(s))
            self.indent_level -= 1
            res.append(f"{ind}}}")
            return "\n".join(res)

        raise NotImplementedError(f"Statement not supported in C: {type(stmt).__name__}")

    def gen_expr(self, expr) -> str:
        if isinstance(expr, Number):
            if isinstance(expr.value, float):
                return f"r_dbl({expr.value})"
            return f"r_int({expr.value}LL)"

        if isinstance(expr, String):
            # C string escaping
            escaped = (expr.value
                       .replace('\\', '\\\\')
                       .replace('"', '\\"')
                       .replace('\n', '\\n')
                       .replace('\t', '\\t')
                       .replace('\r', '\\r'))
            return f'r_str("{escaped}")'

        if isinstance(expr, Bool):
            return "r_bool(true)" if expr.value else "r_bool(false)"

        if isinstance(expr, None_):
            return "r_none()"

        if isinstance(expr, Variable):
            return f"rv_{expr.name}"

        if isinstance(expr, ListLiteral):
            count = len(expr.elements)
            if count == 0:
                return "r_list_create(0)"
            items = ", ".join(self.gen_expr(el) for el in expr.elements)
            return f"r_list_create({count}, {items})"

        if isinstance(expr, Index):
            coll = self.gen_expr(expr.collection)
            idx = self.gen_expr(expr.index)
            return f"r_index({coll}, {idx})"

        if isinstance(expr, BinOp):
            l = self.gen_expr(expr.left)
            r = self.gen_expr(expr.right)
            op_map = {
                '+': 'r_add',
                '-': 'r_sub',
                '*': 'r_mul',
                '/': 'r_div',
                '==': 'r_eq',
                '!=': 'r_neq',
                '<': 'r_lt',
                '>': 'r_gt',
                '<=': 'r_lte',
                '>=': 'r_gte',
                'and': 'r_and',
                'or': 'r_or',
            }
            if expr.op in op_map:
                return f"{op_map[expr.op]}({l}, {r})"
            raise NotImplementedError(f"Binary operator {expr.op} not supported in C")

        if isinstance(expr, UnaryOp):
            operand = self.gen_expr(expr.operand)
            if expr.op == 'not':
                return f"r_not({operand})"
            if expr.op == '-':
                return f"r_neg({operand})"
            raise NotImplementedError(f"Unary operator {expr.op} not supported in C")

        if isinstance(expr, Call):
            name = expr.name
            args = expr.args
            if name == 'len':
                if len(args) != 1:
                    raise SyntaxError("len() requires 1 argument")
                return f"r_len({self.gen_expr(args[0])})"
            if name == 'int':
                if len(args) != 1:
                    raise SyntaxError("int() requires 1 argument")
                return f"r_to_int({self.gen_expr(args[0])})"
            if name == 'dbl':
                if len(args) != 1:
                    raise SyntaxError("dbl() requires 1 argument")
                return f"r_to_dbl({self.gen_expr(args[0])})"
            if name == 'str':
                if len(args) != 1:
                    raise SyntaxError("str() requires 1 argument")
                return f"r_to_str({self.gen_expr(args[0])})"
            if name == 'gud':
                if len(args) == 0:
                    return "r_gud(0)"
                elif len(args) == 1:
                    return f"r_gud(1, {self.gen_expr(args[0])})"
                raise SyntaxError("gud() accepts 0 or 1 argument")
            if name == 'add':
                if len(args) != 2:
                    raise SyntaxError("add() requires 2 arguments")
                return f"r_list_add({self.gen_expr(args[0])}, {self.gen_expr(args[1])})"
            if name == 'remove':
                if len(args) != 2:
                    raise SyntaxError("remove() requires 2 arguments")
                return f"r_list_remove({self.gen_expr(args[0])}, {self.gen_expr(args[1])})"

            raise NotImplementedError(f"Function call '{name}' is not recognized in C runtime")

        raise NotImplementedError(f"Expression type {type(expr).__name__} not supported in C")

