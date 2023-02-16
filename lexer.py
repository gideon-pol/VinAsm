import ply.lex as lex
from parse_types import *

states = (
    ('comment', 'exclusive'),
)

reserved = (
    #'global',
)

reserved_map = dict((word, word.upper()) for word in reserved)

instructions_map = dict((word, word.upper()) for word in Instruction.get_opcodes())

tokens = (
    'REGISTER',
    'COMMA', 'SEMICOLON', 'COLON', 'DOLLAR',
    'NEWLINE',
    'INTCONST', 'HEXCONST',
    'FLOATCONST',
    'OPCODE',
    'ID',
) + tuple(reserved_map.values())

t_COMMA = r','
t_SEMICOLON = r';'
t_COLON = r':'
t_DOLLAR = r'\$'

t_ignore = ' \t'            # ignore whitespace
t_ignore_COMMENT = r'//.*'  # single-line comment

def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'

    if t.value in instructions_map:
        #t.type = 'INST_' + str(Instruction.get_arg_num(t.value)) + '_ARGS'
        t.type = 'OPCODE'
    else:
        t.type = reserved_map.get(t.value, 'ID')
    
    return t

def t_register(t):
    r'%R[a-zA-Z]{2}|%R[a-zA-Z]{1}'
    if t.value[1:] in Register.registers:
        t.type = 'REGISTER'
        return t
    else:
        raise LocationError(token_loc(t), 'Unknown register: \'%s\'' % t.value)

def t_float(t):
    r'\d+\.\d+|\d+\.|\.\d+'
    t.type = 'FLOATCONST'
    return t

def t_num(t):
    r'0x[a-fA-F0-9]+|\d+'
    if t.value.startswith('0x'):
        t.type = 'HEXCONST'     # e.g. 0xabc123
    elif t.value.isdigit():
        t.type = 'INTCONST'     # e.g. 123
    return t

def t_ANY_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.last_newline_pos = t.lexpos + len(t.value) - 1
    t.type = 'NEWLINE'
    return t

def t_error(t):
    raise LocationError(token_loc(t), 'Unexpected token \'%s\'' % t.value.split('\n')[0])

def create_lexer(filename):
    lexer = lex.lex()
    lexer.lineno = 1
    lexer.last_newline_pos = -1
    lexer.filename = filename
    return lexer

def run_lexer(filename):
    with open(filename, 'r') as f:
        file = f.read()

    lexer = create_lexer(filename)
    lexer.input(file)

    try:
        tok = lexer.token()
        while tok:
            print(tok)
            tok = lexer.token()
        print("Lexer finished successfully")
    except CompilationError as e:
        print(e)


if __name__ == '__main__':
    # take the filename as the first argument
    import sys
    run_lexer(sys.argv[1])