from pysmt.shortcuts import *
import constraint_solver as cs
import itertools
controll_varaible_eq = dict()
controll_varaible_eq_r = dict()
raw_control_variable = set()
controll_variable = set()
controll_variable_scope = dict()
control_var_sym = dict()

learned_inv = []
model_action_mapping = dict()
class Control_Tree():

    def __init__(self, control_vs, trees, name="control_v"):
        self.control_vs = control_vs
        self.trees = trees
        self.name = name


    def add_child(self, child_vs, child_trees):
        self.control_vs += child_vs
        self.trees += child_trees

def look_for_child_control_variable(formula):
   collection = set()
   fv = get_free_variables(formula)
   for v in fv:
       if v.symbol_name().startswith("control_v_"):
           collection.add(v)
   return collection


def build_tree(control_vs, args):
    trees = []
    for control_v, arg in zip(control_vs, args):

            control_set = look_for_child_control_variable(arg)
            tree= set()
            for child in control_set:
                ct = controll_variable_scope.get(child, None)
                if ct is not None:
                    tree.add(ct)
            trees.append(tree)

            controll_varaible_eq[arg] = control_v
            controll_varaible_eq_r[control_v] = arg


    c_tree = Control_Tree(control_vs, trees)
    for control_v in control_vs:
        controll_variable_scope[control_v] = c_tree


    controll_variable.add(c_tree)
    for child_ts in trees:
        for child_t in child_ts:
            if (child_t in controll_variable):
                controll_variable.remove(child_t)




def build_symmetry_mapping(constraints):
    cs = [look_for_child_control_variable(cons) for cons in constraints]
    collections =[]
    for control_v in cs:
        index = 0
        while len(control_v) > 0:
            if len(collections) <= index:
                sym = set()
                collections.append(sym)
            else:
                sym = collections[index]
            sym.add(control_v.pop())
            index += 1

    for col in collections:
        sym_set = col
        for v in col:
            sym_res = control_var_sym.get(v, None)
            if sym_res is not None:
                sym_set = sym_set.union(sym_res)
        for v in col:
            control_var_sym[v] = sym_set

        new_constraint = [controll_varaible_eq_r[v] for v in col]
        build_symmetry_mapping(new_constraint)


def get_symmetry(assignments):
    new_constraint = set()
    for ass in assignments:
        sym_set = control_var_sym.get(ass, None)
        if sym_set is not None:
            new_con = Or(sym_set)
            if new_con not in new_constraint:
                new_constraint.add(Or(sym_set))
                continue
        new_constraint.add(ass)

    return list(new_constraint)

def symmetry_sub(formula):
    result =[]
    for f in formula:
        if f.is_symbol():
            convs = look_for_child_control_variable(f )
            res = get_symmetry(convs)
            f = substitute(f, dict([(con, res) for con, res in zip(convs,res)]))
        result.append(f)
    return result



from collections import Iterable
class illFormedFormulaException(Exception):
    pass

def _polymorph_args_to_tuple( args):
    """ Helper function to return a tuple of arguments from args.

    This function is used to allow N-ary operators to express their arguments
    both as a list of arguments or as a tuple of arguments: e.g.,
       And([a,b,c]) and And(a,b,c)
    are both valid, and they are converted into a tuple (a,b,c) """

    if len(args) == 1 and isinstance(args[0], Iterable):
        args = args[0]
    return list(tuple(args))

def encode(formula, assumption=False):
    if isinstance(formula, Property):
        return formula.encode(assumption)
    if isinstance(formula, Operator):
        res = formula.encode(assumption=assumption)
        if formula.subs is not None:
            for target, src in formula.subs.items():
                res = target.sym_subs(src, encode(res, assumption=assumption))
        return res
    else:
        return formula

def invert(formula):
    if isinstance(formula, Operator):
        res = formula.invert()
        res.subs = formula.subs
        return res
    else:
        return Not(formula)

def DNF(formula):
    dnfs = to_DNF(formula)
    return [AND(dnf)for dnf in dnfs]

def to_DNF(formula):
    if isinstance(formula, Operator):
        return formula.to_DNF()
    else:
        return [simplify(formula)]

