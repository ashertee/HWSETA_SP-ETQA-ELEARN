import os 
for x in os.walk(os.getcwd()):
    for b in x[2]:
        print(f'"data/{b}",')
