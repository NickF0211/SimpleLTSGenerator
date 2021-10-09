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