def to_CNF(formula):
    if isinstance(formula, Operator):
        return formula.to_CNF()
    else:
        return [simplify(formula)]


def sub(formula, source, target):
    if isinstance(formula, Operator):
        formula.sub(source, target)
        return formula
    else:
        return target.sym_subs(source, formula)


def slicing(formula, actions, reverse=False):
    if isinstance(formula, Operator):
        return formula.slicing(actions, reverse = reverse)
    else:
        bounded_variables = []
        fb = get_free_variables(formula)
        for action in actions:
            bounded_variables += action.get_all_variables()

        if len(set(fb) - set(bounded_variables)) == 0:
            if reverse:
                return None
            else:
                return formula
        else:
            if reverse:
                return formula
            else:
                return None


#happen before
def HB(action1, action2, strict=False):
    if strict:
        operator = LT
    else:
        operator = LE

    return operator(action1.time, action2.time)

def Equal_attr(action1, action2, a1, a2=None):
    if a2 is None:
        a2 = a1
    attr1  = getattr(action1, a1)
    attr2 = getattr(action2, a2)

    return Equals(attr1, attr2)

def Non_Equal_attr(action1, action2, a1, a2=None):
    if a2 is None:
        a2 = a1
    attr1  = getattr(action1, a1)
    attr2 = getattr(action2, a2)

    return NOT(Equals(attr1, attr2))

def Equal_attrs(action1, action2, attr_map):
    constraint = []
    for key, value in attr_map.items():
        constraint.append(Equal_attr(action1, action2, key, value))
    return AND(constraint)

def Non_Equal_attrs(action1, action2, attr_map):
    constraint = []
    for key, value in attr_map.items():
        constraint.append(Non_Equal_attr(action1, action2, key, value))
    return AND(constraint)

def action_EQ_cons(action1, action2, eq_maps={}, non_eq_maps={}):
    return AND(Equal_attrs(action1, action2, eq_maps), Non_Equal_attrs(action1, action2, non_eq_maps))

def sequence_action(action_sequnece, upper_bound = None, lower_bound = Int(0), strict=False, non_exist =[]):
    cur_time = lower_bound
    pos_constraint = set()
    neg_constraint = set()

    if strict:
        operator = LT
    else:
        operator = LE

    first_time = True
    unattched_negs = []
    for i in range(len(action_sequnece)):
        action = action_sequnece[i]
        if action not in non_exist:
            if first_time:
                pos_constraint.add(LE(cur_time, action.time))
                first_time = False
            else:
                pos_constraint.add(operator(cur_time, action.time))

            for unattched_neg in unattched_negs:
                neg_constraint.add(operator(unattched_neg.time, action.time))
            unattched_negs.clear()
            cur_time = action.time

        else:
            if first_time:
                neg_constraint.add(LE(cur_time, action.time))
            else:
                neg_constraint.add(operator(cur_time, action.time))
            unattched_negs.append(action)

    if upper_bound is not None:
        pos_constraint.add(operator(cur_time, upper_bound))
        for unattched_neg in unattched_negs:
            neg_constraint.add(operator(unattched_neg.time, upper_bound))




    return AND(pos_constraint), AND(neg_constraint)

def create_abstraction(constraints, target):
    return lambda act: sub(constraints, act, target)

def create_power(actions, constraints,  prefix=[], reachable_path=[]):
    if actions == []:
        reachable_path.append(prefix)
        return
    else:
        for i in range(len(actions)):
            new_prifix = prefix.copy()
            action = actions[i]
            remaining_actions = actions[:i] + actions[i+1:]
            time_constraing = [HB(action, remaining_action) for remaining_action in remaining_actions]
            new_constraint = time_constraing + constraints
            if is_sat(And(new_constraint)):
                new_prifix = new_prifix + [action]
                create_power(remaining_actions, new_constraint, new_prifix, reachable_path)
            else:
                continue

def cleanup(actions, constraints):
    constraint = constraints[0]
    return [act for act in actions if act.context_dependent_variable(constraint) != []]


