from CEXGen.s_expr_converter import variable_parser
import os

with open(os.path.join(os.getcwd(), "LNT_template", "LNT_template.lnt"), 'r') as file :
    LNT_template = file.read()

with open(os.path.join(os.getcwd(), "LNT_template", "demo.sh"), 'r') as file :
    DEMOSHELL_template = file.read()


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

def form_string(sequence, variable_condition, ap, dep, cur_indent = 0):
    indent = "	"
    if sequence == []:
        return indent * cur_indent + "TESTOR_ACCEPT"
    else:
        action_num, action_class,  exist = sequence[0]

        argument_decl = create_action_declartion(dep, action_num, ap, variable_condition)
        #argument_decl.append("t_{i} := any Nat where (t_{i} < {t_bound});".format(i=action_num, t_bound=ap.b_time))
        action_occurance = "ACT_{} ({});".format(action_class, ', '.join(
            [form_arg_name(action_num, i) for i in range(len(ap.b_args))]))


        if exist:
            argument_decl.append(action_occurance)
            cont = form_string(sequence[1:], variable_condition, ap, dep, cur_indent = cur_indent)
            return "{cur}\n{next}".format(cur = '\n'.join([indent * cur_indent +  line for line in argument_decl]),
                                          next = cont)
        else:
            argument_decl = [indent * cur_indent + line for line in argument_decl]
            argument_decl.append(indent * cur_indent  + "select")
            argument_decl.append(indent * (cur_indent + 1) + action_occurance)
            argument_decl.append(indent * (cur_indent + 1) + "TESTOR_REFUSE")
            argument_decl.append(indent * cur_indent + "[]")
            cont = form_string(sequence[1:], variable_condition, ap, dep,  cur_indent = cur_indent+1)
            argument_decl.append(cont)
            argument_decl.append(indent * cur_indent + "end select")
            return '\n'.join(argument_decl)




def create_lnt_file(sequence, data_constraint, ap, module_name = "purpose"):
    global LNT_template
    vars, dep = variable_parser(data_constraint)

    variables = []
    variable_condition = dict()
    action_classes = set()
    # now we have sorted data with dependicies
    refuse = ""
    for action_num, action_class, exist in sequence:
        if not exist:
            refuse = "TESTOR_REFUSE,"

        action_classes.add("ACT_{}".format(action_class))
        for i in range(len(ap.b_args)):
            var_name = form_arg_name(action_num, i)
            variables.append(form_arg_name(action_num, i))
            var_dep = fetch_dependicy(dep, var_name)
            bound = ap.b_args[i]
            var_dep_string = ' and '.join(["({} < {})".format(var_name, bound)]+['({})'.format(content) for content in var_dep])
            #variables.append(var_name)
            var_declar_string = "{var_name}:= any NAT where {follow};".format(var_name=var_name,
                                                                                                  follow = var_dep_string)
            variable_condition[var_name] = var_declar_string

    decl = form_string(sequence, variable_condition, ap, dep, cur_indent = 2)
    variables = ', '.join(variables)
    #time_variables = ', '.join(time_variables)
    action_classes = ', '.join(action_classes)

    with open(os.path.join(os.getcwd(), "LTS_folder", "{}.lnt".format(module_name)), 'w') as outfile:
        outfile.write(LNT_template.format(decl=decl, arg_var = variables, module_name = module_name,
                                          action_class =action_classes, TESTOR_REFUSE = refuse))

    with open(os.path.join(os.getcwd(), "LTS_folder", "{}.sh".format(module_name)), 'w') as outfile:
        outfile.write(DEMOSHELL_template.replace("{purpose}", module_name))








