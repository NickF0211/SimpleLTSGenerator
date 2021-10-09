import os.path

with open(os.path.join(os.getcwd(), "svl_template", "sync_template.txt")) as file:
    SVL_TEMPLATE = file.read()

with open(os.path.join(os.getcwd(), "svl_template", "component_detail.txt")) as file:
    COMPONENT_DETAIL = file.read()

with open(os.path.join(os.getcwd(), "svl_template", "sync_comp.txt")) as file:
    SYNC_COMP = file.read()

with open(os.path.join(os.getcwd(), "svl_template", "generation_header.txt")) as file:
    GENERATION_header = file.read()

def generate_svl(graph_name, N, shared_action = "ACT_SHARED"):
    global SVL_TEMPLATE, COMPONENT_DETAIL, SYNC_COMP, GENERATION_header
    generation_header = '\n'.join([GENERATION_header.format(graph = graph_name, id=i) for i in range(N)])
    component_detail = "\n        ||\n".join([COMPONENT_DETAIL.format(shared_action = shared_action, graph = graph_name, id=i) for i in range(N)])
    sync_comp = SYNC_COMP.format(component = component_detail)
    svl_file = SVL_TEMPLATE.format(generation_script = generation_header, sync_script = sync_comp)
    return svl_file

def generate_svl_ring(graph_name, N, shared_action):
    global SVL_TEMPLATE, SYNC_COMP, GENERATION_header
    generation_header = '\n'.join([GENERATION_header.format(graph=graph_name, id=i) for i in range(N)])
    svl_file = SVL_TEMPLATE.format(generation_script=generation_header, sync_script=generate_svl_for_ring(graph_name, N, shared_action))
    return svl_file

def form_body(graph_name, id):
    return "    \"{graph}_{id}.bcg\"".format(graph = graph_name, id=id)


def generate_svl_for_ring(graph_name, N, shared_action="ACT_SHARED_{}_{}"):
    if N <=  1:
        return ""
    indent_token = "    "
    cur_body = generate_svl_for_pair(N-1, 0, form_body(graph_name, N-1), form_body(graph_name, 0), shared_action, indent=indent_token*N)
    for i in range(N-2):
        next = i + 1
        if next == N-2:
            cur_body = generate_svl_for_pair_special(i, next, cur_body, form_body(graph_name, next), "{},{}".format(shared_action.format(i, next),
                                                                                                                    shared_action.format(next, next+1)),
                                  indent=indent_token * (N - 1 - i))
        else:
            cur_body = generate_svl_for_pair(i, next, cur_body, form_body(graph_name, next), shared_action, indent= indent_token * (N-1-i))

    return cur_body

def generate_svl_for_pair(pa, pb, pa_string, pb_string, shared_action="ACT_SHARED_{}_{}", indent=""):
    shared_action = shared_action.format(pa, pb)
    string= "{indent}par\n" \
            "{indent}   {shared_action} -> \n" \
            "{indent}{pa_string}\n" \
            "{indent}||\n" \
            "{indent}    {shared_action} -> \n" \
            "{indent}{pb_string}\n " \
            "{indent}end par".format(pa_string= pa_string, pb_string = pb_string, shared_action = shared_action.format(pa, pb),
                                      indent = indent)

    return string

def generate_svl_for_pair_special(pa, pb, pa_string, pb_string, shared_action, indent=""):
    shared_action = shared_action.format(pa, pb)
    string= "{indent}par\n" \
            "{indent}   {shared_action} -> \n" \
            "{indent}{pa_string}\n" \
            "{indent}||\n" \
            "{indent}    {shared_action} -> \n" \
            "{indent}{pb_string}\n " \
            "{indent}end par;".format(pa_string= pa_string, pb_string = pb_string, shared_action = shared_action,
                                      indent = indent)

    return string

