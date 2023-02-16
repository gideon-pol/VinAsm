def token_loc(token):
    return (token.lexer.filename,
            token.lineno,
            token.lexpos - token.lexer.last_newline_pos)

def loc(p):
    lexpos = p.lexpos(1) - p.lexer.last_newline_pos
    return (p.lexer.filename,
            p.lineno(1),
            1 if lexpos < 0 else lexpos)

class Node():
    def __init__(self):
        self.type = None
        self.children = []

    def at(self, p):
        self.loc = loc(p)
        return self

class CompilationError(Exception):
    def get_line(self, filename, lineno):
        with open(filename, 'r') as f:
            for i, l in enumerate(f.readlines()):
                if i == lineno - 1:
                    return l.strip()

    def format(self, msg, filename, line, lineno, pos):
        s = '%s:%d:%d %s\n     %s' % (
                filename,
                lineno,
                pos,
                msg,
                line,
            )

        s += '\n>>>>' + '-' * (pos) + '^'
        return s

class LocationError(CompilationError):
    def __init__(self, loc, msg):
        self.loc = loc
        self.msg = msg

    def __str__(self):
        (filename, lineno, lexpos_line) = self.loc
        line = self.get_line(filename, lineno)

        return self.format(self.msg, filename, line, lineno, lexpos_line)

class TypeError(LocationError):
    def __init__(self, loc, expected, got):
        self.loc = loc
        self.expected = expected
        self.got = got
        self.msg = 'Expected type \'%s\', got \'%s\'' % (self.expected, self.got)

class Program(Node):
    def __init__(self, declarations):
        super().__init__()
        self.type = 'program'
        self.declarations = declarations

    def __str__(self):
        s = ''
        for d in self.declarations:
            s += str(d) + '\n'
        return s

class LabelDecl(Node):
    def __init__(self, label):
        super().__init__()
        self.type = 'label_decl'
        self.label = label

    def __str__(self):
        return '$' + self.label + ':'

class Label(Node):
    def __init__(self, label):
        super().__init__()
        self.type = 'label'
        self.label = label

    def __str__(self):
        return '$' + self.label

class Register(Node):
    registers = {
        'RA': 0x0, 'RB': 0x1, 'RC': 0x2, 'RD': 0x3, 'RE': 0x4, 'RF': 0x5,
        'RSP': 0x6,
        'RBP': 0x7
    }

    def __init__(self, name):
        super().__init__()
        self.type = 'register'
        self.name = name

    def __str__(self):
        return '%' + self.name

    def get_code(self):
        return self.registers[self.name]

class Constant(Node):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def __str__(self):
        return str(self.value)

class IntConstant(Constant):
    def __init__(self, value):
        super().__init__(value)
        self.type = 'int24' if value <= 0xFFFFFF else 'int32'

class FloatConstant(Constant):
    def __init__(self, value):
        super().__init__(value)
        self.type = 'float'

class InstructionConfig():
    def __init__(self, opcodes, arg_num, first_val_types=None, second_val_types=None):
        self.opcodes = opcodes
        self.arg_num = arg_num
        self.first_val_types = first_val_types
        self.second_val_types = second_val_types
    
    def modify(self, mod):
        for k, v in mod.items():
            setattr(self, k, v)
        return self

class Instruction(Node):
    def __init__(self, opcode, args):
        super().__init__()
        self.type = 'instr'
        self.opcode = opcode
        self.children.extend(args)

    def __str__(self):
        s = self.opcode
        if len(self.children) > 0:
            s += ' '
        s += ', '.join([str(arg) for arg in self.children])
        return s

    """
    instrs_no_args = {
        'NOP': 0x00,
        'STOP': 0xffff,
        # 'RET': 0x46,
    }

    instrs_one_arg = {
        'JMP': 0x40, 'JE': 0x41, 'JNE': 0x42, 'JG': 0x43, 'JS': 0x44, # 'CALL': 0x45,
    }

    instrs_two_args = {
        'MOV': 0x2, 'STORE': 0x3, 'LOAD': 0x4, # 'PUSH': 0x5, 'POP': 0x6,
        'ADD': 0x10, 'SUB': 0x11, 'MUL': 0x12, 'DIV': 0x13, 'NEG': 0x14, 'SHL': 0x15, 'SHR': 0x16,
        'FADD': 0x20, 'FSUB': 0x21, 'FMUL': 0x22, 'FDIV': 0x23, 'FNEG': 0x24,
        'FTOI': 0x25, 'ITOF': 0x26,
        'AND': 0x30, 'OR': 0x31, 'NOT': 0x32,
        'CMP': 0x18, 'UCMP': 0x19, #'FCMP': 0x20,
    }"""

    configs = {
        InstructionConfig({'NOP': 0x00,'STOP': 0xff}, 0), # 'RET': 0x46
        InstructionConfig({'JMP': 0x40, 'JE': 0x41, 'JNE': 0x42, 'JG': 0x43, 'JS': 0x44}, 1, ['register', 'int24', 'label']).modify({"SKIP_FIRST_REG": True}),
        InstructionConfig({'MOV': 0x2, 'STORE': 0x3}, 2, ['register'], ['register', 'int32', 'int24', 'float', 'label']),
        InstructionConfig({'LOAD': 0x4}, 2, ['register'], ['register', 'int24']),
        InstructionConfig({'ADD': 0x10, 'SUB': 0x11, 'MUL': 0x12, 'DIV': 0x13, 'NEG': 0x14, 'SHL': 0x15, 'SHR': 0x16, 'ITOF': 0x26}, 2, ['register'], ['register', 'int32', 'int24']),
        InstructionConfig({'FADD': 0x20, 'FSUB': 0x21, 'FMUL': 0x22, 'FDIV': 0x23, 'FNEG': 0x24, 'FTOI': 0x25}, 2, ['register'], ['register', 'float']),
        InstructionConfig({'AND': 0x30, 'OR': 0x31, 'NOT': 0x32}, 2, ['register'], ['register', 'int32', 'int24']),
        InstructionConfig({'CMP': 0x18, 'UCMP': 0x19}, 2, ['register'], ['register', 'int32', 'int24']),
        InstructionConfig({'FCMP': 0x1A}, 2, ['register'], ['register', 'float']),
        InstructionConfig({'SSET': 0x80}, 2, ['register'], ['register', 'int32', 'int24']),
        InstructionConfig({'SOUT': 0x81}, 1, ['register', 'int24']).modify({"SKIP_FIRST_REG": True}),
    }

    def get_opcodes():
        l = []
        for instr in Instruction.configs:
            l.extend(list(instr.opcodes.keys()))

        return l

    def get_code(self):
        for config in Instruction.configs:
            if self.opcode in config.opcodes:
                return config.opcodes[self.opcode]
        
        raise Exception('Invalid op code: ' + self.opcode)

    def get_config(self):
        for config in Instruction.configs:
            if self.opcode in config.opcodes:
                return config
        
        raise Exception('Invalid op code: ' + self.opcode)

    def get_arg_num(opcode):
        for config in Instruction.configs:
            if opcode in config.opcodes:
                return config.arg_num
        
        raise Exception('Invalid op code: ' + opcode)