import scanner as sc

FUNCTION_TYPE = 0
VARIABLE_TYPE = 1
ARRAY_TYPE = 2

INT_TYPE = 0
VOID_TYPE = 1


class ScopeItem:
    def __init__(self, pid, ftype=FUNCTION_TYPE, vtype=VOID_TYPE) -> None:
        self.pid = pid
        self.ftype = ftype
        self.vtype = vtype
        self.is_assigned = False

    def __repr__(self) -> str:
        return f'({self.pid}, {self.ftype}, {self.vtype}, {self.is_assigned})'


scope_stack = {
    '-': [{'output': ScopeItem(500, FUNCTION_TYPE, VOID_TYPE)}]
}
CURRENT_FUNCTION = '-'
FUNCTION_PARAMS = {
    'output': [(VARIABLE_TYPE, INT_TYPE)]
}
break_scope_stack = []
SS = []
BS = []
PB = [
    ('ASSIGN', '#0', 96, None),
    ('ASSIGN', '#0', 92, None),
] + [None for _ in range(50000)]
JP_MAIN = 3
PC = 2
RETURN_ADDR = 96
RETURN_JP_ADDR = 92
PARAM_COUNTER = 100
ARG_COUNTER = 100
LAST_TEMP = 508
semantic_errors = []


def get_global_from_pid(pid):
    for fname, item in scope_stack['-'][0].items():
        if item.pid == pid:
            return fname, item
    return None, None


def get_local_from_pid(pid):
    for stack in scope_stack[CURRENT_FUNCTION][::-1]:
        for fname, item in stack.items():
            if item.pid == pid:
                return fname, item
    return None, None


def get_code():
    global PB
    PB = PB[:PC]
    print('\n'.join([f'{i}\t{ins}' for i, ins in enumerate(PB)]))
    PB = [f'{i}\t({PB[i][0]}, {PB[i][1] if PB[i][1] is not None else " "}, {PB[i][2] if PB[i][2] is not None else " "}, {PB[i][3] if PB[i][3] is not None else " "} )' for i in range(len(PB))]
    return '\n'.join(PB)


def get_temp():
    global LAST_TEMP
    LAST_TEMP += 4
    return LAST_TEMP - 4


def pid(var):
    if len(scope_stack) == 1 and var == 'main':
        if PC != JP_MAIN:
            PB[JP_MAIN] = ('JP', f'{PC}', None, None)
    if CURRENT_FUNCTION == '-':
        if var not in scope_stack['-'][0]:
            scope_stack['-'][0][var] = ScopeItem(get_temp(), VARIABLE_TYPE,
                                                 VOID_TYPE if SS[-1] == '#VOID' else INT_TYPE)
        SS.append(scope_stack['-'][0][var].pid)
        return
    for stack in scope_stack[CURRENT_FUNCTION][::-1]:
        if var in stack:
            SS.append(stack[var].pid)
            return
    if var in scope_stack['-'][0]:
        SS.append(scope_stack['-'][0][var].pid)
        return
    scope_stack[CURRENT_FUNCTION][-1][var] = ScopeItem(
        get_temp(), VARIABLE_TYPE, VOID_TYPE if SS[-1] == '#VOID' else INT_TYPE)
    SS.append(scope_stack[CURRENT_FUNCTION][-1][var].pid)


def pnum(num):
    SS.append(f'#{num}')


