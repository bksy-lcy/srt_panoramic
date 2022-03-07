import os


COOKED_TRACE_FOLDER = './train/'


def load_trace(cooked_trace_folder=COOKED_TRACE_FOLDER):
    cooked_files = os.listdir(cooked_trace_folder)
    all_cooked_time = []
    all_file_names = []
    for cooked_file in cooked_files:
        file_path = cooked_trace_folder + cooked_file
        cooked_time = []
        # print file_path
        with open(file_path, 'rb') as f:
            for line in f:
                parse = line.split()
                cooked_time.append(int(parse[0]))
        all_cooked_time.append(cooked_time)
        all_file_names.append(cooked_file)

    return all_cooked_time, all_file_names
