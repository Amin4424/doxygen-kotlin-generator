import re

# Tokenizer pattern
TOKEN_PATTERN = re.compile(
    r'(?P<DOC_COMMENT>/\*\*(?:[^*]|\*(?!/))*\*/)|'
    r'(?P<MULTILINE_COMMENT>/\*(?:[^*]|\*(?!/))*\*/)|'
    r'(?P<SINGLELINE_COMMENT>//.*)|'
    r'(?P<TRIPLE_STRING>"""(?:[^"]|"(?!""))*""")|'
    r'(?P<STRING>"(?:[^"\\]|\\.)*")|'
    r'(?P<CHAR>\'(?:[^\'\\]|\\.)\')|'
    r'(?P<IDENTIFIER>[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<SYMBOL>[\{\}\(\)\[\]\:\,\;\?\.])|'
    r'(?P<OPERATOR>[\=\+\-\*\/\!\&\>\<]+)|'
    r'(?P<NEWLINE>\r?\n)|'
    r'(?P<SPACE>[ \t]+)|'
    r'(?P<OTHER>.)'
)

class TokenStream:
    def __init__(self, text):
        self.tokens = []
        for m in TOKEN_PATTERN.finditer(text):
            kind = m.lastgroup
            val = m.group(kind)
            self.tokens.append((kind, val))
        self.pos = 0
        self.len = len(self.tokens)

    def peek(self, offset=0):
        if self.pos + offset < self.len:
            return self.tokens[self.pos + offset]
        return None

    def next(self):
        if self.pos < self.len:
            t = self.tokens[self.pos]
            self.pos += 1
            return t
        return None

    def skip_whitespace_and_comments(self, output_list=None):
        while self.pos < self.len:
            t = self.tokens[self.pos]
            if t[0] in ('SPACE', 'NEWLINE', 'SINGLELINE_COMMENT', 'MULTILINE_COMMENT', 'DOC_COMMENT'):
                if output_list is not None:
                    output_list.append(t[1])
                self.pos += 1
            else:
                break

    def skip_whitespace(self, output_list=None):
        while self.pos < self.len:
            t = self.tokens[self.pos]
            if t[0] in ('SPACE', 'NEWLINE'):
                if output_list is not None:
                    output_list.append(t[1])
                self.pos += 1
            else:
                break

    def peek_non_whitespace(self, start_offset=0):
        idx = self.pos + start_offset
        while idx < self.len:
            t = self.tokens[idx]
            if t[0] not in ('SPACE', 'NEWLINE', 'SINGLELINE_COMMENT', 'MULTILINE_COMMENT', 'DOC_COMMENT'):
                return t, idx
            idx += 1
        return None, None

def split_params(param_str):
    params = []
    current = []
    depth = 0
    in_str = False
    str_char = None
    
    i = 0
    while i < len(param_str):
        c = param_str[i]
        if in_str:
            if c == str_char and param_str[i-1] != '\\':
                in_str = False
            current.append(c)
        elif c in ('"', "'"):
            in_str = True
            str_char = c
            current.append(c)
        elif c in ('(', '<', '{'):
            depth += 1
            current.append(c)
        elif c in (')', '>', '}'):
            depth -= 1
            current.append(c)
        elif c == ',' and depth == 0:
            params.append("".join(current).strip())
            current = []
        else:
            current.append(c)
        i += 1
    if current:
        params.append("".join(current).strip())
    return [p for p in params if p]
