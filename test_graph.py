from LTS_generator import generate_LTS
import os.path
from shutil import copyfile


def run_experiment(target_directory, num_of_test):
    global PropertyNUM
    #copy the tgvrenmae
    src =  os.path.join(os.getcwd(), "tgv.rename")
    target =  os.path.join(os.getcwd(), target_directory,  "tgv.rename")
    copyfile(src, target)

    # change the current working directory
    target_directory = os.path.join(os.getcwd(), target_directory)

    os.chdir(target_directory)
    for i in range(num_of_test):
        target_file = os.path.join(os.getcwd(), target_directory, "purpose_{}.sh".format(i))
        os.system("chmod u+x {file}".format(file=target_file))
        os.system("{file}".format(file=target_file))
        print("-----------------------------------------------------------------")

if __name__ == "__main__":
    #file name, #num of action, #argument bound, #time progression bound, #shared action bound #LTS math depth, #shared ratio
    result_dir = "LTS_folder"
    N = 5
    '''
    for i in range(N):
        generate_single_LTS("grah_{}.aut".format(i), 2, [2, 2], 2, 1, 2, b_shared_ratio=0.1)
    '''
    #generate_LTS(target_directory, N, b_action, b_var, b_time, b_shared, b_depth, b_shared_ratio = -1):
    property_num  = 10
    generate_LTS(result_dir, 3, 2, [5,5,5], 1, 2, 10, b_shared_ratio = 0.1, ring_sync=False, property_num=property_num)
    run_experiment(result_dir, property_num)
    #generate_LTS(result_dir, 3, 2, [5, 5], 1, 2, 10, b_shared_ratio=0.1, ring_sync=False)

