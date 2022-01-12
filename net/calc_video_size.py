import numpy as np
import os
file_path = '/home/lcy/ABR-5G/v_dash/kyoto_1/chunk-stream3-'

for i in range(1, 173):
    _file = file_path+'{0:0>5}.m4s'.format(i)
    file_size = os.stat(_file).st_size
    # print(_file, file_size)
    print(file_size)