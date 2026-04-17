import pathlib  
p=pathlib.Path(r\"src/substrate/subject_tick/update.py\")  
print(p.read_bytes()[:4])  
