import ast

from objects.errors import PyscalSyntaxError
from objects.tokens import *


class Tokenizer(object):
    def __init__(self, lines):
        self.lines = lines
        self.current_line = None
        self.current_char = None

        self.eof = False
        self.pos = 0
        self.line_no = 0

        self.line_start = True
        self.indent_level = 0
        self.indent_stack = [0]
        self.bad_indent = False

    def error(self, message):
        raise PyscalSyntaxError(message, self.get_ctx())

    def get_ctx(self):
        return Context(self.current_line or '', self.line_no, self.pos + 1)

    def has_next_char(self):
        return self.pos + 1 < len(self.current_line)

    def next_char(self):
        if self.has_next_char():
            self.pos += 1
            self.indent_level += 1
            self.current_char = self.current_line[self.pos]
        else:
            self.current_char = None  # signal end of line

    def next_line(self):
        next_line = next(self.lines, None)
        if next_line:
            self.current_line = next_line.strip('\n')
            self.line_no += 1
            self.pos = self.indent_level = -1
            self.next_char()
        else:
            self.indent_level = 0
            self.eof = True

        self.line_start = True
        self.bad_indent = False

    def check_indent(self):
        """"""
        if self.bad_indent:
            self.error('invalid indentation (only space characters are allowed)')

        if self.indent_level > self.indent_stack[-1]:
            self.indent_stack.append(self.indent_level)
            return Token(INDENT)

        if self.indent_level < self.indent_stack[-1]:
            self.indent_stack.pop()
            if self.indent_level > self.indent_stack[-1]:
                self.error('unexpected indent')
            return Token(DEDENT)

        return None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            if self.line_start and self.current_char != ' ':
                self.bad_indent = True
            self.next_char()

    def skip_comment(self):
        while self.current_char is not None:
            self.next_char()

    def read_id(self):
        result = ''
        while self.current_char is not None and (
                self.current_char.isalnum() or
                self.current_char == '_'
        ):
            result += self.current_char
            self.next_char()

        if result in KEYWORDS:
            return Token(KEYWORDS[result])
        else:
            return IDToken(result)

    def read_number(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.next_char()

        if self.current_char == '.':
            result += self.current_char
            self.next_char()

            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.next_char()

            token = LiteralToken('real', float(result))
        else:
            token = LiteralToken('int', int(result))

        if self.current_char is not None and self.current_char.isalpha():
            self.error('invalid number literal')

        return token

    def read_string(self):
        result = ''
        self.next_char()  # consume opening quote
        while self.current_char != STRING_QUOTE:
            if self.current_char is None:
                self.error('string literal not closed')

            if self.current_char == STRING_ESCAPE and self.has_next_char():
                result += self.current_char
                self.next_char()

            result += self.current_char
            self.next_char()

        self.next_char()  # consume closing quote
        result = ast.literal_eval(STRING_QUOTE + result + STRING_QUOTE)
        return LiteralToken('string', result)

    def read_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while not self.eof:
            if self.current_char is None:
                self.next_line()
                continue
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            if self.current_char == COMMENT_START:
                self.skip_comment()
                continue
            break

        if self.line_start:
            token = self.check_indent()
            if token:
                return token

        if self.eof:
            return Token(EOF)

        self.line_start = False

        if self.current_char.isalpha() or self.current_char == '_':
            return self.read_id()

        if self.current_char.isdigit():
            return self.read_number()

        if self.current_char == STRING_QUOTE:
            return self.read_string()

        if self.has_next_char():
            sym = self.current_char + self.current_line[self.pos + 1]
            if sym in TWO_CHAR_SYMBOLS:
                self.next_char()
                self.next_char()
                return Token(TWO_CHAR_SYMBOLS[sym])

        sym = self.current_char
        if sym in ONE_CHAR_SYMBOLS:
            self.next_char()
            return Token(ONE_CHAR_SYMBOLS[sym])

        self.error('invalid character: ' + self.current_char)

    def next_token(self):
        token = self.read_token()
        token.ctx = self.get_ctx()
        return token


def tokenize(text):
    tokenizer = Tokenizer(text)
    while True:
        token = tokenizer.next_token()
        yield token
        if token.type == EOF:
            break
