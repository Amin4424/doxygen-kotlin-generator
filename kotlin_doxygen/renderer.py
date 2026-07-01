import re
from kotlin_doxygen.parser import split_params

TYPE_MAP = {
    'Int': 'int',
    'Long': 'long',
    'Boolean': 'boolean',
    'Double': 'double',
    'Float': 'float',
    'Char': 'char',
    'Byte': 'byte',
    'Short': 'short',
    'Any': 'Object',
    'Unit': 'void',
    'Nothing': 'void',
}

MODIFIERS = {
    'private', 'protected', 'public', 'internal',
    'override', 'open', 'abstract', 'final',
    'inline', 'const', 'lateinit', 'external',
    'actual', 'expect', 'annotation', 'data',
    'sealed', 'value', 'inner', 'suspend',
    'infix', 'operator', 'tailrec', 'vararg',
    'noinline', 'crossinline', 'reified'
}

def map_type(kt_type):
    if not kt_type:
        return 'Object'
    kt_type = kt_type.strip()
    # Strip nullability
    if kt_type.endswith('?'):
        kt_type = kt_type[:-1].strip()
    return TYPE_MAP.get(kt_type, kt_type)

def infer_type(initializer):
    if not initializer:
        return 'Object'
    initializer = initializer.strip()
    if initializer in ('true', 'false'):
        return 'boolean'
    if initializer.startswith('"') or initializer.startswith('"""'):
        return 'String'
    if re.match(r'^\d+$', initializer):
        return 'int'
    if re.match(r'^\d+L$', initializer):
        return 'long'
    if re.match(r'^\d+\.\d+f?$', initializer):
        return 'float' if initializer.endswith('f') else 'double'
    if 'ArrayList' in initializer:
        return 'ArrayList'
    if 'HashMap' in initializer:
        return 'HashMap'
    if 'HashSet' in initializer:
        return 'HashSet'
    if 'listOf' in initializer:
        return 'List'
    if 'mapOf' in initializer:
        return 'Map'
    if 'setOf' in initializer:
        return 'Set'
    return 'Object'

def clean_initializer(init_str):
    if any(k in init_str for k in ('if', 'else', 'when', 'run', 'let', '{', '}', 'try', 'catch')):
        return None
    return init_str.strip()

def translate_param_list(param_str):
    parts = split_params(param_str)
    res = []
    for part in parts:
        part = part.split('=')[0].strip()  # remove default values
        part = re.sub(r'^(vararg|val|var)\s+', '', part)
        if ':' in part:
            name, ptype = part.split(':', 1)
            name = name.strip()
            ptype = map_type(ptype.strip())
            res.append(f"{ptype} {name}")
        else:
            res.append(f"Object {part}")
    return ", ".join(res)