def type_check(pid_1, pid_2):
    lfname, lfitem = get_local_from_pid(pid_1)
    gfname, gfitem = get_global_from_pid(pid_1)
    fname_1 = None
    fitem_1 = None
    if lfname is None and gfname is not None:
        fname_1 = gfname
        fitem_1 = gfitem
    elif lfname is not None:
        fname_1 = lfname
        fitem_1 = lfitem
    lfname, lfitem = get_local_from_pid(pid_2)
    gfname, gfitem = get_global_from_pid(pid_2)
    fname_2 = None
    fitem_2 = None
    if lfname is None and gfname is not None:
        fname_2 = gfname
        fitem_2 = gfitem
    elif lfname is not None:
        fname_2 = lfname
        fitem_2 = lfitem
    if fname_1 is not None:
        if not fitem_1.is_assigned:
            semantic_errors.append(
                f'#{sc.get_lineno()}: Semantic Error! \'{fname_1}\' is not defined.')
        if fitem_1.vtype == VOID_TYPE:
            semantic_errors.append(
                f'#{sc.get_lineno()}: Semantic Error! Type mismatch in operands, Got void instead of int.')
        elif fitem_1.ftype == ARRAY_TYPE:
            semantic_errors.append(
                f'#{sc.get_lineno()}: Semantic Error! Type mismatch in operands, Got array instead of int.')
    if fname_2 is not None:
        if not fitem_2.is_assigned:
            semantic_errors.append(
                f'#{sc.get_lineno()}: Semantic Error! \'{fname_2}\' is not defined.')
        if fitem_2.vtype == VOID_TYPE:
            semantic_errors.append(
                f'#{sc.get_lineno()}: Semantic Error! Type mismatch in operands, Got void instead of int.')
        elif fitem_2.ftype == ARRAY_TYPE:
            semantic_errors.append(
                f'#{sc.get_lineno()}: Semantic Error! Type mismatch in operands, Got array instead of int.')


def add():
    global PC
    if len(SS) < 2:
        return
    if SS[-2] != '+' and SS[-2] != '-':
        return
    type_check(SS[-3], SS[-1])
    temp = get_temp()
    action = 'ADD'
    if SS[-2] == '-':
        action = 'SUB'
    PB[PC] = (action, f'{SS[-3]}', f'{SS[-1]}', temp)
    SS.pop()
    SS.pop()
    SS.pop()
    SS.append(temp)
    PC += 1


def push_add():
    SS.append('+')


def push_sub():
    SS.append('-')


def mult():
    global PC
    if len(SS) < 2:
        return
    type_check(SS[-2], SS[-1])
    temp = get_temp()
    PB[PC] = ('MULT', f'{SS[-1]}', f'{SS[-2]}', temp)
    SS.pop()
    SS.pop()
    SS.append(temp)
    PC += 1


