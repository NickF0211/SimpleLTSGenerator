from LTS_generator import generate_single_LTS
import os.path
if __name__ == "__main__":
    #file name, #num of action, #argument bound, #time progression bound, #shared action bound #LTS math depth, #shared ratio
    result_dir = "LTS_folder"
    N = 5
    for i in range(N):
        generate_single_LTS("grah_{}.aut".format(i), 2, [2, 2], 2, 1, 2, b_shared_ratio=0.1)


