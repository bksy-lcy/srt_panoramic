import os

file_path = '24Mbps.log'
new_path = './short_log/'+file_path
with open(file_path) as f:
    with open(new_path,'w+') as nf:
        lines = f.readlines()[5:]
        for line in lines:
            if line.split()[1]!='#':
                nf.write(line)