def assign(is_zero=False):
    global PC, LAST_TEMP
    if is_zero:
        is_arr = str(SS[-1])[0] == '#'
        vpid = SS[-1]
        if is_arr:
            vpid = SS[-2]
        vtype = VOID_TYPE if SS[-2] == '#VOID' else INT_TYPE
        if is_arr:
            vtype = VOID_TYPE if SS[-3] == '#VOID' else INT_TYPE
        gfname, gfitem = get_global_from_pid(vpid)
        lfname, lfitem = get_local_from_pid(vpid)
        if lfname is None and gfname is not None and CURRENT_FUNCTION != '-':
            temp = get_temp()
            scope_stack[CURRENT_FUNCTION][-1][fname] = ScopeItem(
                temp, ARRAY_TYPE if is_arr else VARIABLE_TYPE, vtype)
            if is_arr:
                SS[-2] = temp
            else:
                SS[-1] = temp
            lfname, lfitem = get_local_from_pid(vpid)
        if lfname is not None:
            for stack in scope_stack[CURRENT_FUNCTION][::-1]:
                if lfname in stack:
                    stack[lfname].vtype = vtype
                    stack[lfname].is_assigned = True
                    if is_arr:
                        stack[lfname].ftype = ARRAY_TYPE
                    else:
                        stack[lfname].ftype = VARIABLE_TYPE
                    break
        elif gfname is not None and CURRENT_FUNCTION == '-':
            for fname, item in scope_stack['-'][0].items():
                if item.pid == vpid:
                    scope_stack[CURRENT_FUNCTION][-1][fname].vtype = vtype
                    scope_stack[CURRENT_FUNCTION][-1][fname].is_assigned = True
                    if is_arr:
                        scope_stack[CURRENT_FUNCTION][-1][fname].ftype = ARRAY_TYPE
                    else:
                        scope_stack[CURRENT_FUNCTION][-1][fname].ftype = VARIABLE_TYPE
                    break
        if vtype == VOID_TYPE:
            semantic_errors.append(
                f'#{sc.get_lineno() - 1}: Semantic Error! Illegal type of void for \'{lfname if lfname is not None else gfname}\'.')
        SS.append('#0')
        if is_arr:
            for fname, item in scope_stack[CURRENT_FUNCTION][-1].items():
                if item.pid == SS[-3]:
                    scope_stack[CURRENT_FUNCTION][-1][fname].ftype = ARRAY_TYPE
            zero, length, var = SS[-1], SS[-2], SS[-3]
            if length == '#0':
                return
            PB[PC] = ('ASSIGN', f'#{var + 4}', f'{var}', None)
            PC += 1
            LAST_TEMP += int(length[1:]) * 4
            SS.pop()
            SS.pop()
            SS.pop()
            SS.pop()
            SS.append(var + 4)
            SS.append(zero)
        else:
            vtype, var, zero = SS[-3], SS[-2], SS[-1]
            SS.pop()
            SS.pop()
            SS.pop()
            SS.append(var)
            SS.append(zero)
    else:
        gfname, gfitem = get_global_from_pid(SS[-2])
        lfname, lfitem = get_local_from_pid(SS[-2])
        if lfname is not None:
            if not lfitem.is_assigned:
                semantic_errors.append(
                    f'#{sc.get_lineno()}: Semantic Error! \'{lfname}\' is not defined.')
        elif gfname is not None:
            if not gfitem.is_assigned:
                semantic_errors.append(
                    f'#{sc.get_lineno()}: Semantic Error! \'{gfname}\' is not defined.')
        if str(SS[-1])[0] != '#' and str(SS[-1])[0] != '@':
            lfname, litem = get_local_from_pid(SS[-1])
            gfname, gitem = get_global_from_pid(SS[-1])
            if lfname is None and gfname is not None:
                if not gitem.is_assigned:
                    semantic_errors.append(
                        f'#{sc.get_lineno()}: Semantic Error! \'{gfname}\' is not defined.')
            elif lfname is not None:
                if not litem.is_assigned:
                    semantic_errors.append(
                        f'#{sc.get_lineno()}: Semantic Error! \'{lfname}\' is not defined.')
    if len(SS) < 2:
        return
    PB[PC] = ('ASSIGN', f'{SS[-1]}', f'{SS[-2]}', None)
    value = SS.pop()
    SS.pop()
    if not is_zero:
        SS.append(value)
    PC += 1


def function_call():
    global PC, ARG_COUNTER
    if len(SS) < 1:
        return
    fname, fitem, = get_global_from_pid(SS[-1])
    if fitem.ftype != FUNCTION_TYPE:
        semantic_errors.append(
            f'#{sc.get_lineno()}: Semantic Error! \'{fname}\' is not defined.')
        return
    if (ARG_COUNTER - 100) // 4 != len(FUNCTION_PARAMS[fname]):
        semantic_errors.append(
            f'#{sc.get_lineno()}: Semantic Error! Mismatch in numbers of arguments of \'{fname}\'.')
    if SS[-1] == scope_stack['-'][0]['output'].pid:
        PB[PC] = ('PRINT', f'{100}', None, None)
        SS.pop()
        SS.append(100)
        PC += 1
    else:
        for fname, item in scope_stack['-'][0].items():
            if item.pid == SS[-1]:
                if fname == CURRENT_FUNCTION:
                    PB[PC] = ('JP', f'@{RETURN_JP_ADDR}', None, None)
                    PC += 1
        temp = get_temp()
        PB[PC] = ('ASSIGN', f'{RETURN_JP_ADDR}', f'{temp}', None)
        PC += 1
        PB[PC] = ('ASSIGN', f'#{PC + 2}', f'{RETURN_JP_ADDR}', None)
        PC += 1
        PB[PC] = ('JP', f'{SS[-1]}', None, None)
        PC += 1
        PB[PC] = ('ASSIGN', f'{temp}', f'{RETURN_JP_ADDR}', None)
        PC += 1
        PB[PC] = ('ASSIGN', f'{RETURN_ADDR}', f'{temp}', None)
        PC += 1
        SS.pop()
        SS.append(temp)
    ARG_COUNTER = 100


