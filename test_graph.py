from LTS_generator import generate_LTS
import os.path
if __name__ == "__main__":
    #file name, #num of action, #argument bound, #time progression bound, #shared action bound #LTS math depth, #shared ratio
    result_dir = "LTS_folder"
    N = 5
    '''
    for i in range(N):
        generate_single_LTS("grah_{}.aut".format(i), 2, [2, 2], 2, 1, 2, b_shared_ratio=0.1)
    '''
    #generate_LTS(target_directory, N, b_action, b_var, b_time, b_shared, b_depth, b_shared_ratio = -1):
    generate_LTS(result_dir, 2, 2, [5,5], 1, 2, 10, b_shared_ratio = 0.1)



