import struct
from parse_types import Program

USE_LITERAL = 1 << 1

def bytearray_to_hex(ba):
    return ' '.join('{:02x}'.format(x) for x in ba)

class Generator():
    def __init__(self, program: Program):
        self.program = program
        self.write_addr = 0
        self.program_bytes = []
        self.labels = {}
        self.unresolved_label_uses = []

    def resolve_labels(self):
        for addr, label in self.unresolved_label_uses:
            label_addr_bytes = self.labels[label].to_bytes(4, byteorder='big')
            self.program_bytes[addr:addr+4] = label_addr_bytes

    def write(self, bytes):
        self.program_bytes.extend(bytes)
        self.write_addr += len(bytes)
    
    def generate_label_decl(self, decl):
        self.labels[decl.label] = int(self.write_addr/4)
        print("Label " + decl.label + " at " + str(int(self.write_addr/4)))
    
    def generate_instr(self, decl):
        self.write(bytes([0 for i in range(2)]))
        opcode_bytes = decl.get_code().to_bytes(1, byteorder='big')
        self.write(opcode_bytes)
        print(decl.opcode + ": " + bytearray_to_hex(opcode_bytes))

        if len(decl.children) == 0:
            self.write(bytes([0,0]))
            return

        options = 0
        literal = None
        for i, c in enumerate(decl.children):
            if c.type == 'register':
                if hasattr(decl.get_config(), "SKIP_FIRST_REG"):
                    i += 1
                options |= c.get_code() << (5 - i * 3)
            elif c.type == 'label':
                options |= USE_LITERAL
                literal = 0
                self.unresolved_label_uses.append((self.write_addr + 1, c.label))
            else:
                options |= USE_LITERAL
                literal = c.value
        
        option_bytes = options.to_bytes(1, byteorder='big')
        self.write(option_bytes)
        print(decl.opcode + " options: " + bytearray_to_hex(option_bytes))

        if literal != None:
            if type(literal) == int:
                literal_bytes = literal.to_bytes(4, byteorder='big')
            elif type(literal) == float:
                literal_bytes = struct.pack('>f', literal)
            self.write(literal_bytes)
            print(str(literal) + ": " + bytearray_to_hex(literal_bytes))

    def generate(self):
        for decl in self.program.declarations:
            match decl.type:
                case 'label_decl':
                    self.generate_label_decl(decl)
                case 'instr':
                    self.generate_instr(decl)

        self.resolve_labels()

    def output(self, filename):
        with open(filename, 'w+') as f:
            # loop through the bytes in pairs
            for i in range(0, len(self.program_bytes) - 4, 4):
                # convert the pair to a 32 bit int
                b = self.program_bytes[i] << 24 | self.program_bytes[i + 1] << 16 | self.program_bytes[i + 2] << 8 | self.program_bytes[i + 3]
                # write the int to the file in hex
                f.write(hex(b)[2:] + ' ')

            f.close()

