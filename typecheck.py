from parse_types import *

"""
TYPECHECKING:

default rules:
    - all first values must be registers
    - all second values can be registers or ints/floats

special rules:
    - jump instructions can have labels or ints as first values
    - float instructions MUST have floats as second values
    - non float instructions CANNOT have floats as second values
    - the load instruction MUST have a 24 bit value as second value AT MOST
"""

labels = {}
unresolved_label_uses = []

def typecheck(node: Node):
    if node.type == None:
        raise TypeError(("", 0, 0), 'Got a node with type None')

    if node.type == 'program':
        for d in node.declarations:
            typecheck(d)

        for l in unresolved_label_uses:
            if l.label not in labels:
                raise LocationError(l.loc, 'No declaration for label \'%s\' found' %l.label)
    elif node.type == 'label_decl':
        if node.label in labels:
            other = labels[node.label]
            raise LocationError(node.loc, 'Label \'%s\' already declared at %s:%d:%d' % (node.label, other.loc[0], other.loc[1], other.loc[2]))
        labels[node.label] = node
    elif node.type == 'label':
        unresolved_label_uses.append(node)
        # if node.label not in labels:
        #     raise LocationError(node.loc, 'No declaration for label \'%s\' found' %node.label)
    elif node.type == 'instr':
        config = node.get_config()

        if len(node.children) != config.arg_num:
            raise LocationError(node.loc, 'Expected %d arguments, got %d' % (config.arg_num, len(node.children)))

        if config.arg_num > 0:
            if node.children[0].type not in config.first_val_types:
                raise TypeError(node.children[0].loc, " | ".join(config.first_val_types), node.children[0].type)

        if config.arg_num > 1:
            if node.children[1].type not in config.second_val_types:
                raise TypeError(node.children[1].loc, " | ".join(config.second_val_types), node.children[1].type)

    for c in node.children:
        typecheck(c)