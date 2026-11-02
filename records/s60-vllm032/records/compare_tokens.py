"""Report exact token agreement; target eager is NOT NVIDIA ground truth."""
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('reference')
parser.add_argument('candidate')
args = parser.parse_args()
a = json.load(open(args.reference))
b = json.load(open(args.candidate))
assert len(a) == len(b)
rows = []
for ref, candidate in zip(a, b):
    assert ref['prompt'] == candidate['prompt']
    x, y = ref['token_ids'], candidate['token_ids']
    first = next((i + 1 for i, (u, v) in enumerate(zip(x, y)) if u != v), None)
    same = x == y
    rows.append(dict(prompt=ref['prompt'], exact=same, reference_tokens=len(x),
                     candidate_tokens=len(y), first_mismatch=first))
print(json.dumps(rows, indent=2))
raise SystemExit(0 if all(row['exact'] for row in rows) else 1)
