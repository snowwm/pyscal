from random import random


def input_word():
    return next(WORD_GEN)


def word_gen():
    while True:
        yield from input().split()


WORD_GEN = word_gen()


class ValueWrapper(object):
    def __init__(self, type, value=None, real_type=None):
        self.type = type
        self.real_type = real_type or type

        if value is None:
            if type == 'string':
                value = ''
            elif type == 'void':
                value = random()
            else:
                value = 0

        self.value = value

    def __repr__(self):
        return f'<{self.real_type}> {repr(self.value)}'
