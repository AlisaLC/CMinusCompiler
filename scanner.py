

def get_next_token(stream):
    global chars, nums, symbols, whitespace
    if len(stream) == 0:
        return ('EOF', '', '')
    temp = stream[0]

    if temp in chars:
        return get_next_chars(stream)
    elif temp in nums:
        return get_next_num(stream)
    elif temp in symbols:
        return get_next_symbols(stream)
    elif temp == '/':
        return get_next_comment(stream)
    elif temp in whitespace:
        return get_next_whitespace(stream)
    else:
        return ('ERROR', ('Invalid input', temp), stream[1:])


def get_next_symbols(stream):
    global chars, nums, symbols, whitespace
    if stream[0] in [';', ':', '[', ']', '(', ')', '{', '}', '+', '-', ',']:
        return ('SYMBOL', stream[0], stream[1:])
    if len(stream) == 1:
        return ('SYMBOL', stream[0], '')
    if stream[0] == '=':
        if stream[1] == '=':
            return ('SYMBOL', stream[0:2], stream[2:])
        if not (stream[1] in chars or stream[1] in nums or stream[1] in whitespace or stream[1] == '/'):
            return ('ERROR', ('Invalid input', stream[:2]), stream[2:])
        return ('SYMBOL', stream[0:1], stream[1:])
    if stream[0] == '<':
        if stream[1] == '=':
            return ('SYMBOL', stream[0:2], stream[2:])
        return ('SYMBOL', stream[0:1], stream[1:])
    if stream[0] == '>':
        if stream[1] == '=':
            return ('SYMBOL', stream[0:2], stream[2:])
        return ('SYMBOL', stream[0:1], stream[1:])
    if stream[0] == '*':
        if stream[1] == '/':
            return ('ERROR', ('Unmatched comment', '*/'), stream[2:])
        if not (stream[1] in chars or stream[1] in nums or stream[1] in whitespace):
            return ('ERROR', ('Invalid input', stream[:2]), stream[2:])
        return ('SYMBOL', stream[0:1], stream[1:])


def get_next_comment(stream):
    global lineno
    lineno_temp = lineno
    if len(stream) == 1:
        return ('ERROR', ('Invalid input', '/'), '')
    if stream[1] == '#':
        return ('ERROR', ('Invalid input', stream[:2]), stream[2:])
    if not stream[1] == '*':
        return ('ERROR', ('Invalid input', '/'), stream[1:])
    temp = stream[2:]
    for idx in range(len(temp)):
        if temp[idx:].startswith('*/'):
            return ('COM', stream[:idx + 4], stream[idx + 4:])
        elif temp[idx] == '\n':
            lineno += 1
    return ('ERROR', ('Unclosed comment', stream, lineno_temp), '')


def get_next_chars(stream):
    global keywords, chars, nums, symbols, whitespace
    for kw in keywords:
        if stream.startswith(kw):
            if len(kw) == len(stream):
                return ('KEYWORD', kw, '')
            elif stream[len(kw)] in whitespace or stream[len(kw)] in symbols:
                return ('KEYWORD', kw, stream[len(kw):])
    for idx, c in enumerate(stream):
        if c in nums or c in chars:
            continue
        elif c in whitespace or c in symbols:
            if stream[:idx] not in seen:
                seen[stream[:idx]] = True
                symbol_table.append(stream[:idx])
            return ('ID', stream[:idx], stream[idx:])
        return ('ERROR', ('Invalid input', stream[:idx + 1]), stream[idx + 1:])
    if stream[:idx] not in seen:
        seen[stream[:idx]] = True
        symbol_table.append(stream[:idx])
    return ('ID', stream, '')


def get_next_num(stream):
    global chars, nums, symbols, whitespace
    for idx, c in enumerate(stream):
        if c in nums:
            continue
        elif c in whitespace or c in symbols:
            return ('NUM', stream[:idx], stream[idx:])
        return ('ERROR', ('Invalid number', stream[:idx + 1]), stream[idx + 1:])
    return ('NUM', stream, '')


def get_next_whitespace(stream):
    if stream[0] == '\n':
        global lineno
        lineno += 1
    return ('WS', stream[0], stream[1:])


def get_lineno():
    global lineno
    return lineno


def get_symbol_table():
    global symbol_table
    return symbol_table


chars = [chr(i + ord('a')) for i in range(26)]
chars.extend([chr(i + ord('A')) for i in range(26)])
chars.append('_')
nums = [chr(i + ord('0')) for i in range(10)]
symbols = [';', ':', '[', ']',
           '(', ')', '{', '}', '+', '-', '*', '=', '<', '>', ',']
keywords = ['if', 'else', 'void', 'int', 'repeat', 'break', 'until', 'return']
whitespace = ['\n', '\f', '\r', '\t', '\v', ' ']
symbol_table = ['break', 'else', 'if', 'int',
                'repeat', 'return', 'until', 'void']
seen = {}
lineno = 1
