import pathlib 
p=pathlib.Path('src/substrate/subject_tick/downstream_contract.py') 
t=p.read_text(encoding='utf-8') 
for i,l in enumerate(t.splitlines(),1): 
    ll=l.lower() 
    if 's01_' in ll or 'strong_self' in ll: 
        print(f'{i}:{l}') 
