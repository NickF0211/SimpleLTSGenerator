import random

from numpy import prod
from numpy.random import binomial
from random import   randint, getrandbits
from condition_grammar import DataArgCondition_Generator, SequenceConstraintGenerator, pretty_print


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

        self.DG = DataArgCondition_Generator(self)
        self.SG = SequenceConstraintGenerator(self)

    def _sample_condition_actions(self, min_length=1):
        condition_act =[]
        while min_length > 0 or bool(getrandbits(1)):
            condition_act.append(self._choose_random_action())
            min_length -= 1

        return condition_act

    def generate_random_constraints(self, is_time = True, is_data=True):
        head_action = self._choose_random_action()
        condition_actions = self._sample_condition_actions(1)
        depth = random.randint(1, 10)
        sequence, detail = self.random_sequence_constraint(head_action, condition_actions)
        sequence_constraint = self.SG.pretty_print(detail)
        time, data = "", ""

        if is_time:
            time = self.SG.get_time_constraint(sequence, 10)

        if is_data:
            data = self.random_data_constraints(sequence[-1], sequence[:-1], depth)

        return sequence_constraint, time, data


    def random_data_constraints(self, head_act, cond_acts, depth):
        self.DG.set_scope([head_act] + cond_acts)
        return self.DG.get_boolean(depth)

    def random_sequence_constraint(self, head_act, cond_acts):
        return self.SG.generate_order(head_act, cond_acts)


    def _choose_random_action(self):
        return randint(0, self.b_name-1)


    def sample_prohibition(self):
        head_action_type = self._choose_random_action()
        condition_action =[]
        while bool(random.getrandbits(1)):
            condition_action.append( self._choose_random_action())



    def shared_action(self):
        return binomial(1, self.shared_ratio)


    def label_ring(self, graph, ring_size):
        bound = graph.depth
        id = graph.id
        forward   = id + 1
        if forward >= ring_size:
            forward = 0
        backward = id - 1

        if backward < 0:
            backward = ring_size-1

        self._ring_label(graph, graph.nodes[0],  0, bound, forward, backward, 0 ,0)



    def forward_or_backward(self, forward_shared, backward_shared):
        if forward_shared == self.b_shared:
            forward_chance = False
        else:
            forward_chance = self.shared_action()
        if backward_shared == self.b_shared:
            backward_chance = False
        else:
            backward_chance = self.shared_action()

        if forward_shared >= backward_shared:
            if forward_chance:
                return 1
            elif backward_chance:
                return 2
            else:
                return 0
        else:
            if backward_chance:
                return 2
            elif forward_chance:
                return 1
            else:
                return 0


    def _ring_label(self, graph, node, cur_depth, max_depth, forward_id, backward_id, forward_shared, backward_shared):
        assert(cur_depth <= max_depth)
        for out in node.out_going:
            action_name = randint(0, self.b_name)
            vars = [randint(0, b_var) for b_var in self.b_args]
            time = randint(0, self.b_time)
            result = self.forward_or_backward(forward_shared, backward_shared)
            if result == 1:
                shared_id = forward_shared
                out.add_label(ProcessWishSharedLabels(shared_id, graph.id, forward_id))
                new_forward_shared_shared = forward_shared + 1
                new_backward_shared = backward_shared
            elif result == 2:
                shared_id = backward_shared
                out.add_label(ProcessWishSharedLabels(shared_id, backward_id, graph.id))
                new_forward_shared_shared = forward_shared
                new_backward_shared = backward_shared+ 1
            else:
                out.add_label(Label(action_name, vars, time))
                new_forward_shared_shared = forward_shared
                new_backward_shared = backward_shared
            dest_node = graph.get_node(out.dest)
            self._ring_label(graph, dest_node, cur_depth+1, max_depth, forward_id, backward_id, new_forward_shared_shared, new_backward_shared )


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
                out.add_label(SharedLabel(shared_id))
                new_shared = cur_shared + 1
            else:
                out.add_label(Label(action_name, vars, time))
                new_shared = cur_shared
            dest_node = graph.get_node(out.dest)
            self._label(graph, dest_node, cur_depth+1, max_depth, new_shared)

def prepare_ID( header, value):
    value = str(value)
    return "!IDS_OF ({}, {})".format( header, value)

def define_and_increment(col, key):
    res = col.get(key, 0)
    col[key] = res + 1



class Label():
    labels = set()
    def __init__(self, name, args, time):
        self.name = name
        self.args = args
        self.time = time
        Label.labels.add(self)


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

    def __hash__(self):
        return str(self).__hash__()

class SharedLabel(Label):

    def __init__(self, id):
        super().__init__("SHARED", [id], 0)


class ProcessWishSharedLabels(Label):
    def __init__(self, id, pa, pb):
        super().__init__("SHARED_{}_{}".format(pa, pb), [id], 0)



