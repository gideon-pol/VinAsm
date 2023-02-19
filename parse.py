import ply.yacc as yacc
from lexer import tokens
from parse_types import *

def p_program(p):
    '''program : declarations'''
    p[0] = Program(p[1])

def p_declarations(p):
    '''declarations : declaration
                    | declarations declaration'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_declaration(p):
    '''declaration : instr
                   | label'''
    p[0] = p[1]

def p_register(p):
    '''value : REGISTER'''
    p[0] = Register(p[1][1:]).at(p)

def p_intconst(p):
    '''value : INTCONST'''
    p[0] = IntConstant(int(p[1])).at(p)

def p_hexconst(p):
    '''value : HEXCONST'''
    p[0] = IntConstant(int(p[1], 16)).at(p)

def p_floatconst(p):
    '''value : FLOATCONST'''
    p[0] = FloatConstant(float(p[1])).at(p)

def p_label_def(p):
    '''label : DOLLAR ID COLON newline'''
    p[0] = LabelDecl(p[2]).at(p)

def p_label(p):
    '''value : DOLLAR ID'''
    p[0] = Label(p[2]).at(p)

def p_args(p):
    '''args : value
            | args COMMA value'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_instruction(p):
    '''instr : OPCODE newline
             | OPCODE args newline'''
    args = p[2] if p[2] != None else []
    p[0] = Instruction(p[1], args).at(p)

def p_newline(p):
    '''newline : NEWLINE
               | newline NEWLINE'''
    pass

def p_error(t):
    if t is None:
        raise EOFError("Unexpected end of file")

    raise LocationError(token_loc(t), 'Syntax error at \'%s\'' % t.value.split('\n')[0])

def create_parser(src):
    parser = yacc.yacc()
    parser.input = src
    
    return parser

if __name__ == '__main__':
    raise Exception('This is a module, not a program')