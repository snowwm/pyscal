from objects.errors import PyscalSemanticError
from helpers import ValueWrapper
from scope import Scope, FuncSymbol, VarSymbol
from objects.tokens import *
import objects.ast as ast
import operations


def interpret(ast, frontend):
    return Interpreter(frontend).visit(ast).value


class ReturnException(Exception):
    def __init__(self, value, ctx):
        self.value = value
        self.ctx = ctx


class LoopException(Exception):
    def __init__(self, type):
        self.type = type


class Interpreter(ast.NodeVisitor):
    def __init__(self, frontend):
        self.frontend = frontend
        self.current_scope = Scope()

    def enter_scope(self, **kwargs):
        self.current_scope = Scope(self.current_scope, **kwargs)
        self.frontend.scope_changed(self.current_scope)

    def leave_scope(self):
        self.current_scope = self.current_scope.enclosing_scope
        self.frontend.scope_changed(self.current_scope)

    def visit_Program(self, node):
        program = self.visit_FuncDef(node)
        args = self.frontend.get_args()

        param_cnt = len(program.params)
        arg_cnt = len(args)
        if param_cnt != arg_cnt:
            raise PyscalSemanticError(f'program {program.id} requires {param_cnt} argument(s), but {arg_cnt} given',
                                      node.token.ctx)

        return self.call(program, args, node.params, op=CAST_ASSIGN)

    def visit_FuncDef(self, node):
        if isinstance(node, ast.Program):
            ret_type = 'int'
        else:
            if node.ret_type:
                ret_type = self.visit(node.ret_type)
            else:
                ret_type = 'any'

        symbol = FuncSymbol(node.id, ret_type, node.params, node.body)

        self.current_scope.insert(symbol)
        return symbol

    def visit_Block(self, node, create_scope=True):
        if create_scope:
            self.enter_scope()

        for func_def in node.functions:
            self.visit(func_def)

        try:
            for stmt in node.statements:
                self.frontend.visit_line(stmt.token.ctx)
                self.visit(stmt)
        finally:
            if create_scope:
                self.leave_scope()

    def visit_UnaryOp(self, node):
        expr = self.visit(node.expr)
        return operations.get_un_op_value(node.op, expr, ctx=node.token.ctx)

    def visit_BinaryOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return operations.get_bin_op_value(node.op, left, right, ctx=node.token.ctx)

    def visit_Assignment(self, node):
        var = self.current_scope.lookup(node.left.id)
        expr = self.visit(node.right)
        var.value = operations.get_assignment_value(node.op, var.decl_type, expr, ctx=node.token.ctx)

    def visit_Var(self, node):
        symbol = self.current_scope.lookup(node.id)
        return symbol.value

    def visit_Type(self, node):
        return node.id

    def visit_Literal(self, node):
        return ValueWrapper(node.value_type, node.value)

    def visit_VarDecl(self, node):
        type_name = node.type and node.type.id or 'any'
        var_symbol = VarSymbol(node.var.id, type_name)
        self.current_scope.insert(var_symbol)
        return var_symbol

    def visit_FuncCall(self, node):
        symbol = self.current_scope.lookup(node.id)
        args = [self.visit(arg) for arg in node.args]
        return self.call(symbol, args, node.args)

    def call(self, func_symbol, args, arg_nodes, op=ASSIGN):
        self.enter_scope()

        for param, arg, node in zip(func_symbol.params, args, arg_nodes):
            param_symbol = self.visit(param)
            param_symbol.value = operations.get_assignment_value(op, param_symbol.decl_type, arg, ctx=node.token.ctx)

        ret_value = None
        ctx = None

        self.frontend.enter_func(func_symbol)

        try:
            self.visit(func_symbol.body, create_scope=False)
        except ReturnException as e:
            ret_value = e.value
            ctx = e.ctx
        finally:
            self.leave_scope()

        self.frontend.leave_func()

        if ret_value is None:
            ret_value = ValueWrapper(func_symbol.ret_type)
        return operations.get_assignment_value(ASSIGN, func_symbol.ret_type, ret_value, ctx=ctx)

    def visit_IfStmt(self, node):
        while node:
            if node.expr is None or self.visit(node.expr).value:
                self.visit(node.body, )
                break
            node = node.next

    def visit_WhileStmt(self, node):
        while self.visit(node.expr).value:
            try:
                self.visit(node.body, )
            except LoopException as e:
                if e.type == CONTINUE:
                    continue
                elif e.type == BREAK:
                    break
                else:
                    raise

    def visit_SpecialStmt(self, node):
        if node.type in (BREAK, CONTINUE):
            raise LoopException(node.type)
        elif node.type == RETURN:
            if node.args:
                ret_value = self.visit(node.args[0])
            else:
                ret_value = None
            raise ReturnException(ret_value, node.token.ctx)
        elif node.type == PRINT:
            for arg in node.args:
                self.frontend.print(self.visit(arg))
        elif node.type == READ:
            for arg in node.args:
                var = self.current_scope.lookup(arg.id)
                expr = self.frontend.read()
                var.value = operations.get_assignment_value(CAST_ASSIGN, var.decl_type, expr, ctx=arg.token.ctx)
