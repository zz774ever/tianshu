"""Check single-request history against each actual stress-batch history."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent

def diff(a, b):
    for i, (x, y) in enumerate(zip(a, b), 1):
        if x != y:
            return {'first_difference': i, 'reference': x, 'candidate': y}
    return {'exact': len(a) == len(b), 'lengths': [len(a), len(b)]}

single = {}
for device in ('nvidia', 's60'):
    rows = json.loads((root / f'japan-{device}-fp32head.json').read_text())
    assert len(rows) == 1
    single[device] = rows[0]
    batch = json.loads((root / f'stress-{device}-fp32head.json').read_text())
    matches = [r for r in batch if r['prompt'] == rows[0]['prompt']]
    assert len(matches) == 1
    print(device, 'single versus own batch:', diff(matches[0]['token_ids'], rows[0]['token_ids']))
assert single['nvidia']['prompt'] == single['s60']['prompt']
result = diff(single['nvidia']['token_ids'], single['s60']['token_ids'])
print('NVIDIA versus S60 single:', result)
(root / 'japan-probe-comparison.json').write_text(json.dumps(result, indent=2))
