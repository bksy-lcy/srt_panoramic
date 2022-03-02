import os


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
                for t, line in enumerate(lines, 1):
                    n = float(line.split()[1])
                    n *= 1000000
                    n /= 8*1500
                    while n>0 :
                        new_f.write(str(t))
                        new_f.write('\n')
                        n -= 1