def find_ordering(actions, constraints):
    reachable_config = []
    actions= cleanup(actions, constraints)
    create_power(actions, constraints, prefix=[], reachable_path=reachable_config)
    return reachable_config


def find_contex_by_action(cnfs, actions):
    context_variables = []
    local_constraints = set()
    for action in actions:
        context_variables += action.get_all_variables()

    context_variables = set(context_variables)
    for cnf in cnfs:
        cnf_var =get_free_variables(cnf)
        if len(set(cnf_var) - context_variables) == 0:
            local_constraints.add(cnf)


    return  local_constraints

def compose_attackcase(*attacks):
    attacks = _polymorph_args_to_tuple(attacks)
    context_map = dict()
    if (len(attacks) == 1):
        context_map = attacks[0].context_map
    else:
        for attack in attacks:
            merge_context_map(context_map, attack.context_map)
    composed_attack= AttackCase(None, None,None,None, None, context_map, sub_attackcases=attacks)
    composed_attack.push_down_context()
    return composed_attack

class AttackCase():
    def __init__(self , actions, constraints, context, exist_acts, non_exist_act, context_map, sub_attackcases=[] ):
        self.actions = actions
        self.constraints = constraints
        self.context  = context
        self.exist_acts = exist_acts
        self.non_exist_act = non_exist_act
        self.sub_attackcases = sub_attackcases
        self.context_map = context_map
        self.enable_header = True

    def push_down_context(self):
        for sub_attack in self.sub_attackcases:
            sub_attack.context_map = self.context_map
            sub_attack.enable_header = False
            sub_attack.push_down_context()

    def __str__(self):
        if self.enable_header:
            header = "\"{}\" = \n" \
                     "total rename".format("diag_1_fast.bcg" )
            tails = "in \"{}\" ".format("PDM.bcg")

            traits =[]
            for action_type, value in self.context_map.items():
                value = [att.upper() for att in value]
                key_locations = [key.upper() for key in action_type.attr_order]
                model_name, model_attribute = model_action_mapping.get(action_type.action_name, (action_type.action_name, ['ACTION'] + key_locations))
                included_attr = []
                included_indexed = []
                for m_attribute in model_attribute:
                    if m_attribute not in value:
                        included_attr.append("!.*")
                    else:
                        included_indexed.append(m_attribute)
                        included_attr.append("!Ids_of ({}, \([0-9]*\))".format(m_attribute))
                trait_body_first = "\"{} {} \"  ->\n".format(model_name, ' '.join(included_attr))
                arg_index = []
                for k in key_locations:
                    if k in included_indexed:
                        arg_index.append(included_indexed.index(k) + 1)
                trait_body_next = "\"{} {}\"".format(action_type.action_name.upper(),
                                                      ' '.join(['!\{}'.format(index) for index in arg_index]))
                trait = trait_body_first + trait_body_next
                traits.append(trait)
            headers = "{}\n{}\n{}\n".format(header,',\n'.join(traits), tails)
        else:
            headers = ""


        if self.sub_attackcases == []:
            generalized_trace = []
            prev = None
            for i in range(len(self.actions)):
                trace_item =""
                act = self.actions[i]
                local_constraint = self.constraints[i]
                if act in self.exist_acts:
                    if prev is None or prev not in self.non_exist_act:
                        trace_item += ("true*\n")
                    trace_item += (
                        "{{ {} where {} }}".format(act.print_with_context(self.context_map), serialize(local_constraint)))
                elif act in self.non_exist_act:
                    trace_item += ("(not({{ {} where {} }}))* ".format(act.print_with_context(self.context_map),
                                                                      serialize(local_constraint)))
                generalized_trace.append(trace_item)
                prev = act
            if prev is None or prev not in self.non_exist_act:
                generalized_trace.append("true*")
            generalized_trace = ' .\n'.join(generalized_trace)
             # generalized_trace += "where({})\n".format(serialize(constraints))
            generalized_trace = generalized_trace.replace("!", "not").replace("&", "and").replace("|", "or")
            generalized_trace = "([\n {} ]\n false;)".format(generalized_trace)
            return headers+ generalized_trace
        elif len(self.sub_attackcases) == 1:
            return headers + str(self.sub_attackcases[0])
        else:
            return headers + "({})".format(
                   "\n and \n".join(["{}".format(item) for item in self.sub_attackcases]))

