import random


def pretty_print( expr):

    if isinstance(expr, type("")):
        return expr
    elif isinstance(expr, type(1)):
        return str(expr)
    elif isinstance(expr, type([])):
        head = expr[0]
        if len(expr) == 2:
            # binary
            return "{} ({})".format(head, pretty_print(expr[1]))
        elif len(expr) == 3:
            return "({}) {} ({})".format(pretty_print(expr[1]), head, pretty_print(expr[2]))
        else:
            return "{} {}".format(head, ','.join([sub_exp for sub_exp in expr[1:]]))
    return ""



class SequenceConstraintGenerator():
    def __init__(self, ap, scope = None):
        self.ap = ap
        self.scope = scope

    def set_scope(self, scope):
        assert(scope != [])
        self.scope = scope

    def pretty_print_action(self, action_num, action_class, exist):
        if exist:
            return 'act_{}:ACT_{}'.format(action_num, action_class)
        else:
            return '(* \ act_{}:ACT_{})'.format(action_num, action_class)

    def pretty_print(self,  details):
        return ' , '.join([self.pretty_print_action(action_num, action_class, exist)
                           for action_num, action_class, exist in details])

    def generate_order(self, head, min_step = 1):
        condition_sequence =[]
        random.shuffle(condition_sequence)
        existence = []
        non_existence = []
        contex = set()
        cur_step = 0
        result = []
        while cur_step < min_step or bool(random.getrandbits(1)):
            exist = ( bool(random.getrandbits(1)) or len(contex) == self.ap.b_name -1)
            if exist:
                action_class = self.ap._choose_random_action(contex)
                condition_sequence.append(action_class)
                contex.clear()
                result.append((cur_step, action_class, True))
                cur_step += 1
            else:
                action_class = self.ap._choose_random_action(contex)
                contex.add(action_class)
                condition_sequence.append(action_class)
                result.append((cur_step, action_class, False))
                cur_step += 1

        result.append((len(condition_sequence), head, True))

        return condition_sequence, result


    def get_time_constraint(self, sequence, difference_ub):
        #choose the first action (ealier)
        act1 = random.randint(0, len(sequence)-2)
        #choose the second action (later)
        act2 = random.randint(act1+1, len(sequence)-1)

        difference = random.randint(0, difference_ub)
        random_op = random.choice(["<", ">"])
        #if within the range
        return [random_op, ["+", "act_{}.time".format(act1), str(difference)],"act_{}.time".format(act2)]



class DataArgCondition_Generator():
    def __init__(self, ap, scope=None):
        self.ap = ap
        self.numerical_function = [self.ADD, self.Minus]
        #self.boolean_function = [self.NOT, self.AND, self.OR, self.EQ, self.GT, self.LE, self.GE, self.LT, self.NEQ]
        self.boolean_function = [self.AND, self.EQ, self.GT, self.LE, self.GE, self.LT, self.NEQ]
        self.scope = scope

    def set_scope(self, scope):
        assert(scope != [])
        self.scope = scope

    def get_numerical(self, depth=0, constant_allow = False):
        if depth == 0:
            arg_num = random.randint(0 , len(self.ap.b_args) -1)
            #arg_bound = self.ap.b_args[arg_num]
            if constant_allow and bool(random.getrandbits(1)):
                return random.choice(["LB", "UP"])
            else:
                if self.scope is None or self.scope == []:
                    return "arg_{}".format(arg_num)
                else:
                    action = random.choice(self.scope)
                    return "arg_{}_{}".format(action, arg_num)
        else:
            return self.get_numerical(depth=0, constant_allow = constant_allow)
            #f = random.choice(self.numerical_function)
            #return f(depth)

    def get_boolean(self, depth=0):
         if depth == 0:
             f = random.choice(self.boolean_function)
             return f(1)
         else:
             f = random.choice(self.boolean_function)
             return f(depth)

    def NOT(self, depth):
        assert (depth > 0)
        return ["NOT", self.get_boolean(random.randint(0, depth-1))]

    def AND(self, depth):
        assert (depth > 0)
        return ["AND", self.get_boolean(random.randint(0, depth - 1)), self.get_boolean(random.randint(0, depth - 1))]

    def OR(self, depth):
        assert (depth > 0)
        return ["OR", self.get_boolean(random.randint(0, depth - 1)), self.get_boolean(random.randint(0, depth - 1))]

    def get_binary_numerical(self, boolean_op, depth, constant_allow = True):
        if depth == 1 and not constant_allow:
            return [boolean_op, self.get_numerical(random.randint(0, depth - 1)),
                    self.get_numerical(random.randint(0, depth - 1) ,constant_allow=False)]
        else:
            return [boolean_op, self.get_numerical(random.randint(0, depth - 1)), self.get_numerical(random.randint(0, depth - 1))]

    def EQ(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("==", depth, constant_allow=False)

    def NEQ(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("==", depth, constant_allow=False)

    def GT(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical(">", depth, constant_allow = False)

    def LT(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("<", depth, constant_allow = False)

    def GE(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical(">=", depth, constant_allow = False)

    def LE(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("<=", depth, constant_allow = False)

    def ADD(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("+", depth, constant_allow = False)

    def Minus(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("-", depth, constant_allow = False)




