
from numpy import prod
from numpy.random import binomial
from random import   randint
class ActionPool():
    def __init__(self, b_name, b_args, b_time, b_shared, b_shared_ratio =-1 ):
        # assume b_args is a list of natural numbers
        self.b_name = b_name
        self.b_args = b_args
        self.b_time = b_time
        self.b_shared = b_shared
        self.ap_size = b_name * prod(b_args) * b_time + b_shared
        if b_shared_ratio < 0 or b_shared_ratio > 1:
            self.shared_ratio = self.b_shared / (self.ap_size + self.b_shared)
        else:
            self.shared_ratio = b_shared_ratio

    def shared_action(self):
        return binomial(1, self.shared_ratio)

    def label(self, graph):
        #DFS on the graph, assume time transition is monotonic
        bound = graph.depth
        self._label(graph, graph.nodes[0],  0, bound, 0)

    def _label(self, graph, node,  cur_depth, max_depth, cur_shared = 0):
        assert(cur_depth <= max_depth)
        for out in node.out_going:
            action_name = randint(0, self.b_name)
            vars = [randint(0, b_var) for b_var in self.b_args]
            time = randint(0, self.b_time)
            if cur_shared < self.b_shared and  self.shared_action():
                shared_id = cur_shared
                out.add_label(SharedLabel(shared_id, time))
                new_shared = cur_shared + 1
            else:
                out.add_label(Label(action_name, vars, time))
                new_shared = cur_shared
            dest_node = graph.get_node(out.dest)
            self._label(graph, dest_node, cur_depth+1, max_depth, new_shared)

def prepare_ID( header, value):
    value = str(value)
    return "!IDS_OF ({}, {})".format( header, value)

class Label():

    def __init__(self, name, args, time):
        self.name = name
        self.args = args
        self.time = time


    def __repr__(self):
        action_head = prepare_ID("ACTION", "ACT_{}".format(self.name))
        action_time = prepare_ID("TIME", self.time)
        return "\"{} {} {} {}\"".\
            format("ACT_{}".format(self.name), action_head,
                   ' '.join([prepare_ID("VAR_{}".format(i), self.args[i] ) for i in range(len(self.args))]),
                   action_time)

    def actinorepr(self):
        return "\"ACT_{}\" {} time! {}".\
            format(str(self.name),
                   ' '.join(["var{}! {}".format(str(i), str(self.args[i])) for i in range(len(self.args))]),
                   self.time)


    def __str__(self):
        return self.__repr__()


class SharedLabel(Label):

    def __init__(self, id, time):
        super().__init__("shared", [id], time)