def relop():
    global PC
    if len(SS) < 2:
        return
    if SS[-2] != '<' and SS[-2] != '==':
        return
    type_check(SS[-3], SS[-1])
    temp = get_temp()
    action = 'LT'
    if SS[-2] == '==':
        action = 'EQ'
    PB[PC] = (action, f'{SS[-3]}', f'{SS[-1]}', temp)
    SS.pop()
    SS.pop()
    SS.pop()
    SS.append(temp)
    PC += 1


def push_lt():
    SS.append('<')


def push_eq():
    SS.append('==')


def array_index():
    global PC
    if len(SS) < 2:
        return
    temp = get_temp()
    PB[PC] = ('MULT', f'{SS[-1]}', '#4', temp)
    PB[PC+1] = ('ADD', f'{SS[-2]}', temp, temp)
    SS.pop()
    SS.pop()
    SS.append(f'@{temp}')
    PC += 2


def save_repeat():
    SS.append(PC)
    break_scope_stack.append(len(scope_stack[CURRENT_FUNCTION]))


def jpf_repeat():
    global PC
    if len(SS) < 2:
        return
    PB[PC] = ('JPF', f'{SS[-1]}', f'{SS[-2]}', None)
    SS.pop()
    SS.pop()
    PC += 1


def save_if():
    global PC
    SS.append(PC)
    PC += 1


def jpf_if():
    global PC
    if len(SS) < 2:
        return
    PB[SS[-1]] = ('JPF', f'{SS[-2]}', f'{PC+1}', None)
    SS.pop()
    SS.pop()
    SS.append(PC)
    PC += 1


def jp_else():
    PB[SS[-1]] = ('JP', f'{PC}', None, None)
    SS.pop()


def scope_enter():
    scope_stack[CURRENT_FUNCTION].append({})


def scope_exit():
    scope_stack[CURRENT_FUNCTION].pop()


def break_save():
    global PC
    if len(break_scope_stack) == 0:
        semantic_errors.append(
            f'#{sc.get_lineno()}: Semantic Error! No \'repeat ... until\' found for \'break\'.')
        return
    BS.append((break_scope_stack[-1], PC))
    PC += 1


def jp_break():
    global PC
    for i in range(len(BS)-1, -1, -1):
        if BS[i][0] == break_scope_stack[-1]:
            PB[BS[i][1]] = ('JP', f'{PC+1}', None, None)
            BS.pop(i)
    break_scope_stack.pop()


def exp_end():
    global PC
    SS.pop()


def param_enter():
    global PC, PARAM_COUNTER, CURRENT_FUNCTION, JP_MAIN
    function_counter = 0
    for _, item in scope_stack['-'][0].items():
        if item.ftype == FUNCTION_TYPE:
            function_counter += 1
    func_pid = SS.pop()
    vtype = VOID_TYPE if SS[-1] == '#VOID' else INT_TYPE
    for func, item in scope_stack['-'][0].items():
        if func_pid == item.pid:
            scope_stack['-'][0][func] = ScopeItem(PC, FUNCTION_TYPE, vtype)
            CURRENT_FUNCTION = func
            FUNCTION_PARAMS[func] = []
            break
    SS.append(PC)
    if function_counter == 1:
        if CURRENT_FUNCTION != 'main':
            JP_MAIN = PC
            PC += 1
    scope_stack[CURRENT_FUNCTION] = [{}]
    PARAM_COUNTER = 100


