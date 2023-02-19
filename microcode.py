from parse_types import *
from parse import *
from lexer import *

def compile_microcode(microcode):
    lexer = create_lexer("")
    parser = create_parser(microcode)
    return parser.parse(microcode, lexer=lexer)

def resolve_microcode(node: Node):
    if node.type == None:
        raise TypeError(("", 0, 0), 'Got a node with type None')

    if node.type == 'program':
        resolved_declarations = []
        for d in node.declarations:
            resolved_declarations.extend(resolve_microcode(d))

        node.declarations = resolved_declarations
        return node

    elif node.type == 'label_decl':
        return [node]
    elif node.type == 'instr':
        config = node.get_config()

        if hasattr(config, 'MICROCODE'):
            microcode = config.MICROCODE
            
            for i, v in enumerate(node.children):
                microcode = microcode.replace("%" + str(i), str(v))

            try:
                return compile_microcode(microcode).declarations
            except CompilationError as e:
                print(e)
                exit(0)
        else:
            return [node]