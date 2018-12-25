from objects.errors import PyscalSyntaxError
from objects.ast import *
from objects.tokens import *


def parse(tokens):
    return Parser(tokens).program()


class Parser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = next(self.tokens)
        self.last_token = None

    """Helpers"""

    def error(self, message):
        token = self.last_token or self.current_token
        raise PyscalSyntaxError(message, token.ctx)

    def try_eat(self, *token_types):
        if self.current_token.type in token_types:
            self.last_token = self.current_token
            self.current_token = next(self.tokens, None)
            return True
        return False

    def eat_token(self, *token_types):
        if self.try_eat(*token_types):
            return self.last_token
        else:
            self.error(f'expected one of: {", ".join(token_types)}')

    def bin_op_expr(self, op_types, arg_scanner, factory=BinaryOp):
        node = arg_scanner()
        while self.try_eat(*op_types):
            node = factory(node, self.last_token, arg_scanner())
        return node

    """Program"""

    def program(self):
        """
        program ::= PROGRAM func-signature COLON block
        """
        self.eat_token(PROGRAM)
        name, params, ret_type = self.func_signature()
        self.eat_token(COLON)
        body = self.block()
        self.eat_token(EOF)
        return Program(name, ret_type, params, body)

    """Statements"""

    def statement(self):
        """
        statement ::= block
                    | var-statement | assignment
                    | func-definition | func-call
                    | if-statement | while-statement
                    | special-statement
                    | PASS
        """
        token = self.current_token

        if token.type == INDENT:
            return self.block()
        if token.type == VAR:
            return self.var_statement()
        if token.type == DEF:
            return self.func_definition()
        if token.type == ID:
            id = self.eat_token(ID)
            if self.current_token.type == LPAREN:
                return self.func_call(id)
            else:
                return self.assignment(Var(id))
        if token.type == PRINT:
            return self.print_statement()
        if token.type == READ:
            return self.read_statement()
        if token.type == IF:
            return self.if_statement()
        if token.type == WHILE:
            return self.while_statement()
        if token.type == RETURN:
            node = SpecialStmt(self.eat_token(RETURN))
            if not self.try_eat(PASS):
                node.args.append(self.expr())
            return node
        if self.try_eat(BREAK, CONTINUE):
            return SpecialStmt(self.last_token)
        if self.try_eat(PASS):
            return []

        self.error('statement expected')

    def block(self):
        """
        block ::= INDENT {statement} DEDENT
        """
        node = Block(self.eat_token(INDENT))
        while not self.try_eat(DEDENT):
            stmt = self.statement()
            if type(stmt) is list:
                node.statements.extend(stmt)
            elif isinstance(stmt, FuncDef):
                node.functions.append(stmt)
            else:
                node.statements.append(stmt)
        return node

    def if_statement(self):
        """
        if-statement ::= IF expr COLON block
                         {ELIF expr COLON block}
                         [ELSE expr COLON block]
        """
        token = self.eat_token(IF)
        expr = self.expr()
        self.eat_token(COLON)
        body = self.block()
        first_node = node = IfStmt(token, expr, body)

        while self.try_eat(ELIF):
            token = self.last_token
            expr = self.expr()
            self.eat_token(COLON)
            body = self.block()
            node.next = IfStmt(token, expr, body)
            node = node.next

        if self.try_eat(ELSE):
            token = self.last_token
            self.eat_token(COLON)
            body = self.block()
            node.next = IfStmt(token, None, body)

        return first_node

    def while_statement(self):
        """
        while-statement ::= WHILE expr COLON block
        """
        token = self.eat_token(WHILE)
        expr = self.expr()
        self.eat_token(COLON)
        body = self.block()
        return WhileStmt(token, expr, body)

    def print_statement(self):
        """
        print-statement ::= PRINT expr {COMMA expr}
        """
        node = SpecialStmt(self.eat_token(PRINT))
        node.args.append(self.expr())
        while self.try_eat(COMMA):
            node.args.append(self.expr())
        return node

    def read_statement(self):
        """
        read-statement ::= READ variable {COMMA variable}
        """
        node = SpecialStmt(self.eat_token(READ))
        node.args.append(Var(self.eat_token(ID)))
        while self.try_eat(COMMA):
            node.args.append(Var(self.eat_token(ID)))
        return node

    """Expressions"""

    def expr(self):
        """
        expr ::= rel-expr {(AND | OR | XOR) rel-expr}
        """
        return self.bin_op_expr([AND, OR, XOR], self.rel_expr)

    def rel_expr(self):
        """
        rel-expr ::= [NOT] arith-expr {(LT | LTE | GT | GTE | EQ | NEQ) arith-expr}
        """
        if self.try_eat(NOT):
            token = self.last_token
            expr = self.bin_op_expr([LT, LTE, GT, GTE, EQ, NEQ], self.arith_expr)
            return UnaryOp(token, expr)
        return self.bin_op_expr([LT, LTE, GT, GTE, EQ, NEQ], self.arith_expr)

    def arith_expr(self):
        """
        arith-expr ::= term {(PLUS | MINUS) term}
        """
        return self.bin_op_expr([PLUS, MINUS], self.term)

    def term(self):
        """
        term ::= factor {(MUL | INT-DIV | REAL-DIV | MOD) factor}
        """
        return self.bin_op_expr([MUL, INT_DIV, REAL_DIV, MOD], self.factor)

    def factor(self):
        """
        factor ::= PLUS factor | MINUS factor | CAST factor
                 | LPAREN expr RPAREN
                 | literal
                 | variable
                 | func-call
        """
        if self.try_eat(PLUS, MINUS, CAST):
            node = UnaryOp(self.last_token, self.factor())
        elif self.try_eat(LPAREN):
            node = self.expr()
            self.eat_token(RPAREN)
        elif self.try_eat(LITERAL):
            node = Literal(self.last_token)
        else:
            self.eat_token(ID)
            if self.current_token.type == LPAREN:
                node = self.func_call(self.last_token)
            else:
                node = Var(self.last_token)

        return node

    """Variables"""

    def var_statement(self):
        """
        var-statement ::= VAR var-decl-or-defn {COMMA var-decl-or-defn} [COLON type]
        """
        self.eat_token(VAR)
        result = self.var_decl_or_defn()

        while self.try_eat(COMMA):
            result.extend(self.var_decl_or_defn())

        if self.try_eat(COLON):
            type = Type(self.eat_token(ID))
            for decl in result:
                if isinstance(decl, VarDecl):
                    decl.type = type

        return result

    def var_decl_or_defn(self):
        """
        var-decl-or-defn ::= variable | assignment
        """
        var = Var(self.eat_token(ID))
        result = [VarDecl(var)]
        if self.try_eat(ASSIGN, CAST_ASSIGN):
            result.append(Assignment(var, self.last_token, self.expr()))
        return result

    def assignment(self, left):
        """
        assignment ::= variable (ASSIGN | CAST-ASSIGN) expr
        """
        op = self.eat_token(ASSIGN, CAST_ASSIGN)
        right = self.expr()
        return Assignment(left, op, right)

    """Functions"""

    def func_definition(self):
        """
        func-definition ::= DEF func-signature COLON block
        """
        self.eat_token(DEF)
        name, params, ret_type = self.func_signature()
        self.eat_token(COLON)
        body = self.block()
        return FuncDef(name, ret_type, params, body)

    def func_signature(self):
        """
        func-signature ::= ID LPAREN [formal-parameters] RPAREN [ARROW type]
        """
        name = self.eat_token(ID)
        self.eat_token(LPAREN)
        params = self.formal_parameters()
        self.eat_token(RPAREN)

        ret_type = None
        if self.try_eat(ARROW):
            ret_type = Type(self.eat_token(ID))

        return name, params, ret_type

    def formal_parameters(self):
        """
        formal-parameters ::= param-list {COMMA param-list}
        """
        if self.current_token.type == RPAREN:
            return []

        params = self.param_list()
        while self.try_eat(COMMA):
            params.extend(self.param_list())

        return params

    def param_list(self):
        """
        param-list ::= variable {COMMA variable} [COLON type]
        """
        var = Var(self.eat_token(ID))
        result = [VarDecl(var)]
        while self.try_eat(COMMA):
            var = Var(self.eat_token(ID))
            result.append(VarDecl(var))

        if self.try_eat(COLON):
            type = Type(self.eat_token(ID))
            for var in result:
                var.type = type

        return result

    def func_call(self, name):
        """
        func-call ::= ID LPAREN [expr {COMMA expr}] RPAREN
        """
        self.eat_token(LPAREN)
        args = []
        while not self.try_eat(RPAREN):
            args.append(self.expr())
            if self.try_eat(RPAREN):
                break
            self.eat_token(COMMA)
        return FuncCall(name, args)
