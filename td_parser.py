import json
import scanner as sc
import code_gen as cg
import anytree

with open('data.json') as f:
    data = json.loads(''.join(f.readlines()))
    terminals = data['terminals']
    non_terminals = data['non-terminal']
    first = data['first']
    follow = data['follow']

transitions = {
    'Program': [['Declaration-list']],
    'Declaration-list': [['Declaration', 'Declaration-list'], ['EPSILON']],
    'Declaration': [['Declaration-initial', 'Declaration-prime']],
    'Declaration-initial': [['Type-specifier', 'ID', '#PID']],
    'Declaration-prime': [['Fun-declaration-prime'], ['Var-declaration-prime']],
    'Var-declaration-prime': [[';', '#ASSIGN_ZERO'], ['[', 'NUM', '#PNUM', ']', ';', '#ASSIGN_ZERO']],
    'Fun-declaration-prime': [['(', '#PARAM_ENTER', 'Params', '#PARAM_EXIT', ')', 'Compound-stmt', '#FUNC_EXIT']],
    'Type-specifier': [['int', '#PUSH_TYPE_INT'], ['void', '#PUSH_TYPE_VOID']],
    'Params': [['int', '#PUSH_TYPE_INT', 'ID', '#PID', 'Param-prime', '#PARAM_ASSIGN', 'Param-list'], ['void']],
    'Param-list': [[',', 'Param', '#PARAM_ASSIGN', 'Param-list'], ['EPSILON']],
    'Param': [['Declaration-initial', 'Param-prime']],
    'Param-prime': [['[', ']', '#PUSH_ARRAY_PARAM'], ['EPSILON']],
    'Compound-stmt': [['{', '#SCOPE_ENTER', 'Declaration-list', 'Statement-list', '#SCOPE_EXIT', '}']],
    'Statement-list': [['Statement', 'Statement-list'], ['EPSILON']],
    'Statement': [['Expression-stmt'], ['Compound-stmt'], ['Selection-stmt'], ['Iteration-stmt'], ['Return-stmt']],
    'Expression-stmt': [['Expression', ';', '#EXP_END'], ['break', '#BREAK_SAVE', ';'], [';']],
    'Selection-stmt': [['if', '(', 'Expression', ')', '#SAVE_IF', 'Statement', 'else', '#JPF_IF', 'Statement', '#JP_ELSE']],
    'Iteration-stmt': [['repeat', '#SAVE_REPEAT', 'Statement', 'until', '(', 'Expression', ')', '#JP_BREAK', '#JPF_REPEAT']],
    'Return-stmt': [['return', 'Return-stmt-prime', '#RETURN_JUMP']],
    'Return-stmt-prime': [[';'], ['Expression', ';', '#RETURN_ASSIGN']],
    'Expression': [['Simple-expression-zegond'], ['ID', '#PID', 'B']],
    'B': [['=', 'Expression', '#ASSIGN'], ['[', 'Expression', ']', '#ARRAY_INDEX', 'H'], ['Simple-expression-prime']],
    'H': [['=', 'Expression', '#ASSIGN'], ['G', 'D', 'C']],
    'Simple-expression-zegond': [['Additive-expression-zegond', 'C']],
    'Simple-expression-prime': [['Additive-expression-prime', 'C']],
    'C': [['Relop', 'Additive-expression', '#RELOP'], ['EPSILON']],
    'Relop': [['<', '#PUSH_LT'], ['==', '#PUSH_EQ']],
    'Additive-expression': [['Term', 'D']],
    'Additive-expression-prime': [['Term-prime', 'D']],
    'Additive-expression-zegond': [['Term-zegond', 'D']],
    'D': [['Addop', 'Term', '#ADD', 'D'], ['EPSILON']],
    'Addop': [['+', '#PUSH_ADD'], ['-', '#PUSH_SUB']],
    'Term': [['Factor', 'G']],
    'Term-prime': [['Factor-prime', 'G']],
    'Term-zegond': [['Factor-zegond', 'G']],
    'G': [['*', 'Factor', '#MULT', 'G'], ['EPSILON']],
    'Factor': [['(', 'Expression', ')'], ['ID', '#PID', 'Var-call-prime'], ['NUM', '#PNUM']],
    'Var-call-prime': [['(', 'Args', ')', '#FUNCTION_CALL'], ['Var-prime']],
    'Var-prime': [['[', 'Expression', ']', '#ARRAY_INDEX'], ['EPSILON']],
    'Factor-prime': [['(', 'Args', ')', '#FUNCTION_CALL'], ['EPSILON']],
    'Factor-zegond': [['(', 'Expression', ')'], ['NUM', '#PNUM']],
    'Args': [['Arg-list'], ['EPSILON']],
    'Arg-list': [['Expression', '#PUSH_ARGS', 'Arg-list-prime']],
    'Arg-list-prime': [[',', 'Expression', '#PUSH_ARGS', 'Arg-list-prime'], ['EPSILON']],
}