def param_assign():
    global PC, PARAM_COUNTER
    if len(SS) < 1:
        return
    is_arr = str(SS[-1]) == '#ARRAY_PARAM'
    vpid = SS[-1]
    if is_arr:
        SS.pop()
        vpid = SS[-1]
    vtype = VOID_TYPE if SS[-2] == '#VOID' else INT_TYPE
    FUNCTION_PARAMS[CURRENT_FUNCTION].append(
        (ARRAY_TYPE if is_arr else VARIABLE_TYPE, vtype))
    gfname, gfitem = get_global_from_pid(vpid)
    lfname, lfitem = get_local_from_pid(vpid)
    if vtype == VOID_TYPE:
        semantic_errors.append(
            f'#{sc.get_lineno()}: Semantic Error! Illegal type of void for \'{lfname if lfname is not None else gfname}\'.')
    if lfname is None and gfname is not None:
        scope_stack[CURRENT_FUNCTION][-1][gfname] = ScopeItem(
            get_temp(), ARRAY_TYPE if is_arr else VARIABLE_TYPE, vtype)
        SS[-1] = scope_stack[CURRENT_FUNCTION][-1][gfname].pid
        lfname, lfitem = get_local_from_pid(vpid)
    lfitem.is_assigned = True
    if is_arr:
        scope_stack[CURRENT_FUNCTION][-1][lfname] = ScopeItem(
            SS[-1], ARRAY_TYPE, vtype)
        scope_stack[CURRENT_FUNCTION][-1][lfname].is_assigned = True
        PB[PC] = ('ASSIGN', f'{PARAM_COUNTER}', f'{SS[-1]}', None)
    else:
        PB[PC] = ('ASSIGN', f'{PARAM_COUNTER}', f'{SS[-1]}', None)
    PARAM_COUNTER += 4
    PC += 1
    SS.pop()
    SS.pop()


def param_exit():
    global PARAM_COUNTER
    PARAM_COUNTER = 100


def return_assign():
    global PC
    if len(SS) < 1:
        return
    gfname, gfitem = get_global_from_pid(SS[-1])
    lfname, lfitem = get_local_from_pid(SS[-1])
    if lfname is None and gfname is not None:
        if not gfitem.is_assigned:
            semantic_errors.append(
                f'#{sc.get_lineno() - 1}: Semantic Error! \'{gfname}\' is not defined.')
    elif lfname is not None:
        if not lfitem.is_assigned:
            semantic_errors.append(
                f'#{sc.get_lineno() - 1}: Semantic Error! \'{lfname}\' is not defined.')
    PB[PC] = ('ASSIGN', f'{SS[-1]}', f'{RETURN_ADDR}', None)
    PC += 1
    SS.pop()


def return_jump():
    global PC
    PB[PC] = ('JP', f'@{RETURN_JP_ADDR}', None, None)
    PC += 1


def func_exit():
    global PC, CURRENT_FUNCTION
    if CURRENT_FUNCTION != 'main':
        PB[PC] = ('JP', f'@{RETURN_JP_ADDR}', None, None)
        PC += 1
    del scope_stack[CURRENT_FUNCTION]
    CURRENT_FUNCTION = '-'


