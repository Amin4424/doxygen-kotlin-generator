import os
import re
from kotlin_doxygen.parser import TokenStream, split_params
from kotlin_doxygen.renderer import MODIFIERS, map_type, infer_type, clean_initializer, translate_param_list

def filter_kotlin(content: str, filename: str) -> str:
    stream = TokenStream(content)
    output = []

    # Get class name fallback from filename
    classname_from_file = os.path.splitext(filename)[0]
    if not classname_from_file:
        classname_from_file = "UnknownFile"
    if not classname_from_file[0].isupper():
        classname_from_file = classname_from_file.capitalize()
    classname_from_file += "Kt"

    scope_stack = []  # items: dict with keys 'type', 'is_object', 'brace_depth', 'name'
    brace_depth = 0
    top_level_class_open = False
    active_modifiers = []

    def is_in_class_scope():
        return any(s['type'] in ('class', 'companion') for s in scope_stack)

    def is_in_companion():
        return any(s['type'] == 'companion' for s in scope_stack)

    def is_in_object():
        return any(s.get('is_object', False) for s in scope_stack)

    def get_current_class_name():
        for s in reversed(scope_stack):
            if s['type'] == 'class':
                return s.get('name', 'UnknownClass')
        return classname_from_file

    while stream.pos < stream.len:
        # Move comments and whitespace to output directly
        stream.skip_whitespace_and_comments(output)
        if stream.pos >= stream.len:
            break

        t = stream.peek()
        if not t:
            break

        # Flush modifiers if the next semantic token is not a declaration or modifier
        next_sem, _ = stream.peek_non_whitespace()
        if next_sem and next_sem[1] not in ('fun', 'val', 'var', 'class', 'interface', 'object', 'enum', 'companion', 'init', 'constructor') and next_sem[1] not in MODIFIERS:
            if active_modifiers:
                output.append(" ".join(active_modifiers) + " ")
                active_modifiers = []

        # Handle braces and scopes
        if t[1] == '{':
            brace_depth += 1
            stream.next()
            output.append('{')
            continue

        if t[1] == '}':
            brace_depth -= 1
            stream.next()
            if scope_stack and scope_stack[-1]['brace_depth'] == brace_depth:
                popped = scope_stack.pop()
                if popped['type'] == 'companion':
                    output.append('/* end companion */')
                    continue
            output.append('}')
            continue

        # Package definition
        if t[0] == 'IDENTIFIER' and t[1] == 'package':
            output.append('package')
            stream.next()
            while stream.pos < stream.len:
                pk = stream.peek()
                if pk[0] == 'NEWLINE':
                    break
                output.append(stream.next()[1])
            output.append(';')
            continue

        # Import definition
        if t[0] == 'IDENTIFIER' and t[1] == 'import':
            output.append('import')
            stream.next()
            while stream.pos < stream.len:
                im = stream.peek()
                if im[0] == 'NEWLINE':
                    break
                output.append(stream.next()[1])
            output.append(';')
            continue

        # Modifiers collection
        if t[0] == 'IDENTIFIER' and t[1] in MODIFIERS:
            active_modifiers.append(t[1])
            stream.next()
            continue

        # Class / Interface / Object / Enum declarations
        if t[0] == 'IDENTIFIER' and t[1] in ('class', 'interface', 'object', 'enum'):
            if top_level_class_open and len(scope_stack) == 0:
                output.append('\n} /* end top level */\n')
                top_level_class_open = False

            is_enum = (t[1] == 'enum')
            is_object = (t[1] == 'object')
            is_interface = (t[1] == 'interface')
            kind_keyword = t[1]

            stream.next()  # consume keyword
            
            # Check if it was "enum class"
            next_t, next_idx = stream.peek_non_whitespace()
            if is_enum and next_t and next_t[1] == 'class':
                kind_keyword = 'enum'
                stream.pos = next_idx + 1

            # Get class name
            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[0] == 'IDENTIFIER':
                class_name = next_t[1]
                stream.pos = next_idx + 1
            else:
                class_name = "Unknown"

            # Parse primary constructor if exists
            next_t, next_idx = stream.peek_non_whitespace()
            primary_constructor_params = ""
            if next_t and next_t[1] == '(':
                stream.pos = next_idx + 1
                paren_depth = 1
                param_tokens = []
                while stream.pos < stream.len and paren_depth > 0:
                    pt = stream.next()
                    if pt[1] == '(':
                        paren_depth += 1
                    elif pt[1] == ')':
                        paren_depth -= 1
                    if paren_depth > 0:
                        param_tokens.append(pt[1])
                primary_constructor_params = "".join(param_tokens)

            # Parse inheritance / supertypes
            next_t, next_idx = stream.peek_non_whitespace()
            extends_clause = ""
            implements_clause = []
            if next_t and next_t[1] == ':':
                stream.pos = next_idx + 1
                super_tokens = []
                while stream.pos < stream.len:
                    st = stream.peek()
                    if st[1] == '{':
                        break
                    if st[0] == 'NEWLINE':
                        break
                    super_tokens.append(stream.next()[1])
                
                super_str = "".join(super_tokens).strip()
                supertypes = split_params(super_str)
                for i, stype in enumerate(supertypes):
                    stype = stype.strip()
                    is_class = '(' in stype or i == 0
                    stype_clean = stype.split('(')[0].strip()
                    if is_class and not extends_clause:
                        extends_clause = f"extends {stype_clean}"
                    else:
                        implements_clause.append(stype_clean)

            # Build class header
            java_kind = 'class'
            if is_interface:
                java_kind = 'interface'
            elif is_enum:
                java_kind = 'enum'
            elif 'annotation' in active_modifiers:
                java_kind = '@interface'

            inheritance = ""
            if extends_clause:
                inheritance += " " + extends_clause
            if implements_clause:
                inheritance += " implements " + ", ".join(implements_clause)

            # Build visibility/static modifiers
            vis = 'public'
            if 'private' in active_modifiers:
                vis = 'private'
            elif 'protected' in active_modifiers:
                vis = 'protected'

            cls_mods = [vis]
            if is_in_companion() or is_in_object():
                cls_mods.append('static')
            elif len(scope_stack) > 0 and 'inner' not in active_modifiers:
                cls_mods.append('static')

            if 'abstract' in active_modifiers:
                cls_mods.append('abstract')

            cls_mod_str = " ".join(cls_mods)
            active_modifiers = []

            output.append(f"{cls_mod_str} {java_kind} {class_name}{inheritance} ")

            # Prepare primary constructor fields and constructor method to inject inside the class body
            extra_body_content = ""
            if primary_constructor_params:
                parts = split_params(primary_constructor_params)
                constructor_args = []
                for part in parts:
                    part = part.strip()
                    has_val_var = re.match(r'^(val|var)\b', part) or 'val ' in part or 'var ' in part
                    clean_part = re.sub(r'^(val|var)\s+', '', part)
                    clean_part = clean_part.split('=')[0].strip()
                    if ':' in clean_part:
                        name, ptype = clean_part.split(':', 1)
                        name = name.strip()
                        ptype = map_type(ptype.strip())
                        constructor_args.append(f"{ptype} {name}")
                        if has_val_var:
                            is_final = "final " if 'val' in part else ""
                            extra_body_content += f"\n    public {is_final}{ptype} {name};"
                    else:
                        constructor_args.append(f"Object {clean_part}")
                
                args_str = ", ".join(constructor_args)
                extra_body_content += f"\n    public {class_name}({args_str}) {{}}"

            # Wait for '{'
            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[1] == '{':
                stream.pos = next_idx + 1
                scope_stack.append({'type': 'class', 'is_object': is_object, 'brace_depth': brace_depth, 'name': class_name})
                brace_depth += 1
                output.append("{\n" + extra_body_content + "\n")
            else:
                if extra_body_content:
                    output.append("{\n" + extra_body_content + "\n}")
                else:
                    output.append("{}")
            continue

        # Companion Object declaration
        if t[0] == 'IDENTIFIER' and t[1] == 'companion':
            next_t, next_idx = stream.peek_non_whitespace(start_offset=1)
            if next_t and next_t[1] == 'object':
                after_obj_t, after_obj_idx = stream.peek_non_whitespace(start_offset=(next_idx - stream.pos + 1))
                if after_obj_t:
                    if after_obj_t[1] == '{':
                        stream.pos = after_obj_idx + 1
                        scope_stack.append({'type': 'companion', 'is_object': False, 'brace_depth': brace_depth, 'name': 'Companion'})
                        brace_depth += 1
                        output.append('/* companion object */ ')
                        active_modifiers = []
                        continue
                    elif after_obj_t[0] == 'IDENTIFIER':
                        brace_t, brace_idx = stream.peek_non_whitespace(start_offset=(after_obj_idx - stream.pos + 1))
                        if brace_t and brace_t[1] == '{':
                            stream.pos = brace_idx + 1
                            scope_stack.append({'type': 'companion', 'is_object': False, 'brace_depth': brace_depth, 'name': after_obj_t[1]})
                            brace_depth += 1
                            output.append(f'/* companion object {after_obj_t[1]} */ ')
                            active_modifiers = []
                            continue

        # Initializer block
        if t[0] == 'IDENTIFIER' and t[1] == 'init':
            stream.next()
            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[1] == '{':
                stream.pos = next_idx + 1
                init_depth = 1
                while stream.pos < stream.len and init_depth > 0:
                    it = stream.next()
                    if it[1] == '{':
                        init_depth += 1
                    elif it[1] == '}':
                        init_depth -= 1
                output.append('/* init block */')
                active_modifiers = []
            continue

        # Secondary constructors
        if t[0] == 'IDENTIFIER' and t[1] == 'constructor':
            stream.next()  # consume 'constructor'
            next_t, next_idx = stream.peek_non_whitespace()
            constructor_params = ""
            if next_t and next_t[1] == '(':
                stream.pos = next_idx + 1
                p_depth = 1
                p_tokens = []
                while stream.pos < stream.len and p_depth > 0:
                    pt = stream.next()
                    if pt[1] == '(':
                        p_depth += 1
                    elif pt[1] == ')':
                        p_depth -= 1
                    if p_depth > 0:
                        p_tokens.append(pt[1])
                constructor_params = "".join(p_tokens)

            # Skip secondary constructor delegation like : this(...) or : super(...)
            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[1] == ':':
                stream.pos = next_idx + 1
                while stream.pos < stream.len:
                    nt = stream.peek()
                    if nt[1] == '{' or nt[0] == 'NEWLINE':
                        break
                    stream.next()

            class_name = get_current_class_name()
            translated_params = translate_param_list(constructor_params)
            
            vis = 'public'
            if 'private' in active_modifiers:
                vis = 'private'
            elif 'protected' in active_modifiers:
                vis = 'protected'
            
            output.append(f"{vis} {class_name}({translated_params}) ")
            active_modifiers = []

            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[1] == '{':
                stream.pos = next_idx + 1
                b_depth = 1
                while stream.pos < stream.len and b_depth > 0:
                    bt = stream.next()
                    if bt[1] == '{':
                        b_depth += 1
                    elif bt[1] == '}':
                        b_depth -= 1
                output.append("{}")
            else:
                output.append(";")
            continue

        # Functions (fun)
        if t[0] == 'IDENTIFIER' and t[1] == 'fun':
            # Check if it is a functional interface: 'fun interface'
            next_t, next_idx = stream.peek_non_whitespace(start_offset=1)
            if next_t and next_t[1] == 'interface':
                active_modifiers.append('fun')
                stream.next()  # consume 'fun'
                continue

            if not is_in_class_scope() and not top_level_class_open:
                output.append(f"\npublic class {classname_from_file} {{\n")
                top_level_class_open = True

            stream.next()  # consume "fun"

            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[1] == '<':
                stream.pos = next_idx + 1
                g_depth = 1
                while stream.pos < stream.len and g_depth > 0:
                    gt = stream.next()
                    if gt[1] == '<':
                        g_depth += 1
                    elif gt[1] == '>':
                        g_depth -= 1

            scan_idx = stream.pos
            tokens_before_paren = []
            found_paren = False
            while scan_idx < stream.len:
                t_scan = stream.tokens[scan_idx]
                if t_scan[1] == '(':
                    found_paren = True
                    break
                elif t_scan[1] in ('{', '}'):
                    break
                if t_scan[0] not in ('SPACE', 'NEWLINE', 'SINGLELINE_COMMENT', 'MULTILINE_COMMENT', 'DOC_COMMENT'):
                    tokens_before_paren.append((t_scan, scan_idx))
                scan_idx += 1

            is_extension = False
            receiver_type = ""
            fun_name = "unknownFunction"

            if found_paren and len(tokens_before_paren) >= 3 and tokens_before_paren[-2][0][1] == '.':
                is_extension = True
                fun_name = tokens_before_paren[-1][0][1]
                receiver_parts = [tk[0][1] for tk in tokens_before_paren[:-2]]
                receiver_type = "".join(receiver_parts)
                stream.pos = scan_idx + 1
            else:
                if tokens_before_paren:
                    fun_name = tokens_before_paren[-1][0][1]
                if found_paren:
                    stream.pos = scan_idx + 1

            p_depth = 1
            p_tokens = []
            while stream.pos < stream.len and p_depth > 0:
                pt = stream.next()
                if pt[1] == '(':
                    p_depth += 1
                elif pt[1] == ')':
                    p_depth -= 1
                if p_depth > 0:
                    p_tokens.append(pt[1])
            fun_params = "".join(p_tokens)

            next_t, next_idx = stream.peek_non_whitespace()
            return_type = "void"
            if next_t and next_t[1] == ':':
                stream.pos = next_idx + 1
                ret_tokens = []
                while stream.pos < stream.len:
                    rt = stream.peek()
                    if rt[1] in ('{', '=', '}'):
                        break
                    if rt[0] == 'NEWLINE':
                        break
                    ret_tokens.append(stream.next()[1])
                return_type = map_type("".join(ret_tokens))

            vis = 'public'
            if 'private' in active_modifiers:
                vis = 'private'
            elif 'protected' in active_modifiers:
                vis = 'protected'

            modifiers = [vis]
            if is_in_companion() or is_in_object() or not is_in_class_scope() or is_extension:
                modifiers.append('static')

            if 'external' in active_modifiers:
                modifiers.append('native')

            mod_str = " ".join(modifiers)
            active_modifiers = []

            translated_params = translate_param_list(fun_params)
            if is_extension:
                mapped_receiver = map_type(receiver_type)
                receiver_var = "receiver"
                if translated_params:
                    translated_params = f"{mapped_receiver} {receiver_var}, {translated_params}"
                else:
                    translated_params = f"{mapped_receiver} {receiver_var}"

            output.append(f"{mod_str} {return_type} {fun_name}({translated_params}) ")

            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[1] == '{':
                stream.pos = next_idx + 1
                b_depth = 1
                while stream.pos < stream.len and b_depth > 0:
                    bt = stream.next()
                    if bt[1] == '{':
                        b_depth += 1
                    elif bt[1] == '}':
                        b_depth -= 1
                output.append("{}")
            elif next_t and next_t[1] == '=':
                stream.pos = next_idx + 1
                while stream.pos < stream.len:
                    nt = stream.peek()
                    if nt[0] == 'NEWLINE':
                        break
                    stream.next()
                output.append("{}")
            else:
                output.append(";")
            continue

        # Variables / Properties (val / var)
        if t[0] == 'IDENTIFIER' and t[1] in ('val', 'var'):
            is_val = (t[1] == 'val')
            if not is_in_class_scope() and not top_level_class_open:
                output.append(f"\npublic class {classname_from_file} {{\n")
                top_level_class_open = True

            stream.next()  # consume 'val'/'var'

            # 1. Skip generics if present (e.g. val <T> List<T>.foo)
            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[1] == '<':
                stream.pos = next_idx + 1
                g_depth = 1
                while stream.pos < stream.len and g_depth > 0:
                    gt = stream.next()
                    if gt[1] == '<':
                        g_depth += 1
                    elif gt[1] == '>':
                        g_depth -= 1

            # 2. Scan forward to find ':' or '=' or 'by' or 'NEWLINE' to parse name and check for extension property
            scan_idx = stream.pos
            tokens_before_type = []
            while scan_idx < stream.len:
                t_scan = stream.tokens[scan_idx]
                if t_scan[1] in (':', '=', '{', '}'):
                    break
                elif t_scan[0] == 'IDENTIFIER' and t_scan[1] == 'by':
                    break
                elif t_scan[0] == 'NEWLINE':
                    break
                if t_scan[0] not in ('SPACE', 'NEWLINE', 'SINGLELINE_COMMENT', 'MULTILINE_COMMENT', 'DOC_COMMENT'):
                    tokens_before_type.append((t_scan, scan_idx))
                scan_idx += 1

            is_prop_extension = False
            receiver_type = ""
            var_name = "unknownVar"

            if len(tokens_before_type) >= 3 and tokens_before_type[-2][0][1] == '.':
                is_prop_extension = True
                var_name = tokens_before_type[-1][0][1]
                receiver_parts = [tk[0][1] for tk in tokens_before_type[:-2]]
                receiver_type = "".join(receiver_parts)
            else:
                if tokens_before_type:
                    var_name = tokens_before_type[-1][0][1]

            stream.pos = scan_idx

            # 3. Parse explicit type if separator is ':'
            next_t, next_idx = stream.peek_non_whitespace()
            explicit_type = None
            if next_t and next_t[1] == ':':
                stream.pos = next_idx + 1
                type_tokens = []
                while stream.pos < stream.len:
                    tt = stream.peek()
                    if tt[1] in ('=', 'by', '{', '}', 'get', 'set'):
                        break
                    if tt[0] == 'NEWLINE':
                        break
                    type_tokens.append(stream.next()[1])
                explicit_type = map_type("".join(type_tokens))

            # 4. Check for initializer if next is '='
            next_t, next_idx = stream.peek_non_whitespace()
            initializer = None
            if next_t and next_t[1] == '=':
                stream.pos = next_idx + 1
                init_tokens = []
                while stream.pos < stream.len:
                    it = stream.peek()
                    if it[0] == 'NEWLINE':
                        break
                    init_tokens.append(stream.next()[1])
                initializer = clean_initializer("".join(init_tokens))

            # 5. Check for delegate if next is 'by'
            next_t, next_idx = stream.peek_non_whitespace()
            if next_t and next_t[1] == 'by':
                stream.pos = next_idx + 1
                depth = 0
                while stream.pos < stream.len:
                    nt = stream.peek()
                    if nt[1] in ('(', '{', '['):
                        depth += 1
                    elif nt[1] in (')', '}', ']'):
                        depth -= 1
                    elif nt[0] == 'NEWLINE' and depth == 0:
                        break
                    elif depth == 0 and nt[0] == 'IDENTIFIER' and nt[1] in ('val', 'var', 'fun', 'class', 'interface', 'object', 'enum', 'get', 'set'):
                        break
                    stream.next()

            if explicit_type:
                java_type = explicit_type
            elif initializer:
                java_type = infer_type(initializer)
            else:
                java_type = 'Object'

            vis = 'public'
            if 'private' in active_modifiers:
                vis = 'private'
            elif 'protected' in active_modifiers:
                vis = 'protected'

            modifiers = [vis]
            if is_in_companion() or is_in_object() or not is_in_class_scope() or 'const' in active_modifiers or is_prop_extension:
                modifiers.append('static')
            
            if is_val or 'const' in active_modifiers:
                modifiers.append('final')

            mod_str = " ".join(modifiers)
            init_str = f" = {initializer}" if initializer else ""
            if is_prop_extension:
                output.append(f"/* Extension on {receiver_type} */\n{mod_str} {java_type} {var_name}{init_str};")
            else:
                output.append(f"{mod_str} {java_type} {var_name}{init_str};")
            active_modifiers = []

            next_t, next_idx = stream.peek_non_whitespace()
            while next_t and next_t[1] in ('get', 'set'):
                # Consume 'get'/'set'
                stream.pos = next_idx + 1
                
                # Check if next is '(' (e.g. get() or set(value))
                next_t, next_idx = stream.peek_non_whitespace()
                if next_t and next_t[1] == '(':
                    stream.pos = next_idx + 1
                    p_depth = 1
                    while stream.pos < stream.len and p_depth > 0:
                        pt = stream.next()
                        if pt[1] == '(':
                            p_depth += 1
                        elif pt[1] == ')':
                            p_depth -= 1
                    next_t, next_idx = stream.peek_non_whitespace()
                
                # Now check if it has a body via '=' or '{'
                if next_t and next_t[1] == '{':
                    stream.pos = next_idx + 1
                    g_depth = 1
                    while stream.pos < stream.len and g_depth > 0:
                        gt = stream.next()
                        if gt[1] == '{':
                            g_depth += 1
                        elif gt[1] == '}':
                            g_depth -= 1
                elif next_t and next_t[1] == '=':
                    stream.pos = next_idx + 1
                    while stream.pos < stream.len:
                        nt = stream.peek()
                        if nt[0] == 'NEWLINE':
                            break
                        stream.next()
                
                # Peek for next getter/setter
                next_t, next_idx = stream.peek_non_whitespace()
            continue

        # If none of the above, just copy token to output
        output.append(stream.next()[1])

    if top_level_class_open:
        output.append('\n} /* end top level */\n')

    return "".join(output)
