from actionPool import *
from graph import *

def generate_single_LTS(target_name, b_action, b_var, b_time, b_shared, b_depth, b_shared_ratio = -1):
    ap = ActionPool(b_action, b_var, b_time, b_shared, b_shared_ratio= b_shared_ratio)
    graph = Graph(b_depth, ap.ap_size)
    graph.generate()
    ap.label(graph)
    with open(target_name, 'w') as file:
        file.write(graph.write_LTS())

def generate_LTS(target_directory, b_action, b_var, b_time, b_shared, b_depth, b_shared_ratio = -1):
    return
