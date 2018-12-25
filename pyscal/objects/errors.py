class PyscalException(Exception):
    def __init__(self, message, ctx):
        super().__init__(message)
        self.message = message
        self.ctx = ctx

    def __repr__(self):
        str = ''
        if self.ctx:
            str += f'Line {self.ctx.line_no}, column {self.ctx.pos}:\n'
            str += self.ctx.line + '\n'
            str += ' ' * (self.ctx.pos - 1) + '^\n'
        str += self.message
        return str


class PyscalSyntaxError(PyscalException):
    def __init__(self, message, ctx):
        message = 'SyntaxError: ' + message
        super().__init__(message, ctx)


class PyscalSemanticError(PyscalException):
    def __init__(self, message, ctx):
        message = 'SemanticError: ' + message
        super().__init__(message, ctx)


class PyscalTypeError(PyscalSemanticError):
    def __init__(self, message, ctx=None):
        message = 'TypeError: ' + message
        super().__init__(message, ctx)
