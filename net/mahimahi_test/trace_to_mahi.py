import os
import math

parts = ['test', 'train']

for part in parts:
    path1 = './old_trace/'+part
    path2 = './trace/'+part
    traces = os.listdir(path1)
    for trace in traces:
        # print(trace)
        path11 = path1 + '/' + trace
        path22 = path2 + '/' + trace
        with open(path11) as old_f:
            with open(path22, 'w+') as new_f:
                lines = old_f.readlines()
                c_time = 0
                for t, line in enumerate(lines, 1):
                    n = float(line.split()[1])
                    n *= 1000000
                    n /= 8*1500
                    n = math.floor(n)
                    nn = n / 1000
                    nnn = 0
                    nnnn = 0
                    for i in range(1000):
                        nnn += nn
                        x = math.floor(nnn)-nnnn
                        nnnn += x
                        for xx in range(x):
                            new_f.write(str(c_time+i)+'\n')
                    c_time += 1000

