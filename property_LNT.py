from CEXGen.s_expr_converter import variable_parser


def get_action_and_index(arg_name):
    args = arg_name.spilit('_')
    action_num = args[1]
    arg_index = args[2]

    return action_num, arg_index

def form_arg_name(action_num, arg_index):
    return "arg_{}_{}".format(action_num, arg_index)

def fetch_dependicy(dep, var1):
    res = dep.get(var1, None)
    collection = []
    if res is not None:
        for _, value in res.items():
            collection += value
        return collection
    else:
        return collection

def create_action_declartion(dep, action_num, ap, variable_condition):
    lines = []
    for i in range(len(ap.b_args)):
        var_name = form_arg_name(action_num, i)
        var_declar_string = variable_condition.get(var_name, None)
        if var_declar_string is None:
            var_dep = fetch_dependicy(dep, var_name)
            bound = ap.b_args[i]
            var_dep_string = ' and '.join(
                ["({} < {})".format(var_name, bound)] + ['({})'.format(content) for content in var_dep])
            var_declar_string = "{var_name}:= any NAT where {follow};".format(var_name=var_name,
                                                                              follow=var_dep_string)
        lines.append(var_declar_string)

    return lines



def create_lnt_file(sequence, data_constraint, ap):
    vars, dep = variable_parser(data_constraint)
    sorted_var = sorted(list(vars))

    variables = []
    variable_condition = dict()
    # now we have sorted data with dependicies
    cur_exists = True
    for action_num, action_class, exist in sequence:
        for i in range(len(ap.b_args)):
            var_name = form_arg_name(action_num, i)
            variables.append(form_arg_name(action_num, i))
            var_dep = fetch_dependicy(dep, var_name)
            bound = ap.b_args[i]
            var_dep_string = ' and '.join(["({} < {})".format(var_name, bound)]+['({})'.format(content) for content in var_dep])
            variables.append(var_name)
            var_declar_string = "{var_name}:= any NAT where {follow};".format(var_name=var_name,
                                                                                                  follow = var_dep_string)
            variable_condition[var_name] = var_declar_string

        argument_declar = create_action_declartion(dep, action_num, ap, variable_condition)
        argument_declar.append("t_{i} := any Nat where (t_{i} < {t_bound});".format(i=action_num, t_bound=ap.b_time))
        print('\n'.join(argument_declar))




