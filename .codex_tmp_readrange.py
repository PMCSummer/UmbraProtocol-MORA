import sys, pathlib 
p=pathlib.Path(sys.argv[1]);s=int(sys.argv[2]);e=int(sys.argv[3]);lines=p.read_text(encoding='utf-8').splitlines(); 
[print(f'{i+1}:{lines[i]}') for i in range(max(0,s-1), min(e, len(lines)))];
