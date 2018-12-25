import pprint


class NodeVisitor(object):
    def visit(self, node, **kwargs):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, **kwargs)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class ASTNode(object):
    def __init__(self, token):
        self.token = token

    def __repr__(self):
        return f'{type(self).__name__}:{self.token}'

    def get_children(self):
        return []

    def get_list_repr(self):
        children = filter(None, self.get_children())
        return [self] + [child.get_list_repr() for child in children]

    def pretty_print(self):
        return pprint.pformat(self.get_list_repr())


class FuncDef(ASTNode):
    def __init__(self, token, ret_type, params, body):
        super().__init__(token)
        self.id = token.id
        self.ret_type = ret_type
        self.params = params
        self.body = body

    def get_children(self):
        return [self.ret_type] + self.params + [self.body]


class Program(FuncDef):
    def __init__(self, token, ret_type, params, body):
        super().__init__(token, ret_type, params, body)


class Block(ASTNode):
    def __init__(self, token):
        super().__init__(token)
        self.statements = []
        self.functions = []

    def get_children(self):
        return self.functions + self.statements


class UnaryOp(ASTNode):
    def __init__(self, token, expr):
        super().__init__(token)
        self.op = token.type
        self.expr = expr

    def get_children(self):
        return [self.expr]


class BinaryOp(ASTNode):
    def __init__(self, left, token, right):
        super().__init__(token)
        self.left = left
        self.op = token.type
        self.right = right

    def get_children(self):
        return [self.left, self.right]


class Assignment(BinaryOp):
    def __init__(self, left, token, right):
        super().__init__(left, token, right)


class Var(ASTNode):
    def __init__(self, token):
        super().__init__(token)
        self.id = token.id


class Type(ASTNode):
    def __init__(self, token):
        super().__init__(token)
        self.id = token.id


class Literal(ASTNode):
    def __init__(self, token):
        super().__init__(token)
        self.value = token.value
        self.value_type = token.value_type


class VarDecl(ASTNode):
    def __init__(self, var):
        super().__init__(var.token)
        self.var = var
        self.type = None

    def get_children(self):
        return [self.var, self.type]


class FuncCall(ASTNode):
    def __init__(self, token, args):
        super().__init__(token)
        self.id = token.id
        self.args = args

    def get_children(self):
        return self.args


class IfStmt(ASTNode):
    def __init__(self, token, expr, body):
        super().__init__(token)
        self.expr = expr
        self.body = body
        self.next = None

    def get_children(self):
        return [self.expr, self.body, self.next]


class WhileStmt(ASTNode):
    def __init__(self, token, expr, body):
        super().__init__(token)
        self.expr = expr
        self.body = body

    def get_children(self):
        return [self.expr, self.body]


class SpecialStmt(ASTNode):
    def __init__(self, token):
        super().__init__(token)
        self.type = token.type
        self.args = []

    def get_children(self):
        return self.args
