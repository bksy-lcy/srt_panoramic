with open('../one_trace/360Mbps', 'w+') as f:
    for i in range(1, 361):
        f.write(str(i)+'.0 360\n')