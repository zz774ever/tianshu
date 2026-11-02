"""Compare decode runs and candidate margins at the first shared-history mismatch."""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('reference')
p.add_argument('candidate')
a = p.parse_args()
x = json.loads(Path(a.reference).read_text())
y = json.loads(Path(a.candidate).read_text())
assert len(x) == len(y)
rows = []
for r, t in zip(x, y):
    assert r['prompt'] == t['prompt']
    pos = next((i for i, (u, v) in enumerate(zip(r['token_ids'], t['token_ids'])) if u != v), None)
    row = {'prompt': r['prompt'], 'exact': r['token_ids'] == t['token_ids'],
           'first_mismatch': None if pos is None else pos + 1}
    if pos is not None:
        gt, target = str(r['token_ids'][pos]), str(t['token_ids'][pos])
        row.update(reference_token=int(gt), candidate_token=int(target))
        for name, source in [('reference', r), ('candidate', t)]:
            top = source['top'][pos]
            row[name] = {key: top.get(key) for key in (gt, target)}
            row[name]['top5'] = sorted(top.items(), key=lambda kv: kv[1]['rank'])[:5]
            if gt in top and target in top:
                row[name]['reference_minus_candidate_logprob'] = top[gt]['logprob'] - top[target]['logprob']
    rows.append(row)
print(json.dumps(rows, indent=2, ensure_ascii=False))