def push_args():
    global PC, ARG_COUNTER
    if len(SS) < 2:
        return
    func_name, _ = get_global_from_pid(SS[-2])
    arg_count = (ARG_COUNTER - 100) // 4
    if arg_count + 1 > len(FUNCTION_PARAMS[func_name]):
        ARG_COUNTER += 4
        SS.pop()
        return
    vftype, vvtype = FUNCTION_PARAMS[func_name][arg_count]
    if str(SS[-1])[0] != '#' and str(SS[-1])[0] != '@':
        lfname, litem = get_local_from_pid(SS[-1])
        gfname, gitem = get_global_from_pid(SS[-1])
        if lfname is None and gfname is not None:
            if not gitem.is_assigned:
                semantic_errors.append(
                    f'#{sc.get_lineno()}: Semantic Error! \'{gfname}\' is not defined.')
            if gitem.vtype != vvtype or gitem.ftype != vftype:
                semantic_errors.append(
                    f'#{sc.get_lineno()}: Semantic Error! Mismatch in type of argument {arg_count + 1} of \'{func_name}\'. Expected \'{"array" if vftype == ARRAY_TYPE else "int" if vvtype == INT_TYPE else "void"}\' but got \'{"array" if gitem.ftype == ARRAY_TYPE else "int" if gitem.vtype == INT_TYPE else "void"}\' instead.')
        elif lfname is not None:
            if not litem.is_assigned:
                semantic_errors.append(
                    f'#{sc.get_lineno()}: Semantic Error! \'{lfname}\' is not defined.')
            if litem.vtype != vvtype or litem.ftype != vftype:
                semantic_errors.append(
                    f'#{sc.get_lineno()}: Semantic Error! Mismatch in type of argument {arg_count + 1} of \'{func_name}\'. Expected \'{"array" if vftype == ARRAY_TYPE else "int" if vvtype == INT_TYPE else "void"}\' but got \'{"array" if litem.ftype == ARRAY_TYPE else "int" if litem.vtype == INT_TYPE else "void"}\' instead.')
    elif str(SS[-1])[0] == '#':
        if vftype == ARRAY_TYPE or vvtype == VOID_TYPE:
            semantic_errors.append(
                f'#{sc.get_lineno()}: Semantic Error! Mismatch in type of argument {arg_count + 1} of \'{func_name}\'. Expected \'{"array" if vftype == ARRAY_TYPE else "int" if vvtype == INT_TYPE else "void"}\' but got \'int\' instead.')
    PB[PC] = ('ASSIGN', f'{SS[-1]}', f'{ARG_COUNTER}', None)
    PC += 1
    SS.pop()
    ARG_COUNTER += 4


def push_array_param():
    SS.append('#ARRAY_PARAM')


def push_type(type):
    SS.append(f'#{type}')


def code_gen(action, *args):
    if action == '#PID':
        pid(*args)
    elif action == '#PNUM':
        pnum(*args)
    elif action == '#ADD':
        add()
    elif action == '#PUSH_ADD':
        push_add()
    elif action == '#PUSH_SUB':
        push_sub()
    elif action == '#MULT':
        mult()
    elif action == '#ASSIGN':
        assign()
    elif action == '#ASSIGN_ZERO':
        assign(True)
    elif action == '#FUNCTION_CALL':
        function_call()
    elif action == '#PUSH_LT':
        push_lt()
    elif action == '#PUSH_EQ':
        push_eq()
    elif action == '#RELOP':
        relop()
    elif action == '#ARRAY_INDEX':
        array_index()
    elif action == '#SAVE_REPEAT':
        save_repeat()
    elif action == '#JPF_REPEAT':
        jpf_repeat()
    elif action == '#SAVE_IF':
        save_if()
    elif action == '#JPF_IF':
        jpf_if()
    elif action == '#JP_ELSE':
        jp_else()
    elif action == '#SCOPE_ENTER':
        scope_enter()
    elif action == '#SCOPE_EXIT':
        scope_exit()
    elif action == '#BREAK_SAVE':
        break_save()
    elif action == '#JP_BREAK':
        jp_break()
    elif action == '#EXP_END':
        exp_end()
    elif action == '#PARAM_ENTER':
        param_enter()
    elif action == '#PARAM_EXIT':
        param_exit()
    elif action == '#FUNC_EXIT':
        func_exit()
    elif action == '#PARAM_ASSIGN':
        param_assign()
    elif action == '#RETURN_ASSIGN':
        return_assign()
    elif action == '#RETURN_JUMP':
        return_jump()
    elif action == '#PUSH_ARGS':
        push_args()
    elif action == '#PUSH_ARRAY_PARAM':
        push_array_param()
    elif action == '#PUSH_TYPE_VOID':
        push_type('VOID')
    elif action == '#PUSH_TYPE_INT':
        push_type('INT')
    print('SS:', SS)
    print('BS:', BS)
    print('BREAK:', break_scope_stack)
    print('SCOPE:', scope_stack)
