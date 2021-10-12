from pysmt.shortcuts import *
from pysmt import fnode

request_action_map = dict()
attribute_variable_map = dict()

exception_map = dict()

def get_variables_by_type(type_name):
    return attribute_variable_map.get(type_name, set())

def add_variable_by_type(type_name, variable):
    target = get_variables_by_type(type_name)
    target.add(variable)
    attribute_variable_map[type_name] = target

def get_action_name(action_id):
    if action_id == 1:
        return "access"
    elif action_id == 2:
        return "disclose"


class Action():
    presence_counter = 0
    sym_presence = Symbol("action_presence", typename=BOOL)

    def __init__(self):
        value = self.get_counter_update()
        self.presence = Symbol("action_presence_{}".format(value), typename=BOOL)
        self.card = Symbol("action_card_{}".format(value), typename=INT)
        self.cardinality_constraint = And(Iff(self.presence, Equals(self.card, Int(1))),
                                          Iff(Not(self.presence), Equals(self.card, Int(0))))
        self.sym_constraint = set()

    def get_counter_update(self):
        presence_counter = Action.presence_counter
        Action.presence_counter += 1
        return presence_counter

def create_type(type_name, type_dict = dict(), upper_bound=None, lower_bound=None):
    def constraint(var):
        constraint = []
        if not upper_bound is None:
            constraint.append(LE(var, Int(upper_bound)))
        if not lower_bound is None:
            constraint.append(GE(var, Int(lower_bound)))
        return And(constraint)

    type_dict[type_name] = constraint
    return type_name

def get_value_from_node(model, node):
    if isinstance(node, fnode.FNode):
        return model.get_py_value(node)
    else:
        return  node

def get_or_create(model, key, map, key_type):
    v_map = map.get(key_type, None)
    if v_map is None:
        return key
    else:
        inv_map = {get_value_from_node(model, v): k for k, v in v_map.items()}
        value = inv_map.get(key, None)
        if value is None:
            value = key
            v_map[value] = key

    return value

def create_pair_action(action_name, attributes, constraint_dict):
    action_new_name = "Requested_"+action_name
    action_class = create_action(action_name, attributes, constraint_dict)
    request_class = create_action(action_new_name, attributes, constraint_dict)
    request_action_map[action_class] = request_class
    request_action_map[request_class] = action_class
    return request_class, action_class

