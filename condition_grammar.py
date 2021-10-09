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



class Condition_Generator():
    def __init__(self, ap):
        self.ap = ap
        self.numerical_function = [self.ADD, self.Minus]
        self.boolean_function = [self.NOT, self.AND, self.OR, self.EQ, self.GT, self.LE, self.GE, self.LT]

    def get_numerical(self, depth=0):
        if depth == 0:
            arg_num = random.randint(0 , len(self.ap.b_args) -1)
            arg_bound = self.ap.b_args[arg_num]
            if bool(random.getrandbits(1)):
                return str(random.randint(0, arg_bound))
            else:
                return "VAR_{}".format(arg_num)
        else:
            f = random.choice(self.numerical_function)
            return f(depth)

    def get_boolean(self, depth=0):
         if depth == 0:
             return random.choice(["TRUE", "FALSE"])
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

    def get_binary_numerical(self, boolean_op, depth):
        return [boolean_op, self.get_numerical(random.randint(0, depth - 1)), self.get_numerical(random.randint(0, depth - 1))]

    def EQ(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("==", depth)

    def GT(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical(">", depth)

    def LT(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("<", depth)

    def GE(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical(">=", depth)

    def LE(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("<=", depth)

    def ADD(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("+", depth)

    def Minus(self, depth):
        assert (depth > 0)
        return self.get_binary_numerical("-", depth)