def update_context_map(context_map, action, context):
    attribute_of_interests = action.extract_mentioned_attributes(context)
    action_type = type(action)
    res = context_map.get( action_type, set())
    res  = res.union(attribute_of_interests)
    context_map[action_type] = res
    return context_map

def merge_context_map(map1, map2):
    for key, value in map2.items():
        m1_value = map1.get(key, set())
        map1[key] = m1_value.union(value)


    return map1


def print_reachable_ordering(ordering, exists_actions, non_exist_actions, constraints, property_file = "diag_1_fast.bcg", model_file ="PDM.bcg"):
    cnfs = set(to_CNF(constraints))
    context =get_free_variables(encode(constraints))
    result = []
    for seq in ordering:
        considered =[]
        local_constraints = []
        context_map = dict()
        for act in seq:
            considered.append(act)
            context_clauses = find_contex_by_action(cnfs, considered)
            cnfs -= context_clauses
            local_constraint = encode(AND(context_clauses))
            local_constraints.append(local_constraint)
            context_map = update_context_map(context_map, act, context)

        #generalized_trace += "where({})\n".format(serialize(constraints))
        result.append(AttackCase(seq, local_constraints.copy(), context, exists_actions, non_exist_actions, context_map))
    return result

def determine_polarity(constraints, exists_actions):
    cnfs = to_CNF(constraints)
    pos = []
    neg = []
    bounded_variables = []
    for action in exists_actions:
        bounded_variables += action.get_all_variables()

    for cnf in cnfs:
        fb = get_free_variables(encode(cnf))
        if len(set(fb) - set(bounded_variables)) == 0:
            pos.append(cnf)
        else:
            neg.append(cnf)

    return pos, neg

def find_local_constraints(background_action, other_actions, constraints):
    cnfs = set(to_CNF(constraints))
    b_variables = []
    for b_action in background_action:
        b_variables += b_action.get_all_variables()

    background_set = set()
    s_bv = set(b_variables)
    for cnf in cnfs:
        fb = get_free_variables(encode(cnf))
        s_fb = set(fb)
        if (len(s_fb - s_bv) == 0):
            background_set.add(cnf)

    remaining_set = cnfs - background_set

    action_sets = []

    for action in other_actions:
        action_set = set()
        action_vars = set(action.get_all_variables())
        context_var = action_vars.union(s_bv)
        for cnf in remaining_set:
            fb = get_free_variables(encode(cnf))
            s_fb = set(fb)
            if (len(s_fb - context_var) == 0):
                action_set.add(cnf)
        remaining_set -= action_set
        action_sets.append(action_set)

    if len(remaining_set) > 0:
        print("warning: entangled variables constraints")

    return background_set, action_sets




def create_inv(exists_actions, neg_action_info, pos_constraints):
    total_circuits = []
    if neg_action_info == []:
        constraints = pos_constraints
        pos, neg = determine_polarity(constraints, exists_actions)
        circuit = _create_sequence(exists_actions.copy(), [], pos, neg)
        total_circuits.append(circuit)
    else:
        for neg_action, neg_conditions in neg_action_info:
            non_exist_actions = [neg_action]
            constraints = AND(pos_constraints, neg_conditions)
            pos, neg = determine_polarity(constraints, exists_actions)
            circuit = _create_sequence(exists_actions.copy(), non_exist_actions.copy(), pos, neg)
            total_circuits.append(circuit)
    return NOT(AND(total_circuits))



