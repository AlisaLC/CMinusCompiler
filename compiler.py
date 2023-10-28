import td_parser as parser

s = None
with open('input.txt') as f:
    s = ''.join(f.readlines())

with open('output.txt', 'w', encoding='UTF-8') as f, open('semantic_errors.txt', 'w', encoding='UTF-8') as fp:
    ـ, ـ, PB, semantic_errors = parser.parse(s)
    for error in semantic_errors:
        fp.write(f'{error}\n')
    if len(semantic_errors) == 0:
        f.write(f'{PB}\n')
        fp.write(f'The input program is semantically correct.')
    else:
        f.write('The output code has not been generated')
