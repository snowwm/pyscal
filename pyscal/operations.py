from objects.errors import PyscalTypeError
from objects.tokens import *
from scope import ValueWrapper

VALID_TYPES = {
    AND: ('int', 'real', 'string'),
    OR: ('int', 'real', 'string'),
    XOR: ('int', 'real', 'string'),
    LT: ('int', 'real', 'string'),
    LTE: ('int', 'real', 'string'),
    GT: ('int', 'real', 'string'),
    GTE: ('int', 'real', 'string'),
    EQ: ('int', 'real', 'string'),
    NEQ: ('int', 'real', 'string'),
    PLUS: ('int', 'real', 'string'),
    MINUS: ('int', 'real'),
    MUL: ('int', 'real'),
    INT_DIV: ('int', 'real'),
    REAL_DIV: ('int', 'real'),
    MOD: ('int', 'real'),
}


def is_implicitly_convertible(type1, type2):
    if type1 == type2:
        return True
    if type1 in ('cast', 'any'):
        return True
    if type1 == 'void':
        return False
    if type2 == 'any':
        return True
    if (type1, type2) == ('int', 'real'):
        return True
    return False


def cast(value, type, ctx=None):
    try:
        if type == 'int':
            return int(value)
        elif type == 'real':
            return float(value)
        elif type == 'string':
            return str(value)
        return value
    except ValueError:
        raise PyscalTypeError(f'cannot convert {repr(value)} to {type}', ctx)


def get_assignment_type(op, var_type, expr_type, expr_real_type, ctx=None):
    if op == CAST_ASSIGN:
        expr_type = 'cast'

    if not is_implicitly_convertible(expr_type, var_type):
        raise PyscalTypeError(f'cannot assign {expr_type} to {var_type}', ctx)

    return var_type if var_type != 'any' else expr_real_type


def get_assignment_value(op, var_type, expr, ctx=None):
    type = get_assignment_type(op, var_type, expr.type, expr.real_type, ctx=ctx)
    return ValueWrapper(type, cast(expr.value, type, ctx=ctx))


def get_un_op_type(op, type, ctx=None):
    if op == CAST:
        return 'cast'

    if op in (PLUS, MINUS):
        if type == 'cast':
            return 'int'
        if type in ('int', 'real', 'any'):
            return type

    raise PyscalTypeError(f'invalid operand type {type} for {op}', ctx)


def get_un_op_value(op, arg, ctx=None):
    type = get_un_op_type(op, arg.type, ctx=ctx)
    val = cast(arg.value, type, ctx=ctx)

    if op == MINUS:
        val = -val
    elif op == NOT:
        val = not val

    return ValueWrapper(type, val, real_type=arg.real_type)


def get_bin_op_type(op, type1, type2, ctx=None):
    for type in ('int', 'real', 'string'):
        if (
            type in VALID_TYPES[op]
            and is_implicitly_convertible(type1, type)
            and is_implicitly_convertible(type2, type)
        ):
            if type1 == 'any' or type2 == 'any':
                return 'any'
            return type

    raise PyscalTypeError(f'invalid operand types {type1} and {type2} for {op}', ctx)


def get_bin_op_value(op, arg1, arg2, ctx=None):
    type = get_bin_op_type(op, arg1.type, arg2.type, ctx=ctx)
    val1 = cast(arg1.value, type, ctx=ctx)
    val2 = cast(arg2.value, type, ctx=ctx)
    result = None

    if op == AND:
        result = bool(val1) and bool(val2)
    elif op == OR:
        result = bool(val1) or bool(val2)
    elif op == XOR:
        result = bool(val1) ^ bool(val2)
    elif op == LT:
        result = val1 < val2
    elif op == LTE:
        result = val1 <= val2
    elif op == GT:
        result = val1 > val2
    elif op == GTE:
        result = val1 >= val2
    elif op == EQ:
        result = val1 == val2
    elif op == NEQ:
        result = val1 != val2
    elif op == PLUS:
        result = val1 + val2
    elif op == MINUS:
        result = val1 - val2
    elif op == MUL:
        result = val1 * val2
    elif op == INT_DIV:
        result = val1 // val2
    elif op == REAL_DIV:
        result = val1 / val2
    elif op == MOD:
        result = val1 % val2

    if op in (PLUS, MINUS, MUL, INT_DIV, REAL_DIV, MOD):
        return ValueWrapper(type, result)
    else:
        return ValueWrapper('int', result)
