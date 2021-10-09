from actionPool import *
from graph import *
from svl_template import generate_svl, generate_svl_ring
import os

def generate_single_LTS(target_name, b_action, b_var, b_time, b_shared, b_depth, b_shared_ratio = -1):
    ap = ActionPool(b_action, b_var, b_time, b_shared, b_shared_ratio= b_shared_ratio)
    graph = Graph(b_depth, ap.ap_size)
    graph.generate()
    ap.label(graph)
    with open(target_name, 'w') as file:
        file.write(graph.write_LTS())

def generate_LTS(target_directory, N, b_action, b_var, b_time, b_shared, b_depth, b_shared_ratio = -1 , ring_sync = False):
    if not os.path.isdir(target_directory):
        os.mkdir(target_directory)
    ap = ActionPool(b_action, b_var, b_time, b_shared, b_shared_ratio= b_shared_ratio)
    for i in range(N):
        target_file = os.path.join(os.getcwd(), target_directory, "graph_{}.aut".format(i))
        graph = Graph(b_depth, ap.ap_size, id=i)
        graph.generate()
        if ring_sync:
            ap.label_ring(graph, N)
        else:
            ap.label(graph)
        with open(target_file, 'w') as file:
            file.write(graph.write_LTS())
    with open(os.path.join(os.getcwd(), target_directory, "demo.svl"), 'w') as file:
        if ring_sync:
            file.write(generate_svl_ring("graph", N, "ACT_SHARED_{}_{}"))
        else:
            file.write(generate_svl("graph", N))