def create_sequence(exists_actions, neg_action_info, pos_constraints, comment=""):
    # first create the generalized representation
    total_property = []
    if neg_action_info == []:
        non_exist_actions = []
        constraints = pos_constraints
        dnfs = DNF(constraints)
        total_orderings = []
        total_sub_circuit = []
        for dnf in dnfs:
            dnf_constraints = encode(dnf)
            orderings = find_ordering(exists_actions + non_exist_actions, [dnf_constraints])
            for ordering in orderings:
                ordering_constraint = AND(sequence_action(ordering, non_exist=non_exist_actions))
                dnf_pos, dnf_neg = determine_polarity(AND(dnf, ordering_constraint), exists_actions)
                sub_circuit = _create_sequence(exists_actions.copy(), non_exist_actions.copy(), dnf_pos, dnf_neg)
                total_sub_circuit.append(sub_circuit)
            # total_orderings += orderings
            total_orderings += print_reachable_ordering(orderings, exists_actions, non_exist_actions, dnf)
        pos, neg = determine_polarity(constraints, exists_actions)
        circuit = _create_sequence(exists_actions.copy(), non_exist_actions.copy(), pos, neg)
        total_property.append(
            Property(circuit, lessons=total_orderings, lesson_circuits=total_sub_circuit, natural_language=comment))
    else:
        for neg_action, neg_conditions in neg_action_info:
            non_exist_actions = [neg_action]
            constraints = AND(pos_constraints, neg_conditions)
            dnfs = DNF(constraints)
            total_orderings = []
            total_sub_circuit = []
            for dnf in dnfs:
                dnf_constraints = encode(dnf)
                orderings = find_ordering(exists_actions + non_exist_actions, [dnf_constraints])
                for ordering in orderings:
                    ordering_constraint = AND(sequence_action(ordering, non_exist=non_exist_actions))
                    dnf_pos, dnf_neg = determine_polarity(AND(dnf, ordering_constraint) , exists_actions)
                    sub_circuit = _create_sequence(exists_actions.copy(), non_exist_actions.copy(), dnf_pos, dnf_neg)
                    total_sub_circuit.append(sub_circuit)
                #total_orderings += orderings
                total_orderings += print_reachable_ordering(orderings, exists_actions, non_exist_actions, dnf)

            pos, neg = determine_polarity(constraints, exists_actions)
            circuit =  _create_sequence(exists_actions.copy(), non_exist_actions.copy(), pos, neg)
            total_property.append(Property(circuit, lessons=total_orderings, lesson_circuits = total_sub_circuit, natural_language=comment))
    if len(total_property) > 1:
        return parallel_compo_properties(total_property)
    else:
        return total_property[0]

def lift_negative_constraints(non_exist_actions, neg_constraint):
    if non_exist_actions != []:
        act = non_exist_actions.pop()
        #local, outter = find_local_constraints(neg_constraint, non_exist_actions)
        expression = lift_negative_constraints(non_exist_actions, neg_constraint)
        return forall(type(act), create_abstraction(expression, act))
    else:
        return neg_constraint

def lifted_positive_constraints(exists_actions, pos_constraint):
    if exists_actions != []:
        act = exists_actions.pop()
        expression = lifted_positive_constraints(exists_actions, pos_constraint)
        return exist(type(act), create_abstraction(expression, act))
    else:
        return pos_constraint

def _create_sequence(exists_actions, non_exist_actions, pos_constraint, neg_constraint):
    if neg_constraint == []:
        lifted_negative = TRUE()
    else:
        lifted_negative = lift_negative_constraints (non_exist_actions, NOT(AND(neg_constraint)))
    pos_constraint = AND(pos_constraint + [lifted_negative])
    return lifted_positive_constraints(exists_actions, pos_constraint)

def exist(Action_Class, func):
    return Exists(Action_Class, Function(func))

def forall(Action_Class, func):
    return Forall(Action_Class, Function(func))

def Implication(l, r):
    return OR(NOT(l), r)

class Operator():
   def __init__(self):
       self.subs = {}

   def encode(self, assumption= False):
       return

   def invert(self):
       return self

   def sub(self, source, target):
       if self.subs is None:
            self.subs = {target: source}
       else:
            self.subs.update({target: source})

   def to_DNF(self):
       pass

   def to_CNF(self):
       pass

   def slicing(self, actions, reverse = False):
       pass

def NOT(arg, polarity = True):
    if arg is None or arg == []:
        return TRUE()
    else:
        return C_NOT(arg, polarity)


