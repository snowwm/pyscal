import sys

from scope import ValueWrapper, VarSymbol
from helpers import input_word

COMMANDS = {
    'help': 'help [cmd] -- print help',
    'continue': 'continue -- run until a breakpoint is reached',
    'step': 'step -- step to the next line or into a function',
    'next': 'next -- step to the next line',
    'return': 'return -- run until a function returns',
    'list': 'list -- list current function\'s source code',
    'print': 'print [var] -- print a variable\'s  value',
    'break': 'break [line] -- set a breakpoint on line',
    'delete': 'delete [line] -- remove breakpoint from line',
    'info': 'info -- show all breakpoints',
    'exit': 'exit -- finish this debug session',
}


class Frontend:
    def __init__(self, args, debug_mode=False):
        self.args = args
        self.debug_mode = debug_mode
        self.breakpoints = {}

        self.cmd = 'step'
        self.cmd_depth = 0
        self.cmd_line_no = None
        self.last_printed = ''

        self.stack = []
        self.current_scope = None
        self.ctx = None

    def get_args(self):
        return [ValueWrapper('string', arg) for arg in self.args]

    def print(self, wrapper):
        print(wrapper.value, end='')

    def read(self):
        return ValueWrapper('string', input_word())

    def enter_func(self, func):
        if not self.debug_mode:
            return
        self.stack.append(func)

    def leave_func(self):
        if not self.debug_mode:
            return
        self.stack.pop()

    def scope_changed(self, new_scope):
        if not self.debug_mode:
            return
        self.current_scope = new_scope

    def visit_line(self, ctx):
        if not self.debug_mode:
            return
        if not self.stack:  # not initialized yet
            return
        if not self.should_break(ctx.line_no):
            return

        self.ctx = ctx
        self.print_ctx()
        self.read_cmd()

    def should_break(self, line_no):
        if self.cmd_line_no == line_no and len(self.stack) == self.cmd_depth:
            return False

        if self.cmd == 'step':
            return True
        elif self.cmd == 'next' and len(self.stack) <= self.cmd_depth:
            return True
        elif self.cmd == 'return' and len(self.stack) < self.cmd_depth:
            return True
        elif line_no in self.breakpoints:
            return True

        return False

    def print_ctx(self):
        print(f'In function <{self.stack[-1].id}>')
        print(self.ctx)

    def read_cmd(self):
        while True:
            line = input('pyscal-dbg> ').split()
            if not line:
                continue

            cmd = line[0]
            cmds = [c for c in COMMANDS if c.startswith(cmd)]

            if not cmds:
                print('Unknown command. Type \'h\' for help')
                continue
            if len(cmds) > 1:
                print('Ambiguous command. Type \'h\' for help')
                continue
            cmd = cmds[0]

            arg = line[1] if len(line) > 1 else None

            if cmd in ('break', 'delete'):
                if arg:
                    try:
                        arg = int(arg)
                    except ValueError:
                        print('Invalid line number')
                        continue
                else:
                    arg = self.ctx.line_no

            if self.exec_command(cmd, arg):
                break

    def exec_command(self, cmd, arg):
        if cmd == 'help':
            if arg in COMMANDS:
                print(COMMANDS[arg])
            else:
                print('Available commands:')
                print(f'    {", ".join(COMMANDS.keys())}')
                print('You can type any unambiguous prefix of a command.')

        elif cmd == 'continue':
            self.cmd = self.cmd_depth = self.cmd_line_no = None
            return True

        elif cmd in ('step', 'next', 'return'):
            self.cmd = cmd
            self.cmd_depth = len(self.stack)
            self.cmd_line_no = self.ctx.line_no
            return True

        elif cmd == 'list':
            print(self.stack[-1].src())

        elif cmd == 'print':
            arg = self.last_printed = arg or self.last_printed
            symbol = self.current_scope.lookup(arg)
            if not isinstance(symbol, VarSymbol):
                print(f'No variable {repr(arg)} in current scope')
            else:
                print(f'{arg}: {symbol.value}')

        elif cmd == 'break':
            self.breakpoints[arg] = True
            print(f'Breakpoint set: {arg}')

        elif cmd == 'delete':
            self.breakpoints.pop(arg)
            print(f'Breakpoint deleted: {arg}')

        elif cmd == 'info':
            print(f'Breakpoints: {repr(list(self.breakpoints.keys()))}')

        elif cmd == 'exit':
            sys.exit(0)

        return False
