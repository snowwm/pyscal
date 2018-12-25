class Context(object):
    def __init__(self, line, line_no, pos):
        self.line = line
        self.line_no = line_no
        self.pos = pos

    def __repr__(self):
        return f'{str(self.line_no).ljust(5)}{self.line}'


class Token(object):
    def __init__(self, type):
        self.type = type
        self.ctx = None

    def __repr__(self):
        return self.type


class LiteralToken(Token):
    def __init__(self, value_type, value):
        super().__init__(LITERAL)
        self.value_type = value_type
        self.value = value

    def __repr__(self):
        return f'{self.type}({repr(self.value)})'


class IDToken(Token):
    def __init__(self, id):
        super().__init__(ID)
        self.id = id

    def __repr__(self):
        return f'{self.type}({repr(self.id)})'


# Keywords
PROGRAM = 'PROGRAM'
VAR = 'VAR'
DEF = 'DEF'
RETURN = 'RETURN'
READ = 'READ'
PRINT = 'PRINT'
IF = 'IF'
ELIF = 'ELIF'
ELSE = 'ELSE'
WHILE = 'WHILE'
BREAK = 'BREAK'
CONTINUE = 'CONTINUE'
NOT = 'NOT'
AND = 'AND'
OR = 'OR'
XOR = 'XOR'
PASS = 'PASS'

# Literals
LITERAL = 'LITERAL'
ID = 'ID'

# Operators
PLUS = 'PLUS'
MINUS = 'MINUS'
MUL = 'MUL'
INT_DIV = 'INT-DIV'
REAL_DIV = 'REAL-DIV'
MOD = 'MOD'
GT = 'GT'
GTE = 'GTE'
LT = 'LT'
LTE = 'LTE'
EQ = 'EQ'
NEQ = 'NEQ'
CAST = 'CAST'
ASSIGN = 'ASSIGN'
CAST_ASSIGN = 'CAST-ASSIGN'

# Delimiters
LPAREN = 'LPAREN'
RPAREN = 'RPAREN'
COLON = 'COLON'
ARROW = 'ARROW'
COMMA = 'COMMA'

# Special tokens
INDENT = 'INDENT'
DEDENT = 'DEDENT'
EOF = 'EOF'

KEYWORDS = {
    'program': PROGRAM,
    'var': VAR,
    'def': DEF,
    'return': RETURN,
    'read': READ,
    'print': PRINT,
    'if': IF,
    'elif': ELIF,
    'else': ELSE,
    'while': WHILE,
    'break': BREAK,
    'continue': CONTINUE,
    'not': NOT,
    'and': AND,
    'or': OR,
    'xor': XOR,
    'pass': PASS,
}

ONE_CHAR_SYMBOLS = {
    '+': PLUS,
    '-': MINUS,
    '*': MUL,
    '/': REAL_DIV,
    '%': MOD,
    '>': GT,
    '<': LT,
    '=': EQ,
    '(': LPAREN,
    ')': RPAREN,
    '~': CAST,
    ':': COLON,
    ',': COMMA,
}

TWO_CHAR_SYMBOLS = {
    '//': INT_DIV,
    ':=': ASSIGN,
    '~=': CAST_ASSIGN,
    '->': ARROW,
    '>=': GTE,
    '<=': LTE,
    '!=': NEQ,
}

STRING_QUOTE = "'"
STRING_ESCAPE = '\\'
COMMENT_START = '#'
