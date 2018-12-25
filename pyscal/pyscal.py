#!/usr/bin/env python3

import argparse
import sys
import pickle

from objects.errors import PyscalException
from phases import interpreter, analyzer, parser, tokenizer
from frontend import Frontend


def main():
    args = parse_args()
    phase = 'preparation'
    tokens = ast = None

    need_analyze = args.analyze or args.save_ast or args.interpret and not args.load_ast
    need_parse = args.parse or need_analyze and not args.load_ast
    need_tokenize = args.tokenize or need_parse and not args.load_ast

    try:
        if need_tokenize:
            file = open(args.input_file, 'r')

            phase = 'lexical analysis'

            with file:
                tokens = [x for x in tokenizer.tokenize(file)]  # buffer the iter

            if args.tokenize:
                print('=== TOKENS ===')
                for x in tokens:
                    print(x)
                print('==============')
                print()

        if need_parse:
            phase = 'syntactic analysis'
            ast = parser.parse(iter(tokens))

            if args.parse:
                print('=== AST ===')
                print(ast.pretty_print())
                print('===========')
                print()

        if need_analyze:
            phase = 'semantic analysis'
            analyzer.analyze(ast)

            if args.analyze:
                print('=== SEMANTICS ===')
                print('No errors found.')
                print('=================')
                print()

        if args.load_ast:
            file = open(args.input_file, 'rb')
            with file:
                ast = pickle.load(file)

        if args.save_ast:
            file = open(args.save_ast, 'wb')
            with file:
                pickle.dump(ast, file)

        if args.interpret:
            phase = 'runtime'
            print('=== BEGIN INTERPRETATION ===')
            frontend = Frontend(args.program_args, debug_mode=args.debug)
            exit_code = interpreter.interpret(ast, frontend)
            sys.exit(exit_code)

    except PyscalException as e:
        print_error(phase, e)
    except RecursionError as e:
        print_error(phase, e)
    except OSError as e:
        print_error(phase, e)


def print_error(phase, message):
    print()
    print(f'Error during {phase}:', file=sys.stderr)
    print(repr(message), file=sys.stderr)


def parse_args():
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('-t', '--tokenize', action='store_true')
    arg_parser.add_argument('-p', '--parse', action='store_true')
    arg_parser.add_argument('-a', '--analyze', action='store_true')
    arg_parser.add_argument('-i', '--interpret', action='store_true')
    arg_parser.add_argument('-s', '--save-ast', metavar='output_file')
    arg_parser.add_argument('-l', '--load-ast', action='store_true')
    arg_parser.add_argument('-d', '--debug', action='store_true')

    arg_parser.add_argument('input_file')
    arg_parser.add_argument('program_args', nargs=argparse.REMAINDER)

    args = arg_parser.parse_args()

    if args.debug:
        args.interpret = True

    if args.tokenize or args.parse or args.analyze or args.save_ast:
        if args.load_ast:
            arg_parser.error('options -tpas are not compatible with -l')
    else:
        args.interpret = True

    return args


if __name__ == '__main__':
    main()
