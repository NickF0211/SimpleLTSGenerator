from pysmt.shortcuts import *

unary = {"NOT": Not}
binary_comp =  {" + " : lambda a, b: Plus([a,b]),   "-": Minus, ">=": GE, "<=" : LE, ">": GT, "<" :LT,  "==": Equals, "!=":NotEquals}
binary = binary_comp.update({"AND": lambda a, b: And([a,b]), "OR": lambda a, b: Or([a,b])})

def convert(s_expr):
    if isinstance(s_expr,  type("")):
        return Symbol(s_expr,  typename=INT)
    elif isinstance(s_expr, type(0)):
        return Int(s_expr)
    elif isinstance(s_expr, type([])):
        if len(s_expr) == 1:
            return convert(s_expr[0])
        elif len(s_expr) == 2:
            #unary
            op = s_expr[0]
            op_f = unary.get(op, None)
            assert (op_f is not None)
            return op_f(convert(s_expr[1]))
        elif len(s_expr) == "3":
            op = s_expr[0]
            op_f = binary.get(op, None)
            return op_f(convert(s_expr[1]), convert(s_expr[2]))
        else:
            "unsupported op"
            assert (False)

def add_dep(dep, var1, var2, value):

    var1_dict = dep.get(var1, None)
    if var1_dict is None:
        var1_dict = dict()
        dep[var1] = var1_dict

    var2_list = var1_dict.get(var2, None)
    if var2_list is None:
        var2_list = []
        var1_dict[var2] = var2_list
    var2_list.append(value)

    return value

def _variable_parser(s_expr, dependices):
    if isinstance(s_expr, type("")):
        return [s_expr]
    elif isinstance(s_expr, type([])):
        col = []
        head = s_expr[0]
        if len(s_expr)  == 3:
            if head in binary_comp.keys():
                left_vars = _variable_parser(s_expr[1], dependices)
                right_vars = _variable_parser(s_expr[2], dependices)
                # every variable from left var has dependency on variable in right_vars:
                sub_clause_string = pretty_print(s_expr)
                col = left_vars + right_vars
                left = set(left_vars)
                right = set(right_vars)
                for var1 in left:
                    for var2 in right:
                        if var1 < var2:
                            temp = var2
                            var2 = var1
                            var1 = temp

                        add_dep(dependices, var1, var2, sub_clause_string)
        else:
            for sub_expr in s_expr[1:]:
                col += _variable_parser(sub_expr, dependices)
        return col
    else:
        return []

def variable_parser(s_expr):
    dep = {}
    res = _variable_parser(s_expr, dep)
    return set(res), dep

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