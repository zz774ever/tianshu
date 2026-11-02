import re
import sys
from pathlib import Path
lines = Path(sys.argv[1]).read_text(errors='replace').splitlines()
rows = []
for line in lines:
    if 'SUBGRAPH_DIFF' not in line:
        continue
    line = line[line.index('SUBGRAPH_DIFF'):]
    m = re.search(r'SUBGRAPH_DIFF (\d+) (\d+) (\d+) (\[.*?\]) max (\S+) mean (\S+) refmax (\S+)',line)
    if not m:
        continue
    g,c,o,shape,mx,mean,ref = m.groups()
    if int(o)==3:
        continue  # attention output allocation is uninitialized until attention
    try:
        ratio=float(mx)/max(float(ref),1e-8)
        rows.append((ratio, int(g),int(c),int(o),shape,mx,mean,ref))
    except ValueError:
        pass
print('rows',len(rows))
for row in sorted(rows,reverse=True)[:30]:
    print(row)
print('LAST')
for row in rows[-12:]:
    print(row)
