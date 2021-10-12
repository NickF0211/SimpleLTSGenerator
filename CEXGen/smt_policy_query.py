import actionPool
from CEXGen.constraint_solver import *
from CEXGen.logic_operator import *
from CEXGen.s_expr_converter import convert

constraint_map =  dict()
violation_map = dict()
coverage= "branch"

ACTION_count = dict()

def register_temp_action(Action):
    action = Action(temp = True)
    Action()
    return action

RTA = register_temp_action



def get_all_constraint():
    constraint = []
    all_objects = []
    for action in ACTION:
        all_objects += action.syn_collect_list

    for obj in all_objects:
        constraint += obj.constraint

    for _, value in constraint_map.items():
        constraint += list(value)

    sym_cons = symmtry_breaking_by_time_constraint()
    constraint.append(sym_cons)
    return And(constraint)

def symmtry_breaking_by_time_constraint():
    constraints = []
    for Action_Class in ACTION:
        cur_index = 0
        collections = Action_Class.syn_collect_list
        while (cur_index < len(collections)):
            cur_item = collections[cur_index]
            if (cur_index+1 < len(collections)):
                nex_item = collections[cur_index+1]
                constraints.append(LE(cur_item.time, nex_item.time))
                constraints.append(Implies(nex_item.presence, cur_item.presence))

            cur_index += 1
    return And(constraints)


def card_constraint(action_Class, lb, ub):
    if action_Class in ACTION:
        card_sum = Plus([obj.card for obj in action_Class.collect_list])
        card_sum_constraint = And(LE(card_sum, Int(ub)), GE(card_sum, Int(lb)))
        card_presence_constraint = And([obj.cardinality_constraint for obj in action_Class.collect_list])
        return And(And(card_presence_constraint), card_sum_constraint)







def unqiue_time_constraint():
    all_objects = []
    for action in ACTION:
        all_objects += action.collect_list
    constraints = []
    for obj1 in all_objects:
        for obj2 in all_objects:
            if obj1 != obj2:
                constraints.append(NotEquals(obj1.time, obj2.time))

    return And(constraints)

def get_violations(model):
    for rule, violation_lists in violation_map.items():
        print("violation for {}".format(rule))
        for obj in violation_lists:
            print(obj.get_record(model))


def init_actions(threshold):
    for action in ACTION:
        for _ in range(threshold):
            action()

def clear_actions(Action):
    #Action.collect_list.clear()
    Action.syn_collect_list.clear()

def clear_all_action():
    for Action in ACTION:
        clear_actions(Action)






def update_not_ownered():
    collect = RTA(Collect)
    update = RTA(Update)
    binding = action_EQ_cons(collect, update, {"pid": "pid", "pvalue":"pvalue" , "subject":"subject"})
    ordering = AND(sequence_action([collect, update], strict=True))
    all_constraints = AND(ordering, binding)

    b_actions = [update]
    f_actions = [collect]
    b_constraints, f_constraints = find_local_constraints(b_actions, f_actions, all_constraints)
    property = create_sequence(b_actions,
                               [(action, AND(cons)) for action, cons in zip(f_actions, f_constraints)],
                               AND(b_constraints),
                               comment="all collected data must have a purpose")
    return property



def access_without_authorize(usage):
    access = RTA(usage)
    revoke = RTA(Revoke)
    authorize = RTA(Authorize)
    o1p, o1n = sequence_action([revoke, authorize, access], strict = True, non_exist=[authorize])
    o2p, o2n = sequence_action([authorize, access], strict = True, non_exist=[authorize])
    r_a_binding = AND(action_EQ_cons(authorize, revoke, {"a1": "a1", "pid": "pid"}), action_EQ_cons(revoke, access, {"a1": "a1", "pid": "pid"}))
    a_a_binding = AND(action_EQ_cons(authorize, access, {"a1": "a1", "pid": "pid"}), Equals(authorize.permission, Int(1)))
    property1 = create_sequence([access, revoke], [(authorize, TRUE())],  AND(o1p, o1n, r_a_binding, a_a_binding))
    property2 = create_sequence([access], [(authorize, TRUE())], AND(o2p, o2n, a_a_binding))

    return merge_properties(property1, property2)



#ph: access of
def access_without_owning():
    wrong_access = RTA(Patient_Access)
    #owning data --> the data is proved by the patient
    collect = RTA(Collect)

    #(\collect(pid, s))  p_access(pid, s)
    value_constraint = action_EQ_cons(wrong_access, collect, {"pid": "pid", "subject": "subject"})
    seq_constraint = AND(sequence_action([collect, wrong_access], strict=True, non_exist=[collect]))

    b_actions = [wrong_access]
    f_actions = [collect]
    all_constraints= AND(value_constraint, seq_constraint)

    b_constraints, f_constraints = find_local_constraints(b_actions, f_actions, all_constraints)
    property = create_sequence(b_actions,
                               [(action, AND(cons)) for action, cons in zip(f_actions, f_constraints)],
                               AND(b_constraints),
                               comment="only the owner of the data can access it")
    return property




'''
property_4:
SEQ act_0:ACT_1 , (* \ act_1:ACT_0) , act_2:ACT_0
TIME
DATA (act_0.ARG_0) < (act_1.ARG_1)
'''

def genererated_property(seq_constraint,  data_constraint):
    actions = []
    exists_actions = []
    non_exists_actions = []
    for action_num, exists in seq_constraint:
        action = RTA(ACTION[action_num])
        actions.append(action)
        if exists:
            exists_actions.append(action)
        else:
            non_exists_actions.append(action)

    seq_constraint = AND(sequence_action(actions, strict=True, non_exist=non_exists_actions))
    all_constraints = AND(data_constraint, seq_constraint)
    data_constraint = convert(data_constraint)
    b_constraints, f_constraints = find_local_constraints(exists_actions, non_exists_actions, all_constraints)
    property = create_sequence(exists_actions,
                               [(action, AND(cons)) for action, cons in zip(non_exists_actions, f_constraints)],
                               AND(b_constraints),
                               comment="A generated property")
    return property


def sequence_time_constraint(seq, strict = False):
    index = 0
    constraints= []
    if (seq != []):
        constraints.append(GE(seq[0].time, Int(0)))
    while (index < len(seq) -1):
        action1 = seq[index]
        action2 = seq[index+1]
        constraints.append(HB(action1, action2, strict = strict))
        index += 1
    return And(constraints)

def do_attack(property, constraints):
    property.attack(constraints, assumption=False)
    generalized_trace = property.model_project()
    for i in range(len(property.attack_scenarios)):
        print(property.attack_scenarios[i])
        print(generalized_trace[i])
        print()



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # intialzation based on test scarino
    actions = []
    seq_constraints = sequence_time_constraint(actions)
    constraints = And(get_all_constraint(), seq_constraints)



# See PyCharm help at https://www.jetbrains.com/help/pycharm/

