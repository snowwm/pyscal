from helpers import ValueWrapper


class Scope(object):
    def __init__(self, enclosing_scope=None, is_loop=None, ret_type=None):
        self.symbols = {}
        self.enclosing_scope = enclosing_scope

        if is_loop is not None:
            self.inside_loop = is_loop
        elif enclosing_scope is not None:
            self.inside_loop = enclosing_scope.inside_loop
        else:
            self.inside_loop = False

        if ret_type is not None:
            self.ret_type = ret_type
        elif enclosing_scope is not None:
            self.ret_type = enclosing_scope.ret_type
        else:
            self.ret_type = 'any'

        if enclosing_scope is None:  # global scope
            self.init_builtins()

    def init_builtins(self):
        self.insert(TypeSymbol.INT)
        self.insert(TypeSymbol.REAL)
        self.insert(TypeSymbol.STRING)
        self.insert(TypeSymbol.ANY)
        self.insert(TypeSymbol.VOID)

    def insert(self, symbol):
        self.symbols[symbol.id] = symbol

    def lookup(self, id, current_scope_only=False):
        # 'symbol' is either an instance of the Symbol class or None
        symbol = self.symbols.get(id)

        if symbol is not None:
            return symbol

        if current_scope_only:
            return None

        # recursively go up the chain and lookup the name
        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(id)


class Symbol(object):
    def __init__(self, id):
        self.id = id


class TypeSymbol(Symbol):
    def __init__(self, id):
        super().__init__(id)


TypeSymbol.INT = TypeSymbol('int')
TypeSymbol.REAL = TypeSymbol('real')
TypeSymbol.STRING = TypeSymbol('string')
TypeSymbol.ANY = TypeSymbol('any')
TypeSymbol.VOID = TypeSymbol('void')


class VarSymbol(Symbol):
    def __init__(self, id, decl_type):
        super().__init__(id)
        self.decl_type = decl_type

        type = 'int' if decl_type == 'any' else decl_type
        self.value = ValueWrapper(type)


class FuncSymbol(Symbol):
    def __init__(self, id, ret_type, params, body):
        super().__init__(id)
        self.ret_type = ret_type
        self.params = params
        self.body = body

    def src(self):
        return 'Not implemented yet'
