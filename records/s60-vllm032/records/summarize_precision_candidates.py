import json
from pathlib import Path
root = Path(__file__).parent
for name in ('prefix-nvidia', 'prefix-s60', 'decode-nvidia', 'decode-s60'):
    path = root / (name + '.json')
    if not path.exists():
        print(name, 'PENDING')
        continue
    rows = json.loads(path.read_text())
    if name.startswith('prefix'):
        for r in rows:
            best = sorted(r['top'].items(), key=lambda x: x[1]['rank'])[:3]
            print(name, r['position'], r['selected'], best)
    else:
        for index, pos in ((2, 6), (4, 12)):
            r = rows[index]
            best = sorted(r['top'][pos].items(), key=lambda x: x[1]['rank'])[:3]
            print(name, pos + 1, r['token_ids'][pos], best)