class C_NOT(Operator):
    def __init__(self, arg, polarity=True):
        super().__init__()
        self.arg = arg
        self.polarity = polarity

    def encode(self, assumption=False):
        if self.polarity:
            return encode(invert(self.arg), assumption=assumption)
        else:
            return encode(self.arg, assumption=assumption)

    #if invert the not, then you get the argument
    def invert(self):
        self.polarity = not self.polarity
        return self

    def to_DNF(self):
        if self.polarity:
            return to_DNF(invert(self.arg))
        else:
            return to_DNF(self.arg)

    def to_CNF(self):
        if self.polarity:
            return to_CNF(invert(self.arg))
        else:
            return to_CNF(self.arg)

    def slicing(self, actions, reverse = False):
        if self.polarity:
            return slicing(invert(self.arg), actions, reverse = reverse)
        else:
            return slicing(self.arg, actions, reverse = reverse)

    def generalize_encode(self, context=[]):
        return encode(self)

def AND( *args):
    c_args = _polymorph_args_to_tuple(args)
    if c_args == [] or args is None:
        return TRUE()
    else:
        return C_AND(c_args)


class C_AND(Operator):
    def __init__(self, *args):
        super().__init__()
        self.arg_list = _polymorph_args_to_tuple(args)

    def encode(self, assumption=False):
        result_list =[]
        for arg in self.arg_list:
            result_list.append(encode(arg, assumption=assumption))
        return And(result_list)


    def invert(self):
        arg_list = []
        for arg in self.arg_list:
            arg_list.append(invert(arg))
        return OR(arg_list)

    def to_DNF(self):
        sub_DNFS = [to_DNF(arg) for arg in self.arg_list ]
        dnfs = []
        for sub_dnf in sub_DNFS:
            if dnfs == []:
                dnfs = sub_dnf
            else:
                if sub_dnf == []:
                    continue
                else:
                    temp = []
                    for dnf in dnfs:
                        for sub in sub_dnf:
                            temp.append(AND(dnf, sub))
                    dnfs  = temp
        return dnfs

    def to_CNF(self):
        res = []
        for arg in self.arg_list:
            res += to_CNF(arg)
        return res

    def slicing(self, actions, reverse = False):
        sub_slices = [slicing(arg, actions, reverse = reverse) for arg in self.arg_list]
        sub_slices = [res for res in sub_slices if res is not None]
        return AND(sub_slices)

def OR( *args):
    c_args = _polymorph_args_to_tuple(args)
    if c_args == [] or args is None:
        return FALSE()
    else:
        return C_OR(c_args)


class C_OR(Operator):
    def __init__(self, *args):
        super().__init__()
        self.arg_list = _polymorph_args_to_tuple(args)

    def encode(self, assumption=False):
        result_list =[]
        for arg in self.arg_list:
            result_list.append(encode(arg, assumption=assumption))
        if assumption:
            return _OR(result_list)
        else:
            return Or(result_list)

    def invert(self):
        arg_list = []
        for arg in self.arg_list:
            arg_list.append(invert(arg))
        return AND(arg_list)

    def to_DNF(self):
        res = []
        for arg in self.arg_list:
            res += to_DNF(arg)
        return res


    def to_CNF(self):
        sub_CNFS = [to_CNF(arg) for arg in self.arg_list ]
        cnfs = []
        for sub_cnf in sub_CNFS:
            if cnfs == []:
                cnfs = sub_cnf
            else:
                if sub_cnf == []:
                    continue
                else:
                    temp = []
                    for cnf in cnfs:
                        for sub in sub_cnf:
                            temp.append(OR(cnf, sub))
                    cnfs  = temp
        return cnfs

    def slicing(self, actions, reverse=False):
        sub_slices = [slicing(arg, actions, reverse = reverse) for arg in self.arg_list]
        sub_slices = [res for res in sub_slices if res is not None]
        return OR(sub_slices)


class Function(Operator):

    def __init__(self, procedure, polarity= True):
        #create an concrete input based_on the type
        super().__init__()
        self.procedure = procedure
        self.polarity = polarity
        self.evaulated = []

    def evaulate(self, input, assumption=False):
        if self.polarity:
           res= self.procedure(input)
        else:
            res= invert(self.procedure(input))
        if assumption:
            self.evaulated.append(res)
        return res

    #check the slide effects
    def invert(self):
        return Function(self.procedure, polarity= not self.polarity)

