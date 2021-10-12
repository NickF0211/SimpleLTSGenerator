from type_constructor import create_type, create_action, create_pair_action


num_action = 5
num_args = [1000, 1000, 1000]
time_range = 100000
type_dict = dict()

args = []
for i in range(len(num_args)):
    domain_up = num_args[i]
    args.append(create_type("arg_{}".format(str(i)), type_dict, lower_bound=0, upper_bound= domain_up))

time = create_type("time", type_dict, lower_bound=0, upper_bound=time_range)

ACTION = []
for i in range(num_action):
    ACTION.append(create_action("ACT_{}".format(i), [("time","time")] +
                  [("arg_{}".format(str(i)), "arg_{}".format(str(i))) for i in range(len(args))], type_dict))


ACTION_MAP = {}
for act in ACTION:
    ACTION_MAP[act.action_name.upper()] = act



