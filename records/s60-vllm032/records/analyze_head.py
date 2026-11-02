"""Read real head captures; report same-input CPU oracle and cross-device drift."""
import argparse
from pathlib import Path
import torch

p = argparse.ArgumentParser()
p.add_argument('reference')
p.add_argument('candidate')
a = p.parse_args()
for path in sorted(Path(a.reference).glob('head-*.pt')):
    other = Path(a.candidate) / path.name
    if not other.exists():
        continue
    x, y = (torch.load(f, map_location='cpu', weights_only=True) for f in (path, other))
    assert x['ids'] == y['ids']
    assert torch.equal(x['weight'], y['weight']), 'Candidate weights differ'
    print(path.name, 'shapes', tuple(x['hidden'].shape), tuple(y['hidden'].shape))
    for name, z in [('NV', x), ('S60', y)]:
        print(name, 'head_rounded_maxerr', (z['device'].double() - z['oracle_rounded'].double()).abs().max().item())
        print(name, 'device', z['device'].tolist())
        print(name, 'oracle', z['oracle'].tolist())
    # Scheduler rows/call counters are not identities. Do not compare hidden
    # states across devices until actual input IDs and positions are aligned.