class Exists(Operator):

    def __init__(self, input_type, func):
        super().__init__()
        if not isinstance(func, Function):
            raise illFormedFormulaException("Exists: {} is not a Function".format(func))
        self.input_type = input_type
        self.func = func


    def encode(self, assumption=False):
        constraint = []
        # base construction
        branch_coverage = True
        if branch_coverage:
            action = self.input_type(temp = True)
            base_constraint = AND(self.func.evaulate(action, assumption=assumption), action.presence).encode(
                assumption=assumption)
            choice_list = []
            for t_action in self.input_type.collect_list:
                choice_list.append(action.build_eq_constraint(t_action))
            if assumption:
                choice_constraint = Or(choice_list)
            else:
                choice_constraint = Or(choice_list)

            return And(base_constraint, choice_constraint)

        else:
            for action in self.input_type.collect_list:
                base_constraint = AND(self.func.evaulate(action, assumption=assumption), action.presence).encode(assumption=assumption)
                constraint.append(base_constraint)

            if assumption:
                res = _OR(constraint)
                build_symmetry_mapping(res.args())
                return res
            else:
                return OR(constraint).encode(assumption=assumption)

    def invert(self):
        return Forall(self.input_type, invert(self.func))

    def generalize_encode(self):
        action = self.input_type(temp=True)
        return

    def to_DNF(self):
        raise NotImplementedError("DNF for quantified formula is not ready")


class Forall(Operator):

    def __init__(self, input_type, func):
        super().__init__()
        if not isinstance(func, Function):
            raise illFormedFormulaException("Exists: {} is not a Function".format(func))
        self.input_type = input_type
        self.func = func


    def encode(self, assumption = False):
        constraint = []
        # base construction
        r = None
        action_temp = None
        #if assumption, we also want to test weather there exists any action in the log
        for action in self.input_type.collect_list:
            base_constraint = encode(Implication(action.presence, AND(action.presence, self.func.evaulate(action))) ,  assumption = assumption)
            constraint.append(base_constraint)
        '''
        if assumption:
            build_symmetry_mapping(constraint)
            card_sum = Plus([obj.card for obj in self.input_type.collect_list])
            constraint.append(OR(Equals(card_sum, Int(0)), GT(card_sum, Int(0)) ))
        '''


        return encode(AND(constraint), assumption=assumption)

    def invert(self):
        return Exists(self.input_type, invert(self.func))

    def to_DNF(self):
        raise NotImplementedError("DNF for quantified formula is not ready")




def create_control_variable(arg):
    s = controll_varaible_eq.get(arg)
    if s is None:
        s = Symbol("control_v_{}".format(len(raw_control_variable)))
        raw_control_variable.add(s)
    return s



def _OR(*args):
    arg_list = _polymorph_args_to_tuple(args)
    if len(arg_list) == 0:
        return FALSE()
    if len(arg_list) == 1:
        return arg_list[0]
    if TRUE() in arg_list:
        return TRUE()
    filtered_args = [arg for arg in arg_list if arg != FALSE()]
    control_sym = [create_control_variable(arg) for arg in filtered_args]
    build_tree(control_sym, filtered_args)
    return Or(control_sym)


def eq_class_constraint(Action_class,  rule, assumption):
    eq_classes = Action_class.EQ_CLASS
    length = len(eq_classes)
    index = 0
    constraints = []
    while index < length:
        eq_class = eq_classes[index]
        if len(eq_class) > 0:
            action = eq_class.pop()
            eq_classes.append(set([action]))
            constraints.append(And(action.presence, rule(action)))
        index += 1
    return _OR(constraints)




def Exist(Action_Class, rule, assumption=False):
    if assumption:
        return eq_class_constraint(Action_Class, rule, assumption)
    else:
        constraint = []
        for action in Action_Class.collect_list:
            constraint.append(And(action.presence, rule(action)))

    return Or(constraint)


def ForAll(Action_Class, rule):
    constraint = []
    for action in Action_Class.collect_list:
        constraint.append(Implies(action.presence, rule(action)))
    return And(constraint)


