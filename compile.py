from lexer import create_lexer
from parse import create_parser
from microcode import resolve_microcode
from codegen import Generator
from typecheck import typecheck
from parse_types import CompilationError


def compile(filename, output):
    with open(filename, 'r') as f:
        src = f.read()

    lexer = create_lexer(filename)
    parser = create_parser(src)

    try:
        tree = parser.parse(src, lexer=lexer, debug=False)
        print("Constructed AST:")
        print(tree)

        typecheck(tree)
        tree = resolve_microcode(tree)
        print("Constructed AST after microcode replacement:")
        print(tree)

        gen = Generator(tree)
        gen.generate()
        gen.output(filename.split('.')[0] + '.4vin')

    except CompilationError as e:
        print(e)
    except EOFError as e:
        print(e)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 compile.py <filename>")
        sys.exit(1)
    compile(sys.argv[1], "")