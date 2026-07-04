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
    'String': 'String',
    'ByteArray': 'byte[]',
    'CharArray': 'char[]',
    'IntArray': 'int[]',
    'LongArray': 'long[]',
    'FloatArray': 'float[]',
    'DoubleArray': 'double[]',
    'BooleanArray': 'boolean[]',
    'ShortArray': 'short[]',
}

BOXED_TYPE_MAP = {
    'Int': 'Integer',
    'Long': 'Long',
    'Boolean': 'Boolean',
    'Double': 'Double',
    'Float': 'Float',
    'Char': 'Character',
    'Byte': 'Byte',
    'Short': 'Short',
}

GENERIC_TYPE_MAP = {
    'MutableList': 'List',
    'MutableSet': 'Set',
    'MutableMap': 'Map',
    'MutableCollection': 'Collection',
    'MutableIterable': 'Iterable',
    'ArrayList': 'ArrayList',
    'HashMap': 'HashMap',
    'HashSet': 'HashSet',
    'MutableStateFlow': 'MutableStateFlow',
    'StateFlow': 'StateFlow',
    'MutableSharedFlow': 'MutableSharedFlow',
    'SharedFlow': 'SharedFlow',
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

PARAM_MODIFIERS = {
    'vararg', 'val', 'var', 'noinline', 'crossinline', 'reified'
}

def strip_annotations(text):
    """Remove Kotlin annotations from a signature fragment."""
    if not text:
        return text

    result = []
    i = 0
    while i < len(text):
        if text[i] != '@':
            result.append(text[i])
            i += 1
            continue

        i += 1
        while i < len(text) and (text[i].isalnum() or text[i] in ('_', ':', '.')):
            i += 1
        while i < len(text) and text[i].isspace():
            i += 1
        if i < len(text) and text[i] == '(':
            depth = 1
            i += 1
            while i < len(text) and depth > 0:
                if text[i] == '(':
                    depth += 1
                elif text[i] == ')':
                    depth -= 1
                i += 1
        result.append(' ')

    return re.sub(r'\s+', ' ', ''.join(result)).strip()

def _strip_outer_nullable(kt_type):
    kt_type = kt_type.strip()
    while kt_type.endswith('?'):
        kt_type = kt_type[:-1].strip()
    return kt_type

def _find_top_level(text, target):
    depth = 0
    in_str = False
    str_char = None

    i = 0
    while i < len(text):
        c = text[i]
        if in_str:
            if c == str_char and (i == 0 or text[i - 1] != '\\'):
                in_str = False
        elif c in ('"', "'"):
            in_str = True
            str_char = c
        elif c == target and depth == 0:
            return i
        elif c in '(<[{':
            depth += 1
        elif c in ')>]}':
            depth = max(0, depth - 1)
        i += 1
    return -1

def remove_default_value(param):
    eq_idx = _find_top_level(param, '=')
    if eq_idx >= 0:
        return param[:eq_idx].strip()
    return param.strip()

def strip_param_modifiers(param):
    param = strip_annotations(param).strip()
    changed = True
    while changed:
        changed = False
        for modifier in PARAM_MODIFIERS:
            pattern = rf'^{modifier}\b\s*'
            new_param = re.sub(pattern, '', param)
            if new_param != param:
                param = new_param.strip()
                changed = True
    return param

def _split_generic(kt_type):
    lt_idx = _find_top_level(kt_type, '<')
    if lt_idx < 0 or not kt_type.endswith('>'):
        return None, None
    base = kt_type[:lt_idx].strip()
    args = kt_type[lt_idx + 1:-1].strip()
    return base, split_params(args)

def _normalize_variance(type_arg):
    type_arg = type_arg.strip()
    type_arg = re.sub(r'^(out|in)\s+', '', type_arg)
    if type_arg == '*':
        return '?'
    return type_arg

def normalize_type_params(type_params):
    if not type_params:
        return ""

    type_params = type_params.strip()
    if type_params.startswith('<') and type_params.endswith('>'):
        type_params = type_params[1:-1]

    names = []
    for part in split_params(type_params):
        part = strip_annotations(part)
        part = re.sub(r'\b(reified|out|in)\b\s*', '', part).strip()
        part = part.split(':', 1)[0].strip()
        match = re.match(r'[A-Za-z_][A-Za-z0-9_]*', part)
        if match:
            names.append(match.group(0))

    return f"<{', '.join(names)}>" if names else ""

def map_type(kt_type, boxed=False):
    if not kt_type:
        return 'Object'
    kt_type = strip_annotations(kt_type)
    kt_type = _strip_outer_nullable(kt_type)
    kt_type = re.sub(r'\s+', ' ', kt_type).strip()
    if not kt_type:
        return 'Object'

    # Doxygen's Java parser cannot read Kotlin function type syntax reliably.
    if '->' in kt_type:
        return 'Function'

    # Receiver types can include nullable markers before member access.
    kt_type = kt_type.replace('?.', '.')

    if boxed and kt_type in BOXED_TYPE_MAP:
        return BOXED_TYPE_MAP[kt_type]

    if kt_type in TYPE_MAP:
        return TYPE_MAP[kt_type]

    base, args = _split_generic(kt_type)
    if base:
        normalized_args = [map_type(_normalize_variance(arg), boxed=True) for arg in args]
        if base == 'Array':
            return f"{normalized_args[0]}[]" if normalized_args else "Object[]"
        mapped_base = GENERIC_TYPE_MAP.get(base, TYPE_MAP.get(base, base))
        return f"{mapped_base}<{', '.join(normalized_args)}>"

    return kt_type

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
    remember_block_match = re.match(r'^remember\s*\{(.*)\}$', initializer, re.S)
    if remember_block_match:
        return infer_type(remember_block_match.group(1).strip())
    if initializer.startswith('mutableIntStateOf'):
        return 'int'
    if initializer.startswith('mutableFloatStateOf'):
        return 'float'
    if initializer.startswith('mutableDoubleStateOf'):
        return 'double'
    if initializer.startswith('mutableLongStateOf'):
        return 'long'
    state_match = re.match(r'^(mutableStateOf|remember)\s*\((.*)\)$', initializer, re.S)
    if state_match:
        return infer_type(state_match.group(2))
    flow_match = re.match(r'^(MutableStateFlow|StateFlow|MutableSharedFlow|SharedFlow)\s*\((.*)\)$', initializer, re.S)
    if flow_match:
        inner_type = infer_type(flow_match.group(2))
        if inner_type in {
            'int', 'long', 'boolean', 'double', 'float', 'char', 'byte', 'short'
        }:
            inner_type = BOXED_TYPE_MAP.get(inner_type.capitalize(), inner_type)
        return f"{flow_match.group(1)}<{inner_type}>"
    return 'Object'

def clean_initializer(init_str):
    if any(k in init_str for k in ('if', 'else', 'when', 'run', 'let', '{', '}', 'try', 'catch')):
        return None
    return init_str.strip()

def parse_parameter(part):
    part = strip_param_modifiers(remove_default_value(part))
    if not part:
        return None

    colon_idx = _find_top_level(part, ':')
    if colon_idx >= 0:
        name = part[:colon_idx].strip()
        ptype = part[colon_idx + 1:].strip()
        name = name.split()[-1] if name else 'param'
        return name, map_type(ptype)

    return part.strip(), 'Object'

def translate_param_list(param_str):
    parts = split_params(param_str)
    res = []
    for part in parts:
        parsed = parse_parameter(part)
        if not parsed:
            continue
        name, ptype = parsed
        res.append(f"{ptype} {name}")
    return ", ".join(res)