def curry(func):
    # to keep the name of the curried function:
    curry.__curried_func_name__ = func.__name__
    f_args, f_kwargs = [], {}
    def f(*args, **kwargs):
        nonlocal f_args, f_kwargs
        if args or kwargs:
            f_args += args
            f_kwargs.update(kwargs)
            return f
        else:
            result = func(*f_args, *f_kwargs)
            f_args, f_kwargs = [], {}
            return result
    return f

def get_assumption_constraints():
    #get assumption constraint:
    constraint = []
    for key, val in controll_varaible_eq.items():
        res = Iff(key, val)
        constraint.append(res)
        cs.traverse_solver.add_assertion(res)

    return And(constraint)

def composition(lol, current, collections, func= None):
    if lol == []:
        if func is not None:
            current = func(current)
        collections.append(current)
    else:
        head = lol[0]
        rst = lol[1:]
        for item in head:
            composition(rst, current + [item], collections, func=func)




def parallel_compo_properties( *properties):
    properties = _polymorph_args_to_tuple(properties)
    #perform parellel composition of the property
    circuit = AND([p.circuit for p in properties])
    natural_language = []
    all_lessons = []
    all_lesson_circuit = []
    for p in properties:
        all_lessons.append(p.lessons)
        all_lesson_circuit.append(p.lessons_circuits)
        natural_language.append(p.natural_language)

    composed_lesson =[]
    composed_lesson_circuit = []
    composition(all_lessons, [], composed_lesson, func= lambda lst: compose_attackcase(lst))
    composition(all_lesson_circuit, [], composed_lesson_circuit, func =AND)

    natural_language = '\n parellel composed \n'.join(natural_language)
    return Property(circuit, composed_lesson, composed_lesson_circuit, natural_language)


def merge_properties( *properties):
    properties = _polymorph_args_to_tuple(properties)
    circuit = OR([p.circuit for p in properties])
    lessons = []
    lessons_circuits = []
    natural_language = []
    for p in properties:
        lessons += p.lessons
        lessons_circuits += p.lessons_circuits
        natural_language.append(p.natural_language)
    natural_language = '\n'.join(natural_language)
    return Property(circuit, lessons, lessons_circuits, natural_language)


class Property():

    def __init__(self, circuit, lessons =[], lesson_circuits =[], natural_language=""):
        self.circuit = circuit
        self.lessons = lessons
        self.lessons_circuits = lesson_circuits
        self.natural_language = natural_language
        self.attack_scenarios = []
        self.attack_model = []

    def encode(self, assumption=False):
        return encode(self.circuit, assumption)

    def model_project(self):
        lessons = []
        for model in self.attack_model:
            model_constraint = And([EqualsOrIff(var, v) for var, v in model])
            sub_cir_index =0

            while sub_cir_index in range(len(self.lessons_circuits)):
                sub_cir = self.lessons_circuits[sub_cir_index]
                if is_sat(And(encode(sub_cir), model_constraint)):
                    lessons.append(self.lessons[sub_cir_index])
                    break
                sub_cir_index += 1
        return lessons

    def __repr__(self):
        line = "\n" + "-" * 100 + "\n"
        content_list = []
        content_list.append("")
        content_list.append("Property")
        content_list.append(self.natural_language)
        content_list.append("Realist attack scenarios")
        content_list += self.attack_scenarios
        res = line.join(content_list)
        return (res)


    def attack(self, inv_constraint, assumption=False):
        with Solver("z3", unsat_cores_mode="named") as s:
            # s.set(unsat_core=True)
            s.add_assertion(inv_constraint)
            s.add_assertion(encode(AND(learned_inv)))
            attack = self.encode(assumption=assumption)
            s.add_assertion(get_assumption_constraints())
            print(serialize(simplify(attack)))
            s.add_assertion(attack)
            cs.attack(s)
        print(cs.walked)
        print(cs.models)
        self.attack_scenarios += cs.attack_trace
        self.attack_model += cs.attack_model
        cs.attack_trace = []
        cs.attack_model = []
        cs.walked_set = []
        cs.walked = 0