def create_action(action_name, attributes, constraint_dict, abstraction=True):
    index_map = dict([(att_name, 0) for att_name, attr_type in attributes])
    temp_index_map = dict([(att_name, 0) for att_name, attr_type in attributes])
    args_to_type = dict(attributes)
    attr_order = [attr_name for attr_name, _ in attributes]

    def __init__(self, permanent=True, temp = False):
        super(type(self), self).__init__()
        self.constraint = []
        for attr, attr_type in attributes:
            if temp:
                variable = Symbol("{}_{}_{}_temp".format(action_name, attr, self.get_index_update(attr)), typename=INT)
                setattr(self, attr, variable)
                #add_variable_by_type(attr_type, variable)

            else:
                variable = Symbol("{}_{}_{}".format(action_name, attr, self.get_index_update(attr)), typename=INT)
                setattr(self, attr, variable)
                if abstraction:
                    add_variable_by_type(attr_type, variable)
                type_constraint = constraint_dict.get(attr_type, lambda _: TRUE())
                self.constraint.append(type_constraint(getattr(self,attr)))

        if not temp:
            if permanent:
                type(self).syn_collect_list.append(self)
                type(self).EQ_CLASS[0].add(self)
            type(self).collect_list.append(self)

    def get_index_update(self, key, temp= False):
        if temp:
            target_map = type(self).temp_index_map
        else:
            target_map = type(self).index_map
        if (key not in  target_map.keys()):
            print("strange update")
            return
        res = target_map.get(key, 0)
        target_map[key] = res + 1
        return res

    def sym_subs(self, other, context):
        subs_dict = dict([(getattr(self, attr), getattr(other, attr)) for attr, _ in attributes ] + [(self.presence, other.presence)])
        return substitute(context, subs_dict)

    def build_eq_constraint(self, other):
        constraint = []
        for key in type(self).index_map.keys():
            constraint.append(EqualsOrIff(getattr(self, key), getattr(other, key)))
        constraint.append(EqualsOrIff(self.presence, other.presence))
        return And(constraint)

    def context_dependent_variable(self, conext):
        fb = get_free_variables(conext)
        dependent = []
        for attr, _ in attributes:
            if getattr(self, attr) in fb:
                dependent.append(getattr(self, attr))
        return dependent

    def get_all_variables(self):
        res = [ getattr(self, attr) for attr, _ in attributes]
        res.append(self.presence)
        return res


    def __repr__(self):
        pars = "({})".format(', '.join([str(getattr(self, attr)) for attr, _ in attributes if attr != "time"]))
        time_s = "@{time} {action_name}".format(time = self.time, action_name = action_name)
        return time_s+pars

    def print_with_context(self, context_map):
        interests = context_map.get(type(self), set())
        important_args = ["?{}:Nat".format(getattr(self, attr) ) for attr, _ in attributes if attr in interests]
        content = (' '.join(important_args)) if len(important_args) > 0 else  "..."
        pars = "{action_name} {content}".format(action_name = action_name.upper()   , content = content)
        #time_s = "@{time} {action_name}".format(time=self.time if self.time in context else "*", action_name=action_name)
        return pars

    def extract_mentioned_attributes(self, context):
        return  set([attr for attr, _ in attributes  if getattr(self, attr) in context])

    def get_record(self, model, debug=True):
        if debug:
            pars = "({})".format(', '.join(
                ["{}={}".format(str(getattr(self, attr)), str(model.get_py_value(getattr(self, attr)))) for attr, _ in attributes if
                 attr != "time"]))
            time_s = "@{time} {action_name} = {action_id} ".format(time=model.get_py_value(self.time), action_name=action_name, action_id = self.presence)
            return time_s + pars
        else:
            pars = "({})".format(', '.join(["{}={}".format(attr, str(model.get_py_value(getattr(self, attr)))) for attr, _ in attributes if attr != "time"]))
            time_s = "@{time} {action_name}".format(time=model.get_py_value(self.time), action_name=action_name)
            return time_s+pars


    def get_model_record(self, model, translation_map,  is_readable=False, is_abstract= False):
        def map(var):
            if is_abstract and var.is_symbol():
                name ="{}_abstracted".format(var.symbol_name())
                exists =  get_env().formula_manager.symbols.get(name, None)
                if  exists  is None:
                    return  var
                else:
                    return exists
            else:
                return var


        divider = ' ' if is_readable else ' !IDS_OF '
        time_divider = " " if is_readable else ' !IDS_OF '
        pars = "{})".format(divider.join(["({}, {})".format(attr.upper(),
                                                                 str(get_or_create(model, model.get_py_value(map(getattr(self, attr))),
                                                                                   translation_map,
                                                                                   type(self).args_to_type.get(attr)))) for attr, _ in attributes if attr != "time"]))
        time_s = "{action_name}{div1}(TIME, {time}){div2}".format(div1 = time_divider, div2= divider, time=model.get_py_value(map(self.time)), action_name=action_name)
        return time_s+pars


    action_class = type(action_name, (Action,),{
        "action_name": action_name,
        "args_to_type": args_to_type,
        "index_map": index_map,
        "temp_index_map": temp_index_map,
        "attr_order": attr_order,
        "collect_list" : [],
        "syn_collect_list": [],
        "additional_constraint" : [],
        "EQ_CLASS" : [set()],
        "Uncollected" : set(),
        "__init__": __init__,
        "get_index_update": get_index_update,
        "sym_subs": sym_subs,
        "context_dependent_variable": context_dependent_variable,
        "get_all_variables": get_all_variables,
        "__repr__": __repr__,
        "print_with_context": print_with_context,
        "extract_mentioned_attributes": extract_mentioned_attributes,
        "get_record": get_record,
        "get_model_record": get_model_record,
        "build_eq_constraint": build_eq_constraint
    })
    return action_class

def get_varaible(var):
    if var.is_symbol():
        return Symbol("{}_abstracted".format(var.symbol_name()), INT)
    else:
        res = exception_map.get(var, None)
        if res is not None:
            return res
        else:
            abstracted_symbol= Symbol("{}_abstracted".format(len(exception_map.keys())), INT)
            exception_map[var] = abstracted_symbol
            return abstracted_symbol



