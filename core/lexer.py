"""Lexer for Rameev"""

import re
from collections import namedtuple

Token = namedtuple('Token', ['type', 'value'])

KEYWORDS = {
    'print', 'if', 'else', 'while',
    'and', 'or', 'not',
    'True', 'False', 'none',
    'break', 'continue',
}

TOKEN_SPECIFICATION = [
    ('COMMENT',   r'//[^\n]*'),
    ('NUMBER',    r'\d+(\.\d*)?'),
    ('STRING',    r'"[^"]*"|\'[^\']*\''),
    ('ID',        r'[a-zA-Z_][a-zA-Z_0-9]*'),
    ('OP',        r'==|!=|<=|>=|\+=|-=|\*=|/=|:=|[+\-*/=<>]'),
    ('LPAREN',    r'\('),
    ('RPAREN',    r'\)'),
    ('LBRACE',    r'\{'),
    ('RBRACE',    r'\}'),
    ('LBRACKET',  r'\['),
    ('RBRACKET',  r'\]'),
    ('COMMA',     r','),
    ('SKIP',      r'[ \t]+'),
    ('NEWLINE',   r'\n'),
    ('MISMATCH',  r'.'),
]


def lex(code):
    tok_regex = '|'.join(
        f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION
    )

    for match in re.finditer(tok_regex, code):
        kind = match.lastgroup
        value = match.group()

        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
            yield Token(kind, value)
        elif kind == 'STRING':
            yield Token(kind, value[1:-1])
        elif kind == 'ID':
            token_type = value.upper() if value in KEYWORDS else 'ID'
            yield Token(token_type, value)
        elif kind == 'OP':
            yield Token(kind, value)
        elif kind in ('NEWLINE', 'SKIP', 'COMMENT'):
            continue
        elif kind in ('LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
                      'LBRACKET', 'RBRACKET', 'COMMA'):
            yield Token(kind, value)
        elif kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character: {value!r}')