class TreeNode:
    def __init__(self, root_value, last_value):
        self.root = root_value
        self.last = last_value
        self.transitions = {}
        self.final_node = False


transitions_nodes = {}

for transition_root in transitions:
    root_node = TreeNode(transition_root, None)
    transitions_nodes[transition_root] = root_node
    for transition in transitions[transition_root]:
        current_node = root_node
        for child in transition:
            current_node.transitions[child] = TreeNode(transition_root, child)
            current_node = current_node.transitions[child]
        current_node.final_node = True


def parse(s):
    errors = []
    root = anytree.Node('Program')
    stack = []
    current_node = transitions_nodes['Program']
    current_anytree_node = root
    last_ID = None
    last_NUM = None
    last_token, expr, s = sc.get_next_token(s)
    while True:
        if last_token == 'ERROR':
            break
        if last_token == 'WS':
            last_token, expr, s = sc.get_next_token(s)
            continue
        if last_token == 'COM':
            last_token, expr, s = sc.get_next_token(s)
            continue
        last_grammar = last_token
        if last_token == 'KEYWORD' or last_token == 'SYMBOL':
            last_grammar = expr
        if last_token == 'EOF':
            last_grammar = '$'
        if current_node.final_node and current_node.root != 'Program':
            current_node, current_anytree_node = stack.pop()
            continue
        if last_grammar == '$':
            if current_node.root == 'Program':
                anytree.Node('$', parent=root)
                break
        is_next = False
        for transition in current_node.transitions:
            if transition in terminals and last_grammar == transition:
                if transition == 'ID':
                    last_ID = expr
                elif transition == 'NUM':
                    last_NUM = expr
                anytree.Node(f'({last_token}, {expr})',
                             parent=current_anytree_node)
                current_node = current_node.transitions[transition]
                last_token, expr, s = sc.get_next_token(s)
                is_next = True
                break
            elif transition in non_terminals and (last_grammar in first[transition] or ('EPSILON' in first[transition] and last_grammar in follow[transition])):
                stack.append(
                    (current_node.transitions[transition], current_anytree_node))
                current_anytree_node = anytree.Node(
                    transition, parent=current_anytree_node)
                current_node = transitions_nodes[transition]
                is_next = True
                break
            elif transition[0] == '#':
                print(transition)
                current_node = current_node.transitions[transition]
                args = None
                if transition == '#PID':
                    args = last_ID
                elif transition == '#PNUM':
                    args = last_NUM
                cg.code_gen(transition, args)
                is_next = True
                break
        if is_next:
            continue
        if 'EPSILON' in current_node.transitions:
            anytree.Node('epsilon', parent=current_anytree_node)
            current_node, current_anytree_node = stack.pop()
            continue
        if transition in terminals and last_grammar != transition:
            errors.append(
                f'#{sc.get_lineno()} : syntax error, missing {transition}')
            current_node = current_node.transitions[transition]
            continue
        if last_grammar in follow[transition]:
            errors.append(
                f'#{sc.get_lineno()} : syntax error, missing {transition}')
            current_node = current_node.transitions[transition]
        else:
            if last_grammar == '$':
                errors.append(
                    f'#{sc.get_lineno()} : syntax error, Unexpected EOF')
                break
            errors.append(
                f'#{sc.get_lineno()} : syntax error, illegal {last_grammar}')
            last_token, expr, s = sc.get_next_token(s)
    return root, errors, cg.get_code(), cg.semantic_errors
