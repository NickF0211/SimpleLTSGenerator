import math
from random import randint



class Graph():
    def __init__(self, b_depth, b_edges):
        self.depth = 0
        self.nodes = [Node(self, 0, 0)]
        self.b_depth =b_depth
        self.b_edges = b_edges
        min_fanout  = int(math.ceil(math.log(b_edges, b_depth)))
        self.fanout= min_fanout



    def get_node(self, id):
        return self.nodes[id]

    def add_node(self, depth=-1):
        id =  len(self.nodes)
        self.nodes.append(Node(self, id, depth))
        return id

    def add_edge(self, src_id, dest_id):
        src = self.get_node(src_id)
        dest = self.get_node(dest_id)
        edge = Edge(src_id, dest_id)
        src.add_out_edge(edge)
        dest.add_in_edge(edge)

    def generate(self):
        queue = [0]
        cur_edges = 0
        #A simple BFS that
        depth = 0
        while queue != [] and cur_edges  < self.b_edges:
            head = queue.pop(0)
            depth = self.get_node(head).depth
            random_fanout = randint(self.fanout, math.ceil(1.5 * self.fanout))
            for i in range(random_fanout):
                if cur_edges == self.b_edges:
                    return
                dest_id = self.add_node(depth+1)
                self.add_edge(head,  dest_id)
                queue.append(dest_id)
                cur_edges+=1


    def write_LTS(self):
        header = "des (0, {}, {})".format(self.b_edges, len(self.nodes))
        string_list = [header]
        queue = [0]
        while queue != []:
            head = queue.pop(0)
            head_node = self.get_node(head)
            for edge in head_node.out_going:
                string_list.append(str(edge))
                queue.append(edge.dest)

        return '\n'.join(string_list)


class Node():
    def __init__(self, graph, id, depth=-1):
        self.id = id
        self.graph = graph
        self.depth = depth
        self.out_going = []
        self.in_coming = []

        if depth > self.graph.depth:
            graph.depth = depth

    def add_out_edge(self, edge):
        self.out_going.append(edge)

    def add_in_edge(self, edge):
        self.in_coming.append(edge)


class Edge():

    def __init__(self, src, dest):
        self.src = src
        self.dest =dest
        self.label = None

    def add_label(self, label):
        self.label = label

    def __repr__(self):
        if self.label is None:
            return  "{} -> {}".format(self.src, self.dest)
        else:
            return "({}, {} ,{})".format(self.src,  str(self.label), self.dest)

    def __str__(self):
        return self.__repr__()

