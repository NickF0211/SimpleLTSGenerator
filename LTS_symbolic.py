from graph import *
def build_graph(input_file):
    with open(input_file, 'r') as file:
        #skip the file line of the input file (the header)
        g= Graph(-1,571113)
        for i in range():
            g.add_node()
        file.readline()
        res = file.readline()
        while (res):
            clean = res.lstrip().rstrip().lstrip('(').rstrip(')')
            args = clean.split(',')
            instate = int(args[0])
            outstate = int(args[-1].lstrip())





build_graph("full_graph.aut")