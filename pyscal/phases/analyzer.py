from objects.errors import PyscalSemanticError
from scope import Scope, FuncSymbol, TypeSymbol, VarSymbol
from objects.tokens import *
import objects.ast as ast
import operations


def analyze(ast):
    Analyzer().visit(ast)


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.current_scope = Scope()

    def error(self, message, token):
        raise PyscalSemanticError(message, token.ctx if token else None)

    def visit_Program(self, node):
        self.visit_FuncDef(node)
        self.visit_FuncBody(node)

    def visit_FuncDef(self, node):
        if self.current_scope.lookup(node.id, current_scope_only=True):
            self.error(f'duplicate identifier {node.id}', node.token)

        if isinstance(node, ast.Program):
            ret_type = self.get_type(node.ret_type, default='int')
            if ret_type != 'int':
                self.error('invalid return type for program (must be int)', node.token)
        else:
            ret_type = self.get_type(node.ret_type)

        symbol = FuncSymbol(node.id, ret_type, node.params, node.body)
        self.current_scope.insert(symbol)

    def get_type(self, type_node, default='any'):
        return type_node and self.visit(type_node) or default

    def visit_FuncBody(self, node):
        func_symbol = self.current_scope.lookup(node.id)

        self.current_scope = Scope(self.current_scope, ret_type=func_symbol.ret_type)
        for param in node.params:
            self.visit(param)

        self.visit(node.body, create_scope=False)

        self.current_scope = self.current_scope.enclosing_scope

    def visit_Block(self, node, create_scope=True):
        if create_scope:
            self.current_scope = Scope(self.current_scope)

        for func_def in node.functions:
            self.visit(func_def)

        for func_def in node.functions:
            self.visit_FuncBody(func_def)

        for stmt in node.statements:
            self.visit(stmt)

        if create_scope:
            self.current_scope = self.current_scope.enclosing_scope

    def visit_UnaryOp(self, node):
        expr_type = self.visit(node.expr)
        return operations.get_un_op_type(node.op, expr_type, node.token.ctx)

    def visit_BinaryOp(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        return operations.get_bin_op_type(node.op, left_type, right_type, node.token.ctx)

    def visit_Assignment(self, node):
        var_type = self.visit_Var(node.left)
        expr_type = self.visit(node.right)
        return operations.get_assignment_type(node.op, var_type, expr_type, 'any', node.token.ctx)

    def visit_Var(self, node):
        symbol = self.current_scope.lookup(node.id)
        if not isinstance(symbol, VarSymbol):
            self.error(f'variable {node.id} not declared', node.token)

        return symbol.decl_type

    def visit_Type(self, node):
        symbol = self.current_scope.lookup(node.id)
        if not isinstance(symbol, TypeSymbol):
            self.error(f'unknown type {node.id}', node.token)
        return symbol.id

    def visit_Literal(self, node):
        return node.value_type

    def visit_VarDecl(self, node):
        type_name = self.get_type(node.type)
        var_name = node.var.id

        if type_name == 'void':
            self.error('can not declare variable as void', node.type)

        if self.current_scope.lookup(var_name, current_scope_only=True):
            self.error(f'duplicate identifier {var_name}', node.token)

        var_symbol = VarSymbol(var_name, type_name)
        self.current_scope.insert(var_symbol)
        return var_symbol

    def visit_FuncCall(self, node):
        symbol = self.current_scope.lookup(node.id)
        if not isinstance(symbol, FuncSymbol):
            self.error(f'function {node.id} not declared', node.token)

        param_cnt = len(symbol.params)
        arg_cnt = len(node.args)
        if param_cnt != arg_cnt:
            self.error(f'function {symbol.id} requires {param_cnt} argument(s), but {arg_cnt} given', node.token)

        for param, arg in zip(symbol.params, node.args):
            arg_type = self.visit(arg)
            operations.get_assignment_type(ASSIGN, self.get_type(param.type), arg_type, 'any', ctx=arg.token.ctx)

        return symbol.ret_type

    def visit_IfStmt(self, node):
        while node:
            if node.expr:
                self.visit(node.expr)
            self.visit(node.body)
            node = node.next

    def visit_WhileStmt(self, node):
        self.visit(node.expr)
        self.current_scope = Scope(self.current_scope, is_loop=True)
        self.visit(node.body, create_scope=False)
        self.current_scope = self.current_scope.enclosing_scope

    def visit_SpecialStmt(self, node):
        if node.type in (BREAK, CONTINUE):
            if not self.current_scope.inside_loop:
                self.error(f'{node.type} outside a loop', node.token)
        elif node.type == RETURN:
            if node.args:
                arg_type = self.visit(node.args[0])
            else:
                arg_type = 'void'
            operations.get_assignment_type(ASSIGN, self.current_scope.ret_type, arg_type, 'any', ctx=node.token.ctx)
        else:
            for arg in node.args:
                self.visit(arg)
