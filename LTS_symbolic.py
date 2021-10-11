def build_graph(input_file):
    with open(input_file, 'r') as file:
        #skip the file line of the input file (the header)
        file.readline()
        res = file.readline()
        while (res):
            clean = res[1:-1]
            args = clean.split(',')


