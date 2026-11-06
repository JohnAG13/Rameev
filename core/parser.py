"""Parser for Rameev"""

from core.ast import (
    Assign, BinOp, Block, Bool, Break, Call, Continue, If,
    Index, ListLiteral, None_, Number, Print, Program, String,
    UnaryOp, Variable, While,
)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        self.pos += 1

    def advance_and_get(self):
        tok = self.peek()
        self.advance()
        return tok

    def expect(self, token_type):
        tok = self.peek()
        if tok and tok.type == token_type:
            self.advance()
            return tok
        got = tok.type if tok else 'EOF'
        raise SyntaxError(f'Expected {token_type}, got {got}')

    # --- Верхний уровень ---

    def parse(self):
        statements = []
        while self.peek() is not None:
            statements.append(self.parse_statement())
        return Program(statements)

    def parse_block(self):
        self.expect('LBRACE')
        statements = []
        while self.peek() and self.peek().type != 'RBRACE':
            statements.append(self.parse_statement())
        self.expect('RBRACE')
        return Block(statements)

    def parse_statement(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError('Unexpected end of file')

        if tok.type == 'PRINT':
            return self.parse_print()
        if tok.type == 'IF':
            return self.parse_if()
        if tok.type == 'WHILE':
            return self.parse_while()
        if tok.type == 'BREAK':
            self.advance()
            return Break()
        if tok.type == 'CONTINUE':
            self.advance()
            return Continue()

        if tok.type == 'ID':
            # имя + '(' → это вызов функции как statement (например add(f, 4))
            if (self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1].type == 'LPAREN'):
                return self.parse_expression()
            return self.parse_assign()

        raise SyntaxError(f'Unexpected token: {tok}')

    def parse_assign(self):
        name = self.advance_and_get().value
        op_tok = self.expect('OP')
        if op_tok.value not in (':=', '=', '+=', '-=', '*=', '/='):
            raise SyntaxError(
                f'Expected assignment operator, got {op_tok.value!r}'
            )
        expr = self.parse_expression()
        return Assign(name, op_tok.value, expr)

    def parse_print(self):
        self.expect('PRINT')
        self.expect('LPAREN')
        args = []
        if self.peek() and self.peek().type != 'RPAREN':
            args.append(self.parse_expression())
            while self.peek() and self.peek().type == 'COMMA':
                self.advance()
                args.append(self.parse_expression())
        self.expect('RPAREN')
        return Print(args)

    def parse_if(self):
        self.expect('IF')
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        then_block = self.parse_block()
        else_block = None
        if self.peek() and self.peek().type == 'ELSE':
            self.advance()
            if self.peek() and self.peek().type == 'IF':
                else_block = Block([self.parse_if()])
            else:
                else_block = self.parse_block()
        return If(cond, then_block, else_block)

    def parse_while(self):
        self.expect('WHILE')
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_block()
        return While(cond, body)

    # --- Выражения ---

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.peek() and self.peek().type == 'OR':
            self.advance()
            right = self.parse_and()
            left = BinOp(left, 'or', right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek() and self.peek().type == 'AND':
            self.advance()
            right = self.parse_not()
            left = BinOp(left, 'and', right)
        return left

    def parse_not(self):
        if self.peek() and self.peek().type == 'NOT':
            self.advance()
            return UnaryOp('not', self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()
        if (self.peek() and self.peek().type == 'OP'
                and self.peek().value in ('==', '!=', '<', '>', '<=', '>=')):
            op = self.advance_and_get().value
            right = self.parse_additive()
            return BinOp(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while (self.peek() and self.peek().type == 'OP'
               and self.peek().value in ('+', '-')):
            op = self.advance_and_get().value
            right = self.parse_multiplicative()
            left = BinOp(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while (self.peek() and self.peek().type == 'OP'
               and self.peek().value in ('*', '/')):
            op = self.advance_and_get().value
            right = self.parse_unary()
            left = BinOp(left, op, right)
        return left

    def parse_unary(self):
        if self.peek() and self.peek().type == 'OP' and self.peek().value == '-':
            self.advance()
            return UnaryOp('-', self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        """Индексация: f[0], f[i+1], a[0][1]."""
        expr = self.parse_primary()
        while self.peek() and self.peek().type == 'LBRACKET':
            self.advance()
            idx = self.parse_expression()
            self.expect('RBRACKET')
            expr = Index(expr, idx)
        return expr

    def parse_primary(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError('Unexpected end of file in expression')

        if tok.type == 'NUMBER':
            self.advance()
            return Number(tok.value)
        if tok.type == 'STRING':
            self.advance()
            return String(tok.value)
        if tok.type == 'TRUE':
            self.advance()
            return Bool(True)
        if tok.type == 'FALSE':
            self.advance()
            return Bool(False)
        if tok.type == 'NONE':
            self.advance()
            return None_()

        if tok.type == 'ID':
            self.advance()
            if self.peek() and self.peek().type == 'LPAREN':
                # вызов функции: len(f), add(f, 4), gud(...)
                self.advance()
                args = []
                if self.peek() and self.peek().type != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.peek() and self.peek().type == 'COMMA':
                        self.advance()
                        args.append(self.parse_expression())
                self.expect('RPAREN')
                return Call(tok.value, args)
            return Variable(tok.value)

        if tok.type == 'LBRACKET':
            self.advance()
            elements = []
            if self.peek() and self.peek().type != 'RBRACKET':
                elements.append(self.parse_expression())
                while self.peek() and self.peek().type == 'COMMA':
                    self.advance()
                    elements.append(self.parse_expression())
            self.expect('RBRACKET')
            return ListLiteral(elements)

        if tok.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr

        raise SyntaxError(f'Unexpected token in expression: {tok}')