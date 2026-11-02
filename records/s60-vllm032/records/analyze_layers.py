import argparse
import torch

p = argparse.ArgumentParser()
p.add_argument('reference')
p.add_argument('candidate')
a = p.parse_args()
x, y = [torch.load(path, weights_only=True, map_location='cpu') for path in (a.reference, a.candidate)]
assert torch.equal(x['input_ids'], y['input_ids']), 'Unaligned input IDs'
assert torch.equal(x['positions'], y['positions']), 'Unaligned positions'
print('Aligned actual input IDs', x['input_ids'].tolist())


def walk(u, v, key):
    if isinstance(u, torch.Tensor):
        assert isinstance(v, torch.Tensor) and u.shape == v.shape, key
        d = u.float() - v.float()
        print(key, 'shape', tuple(u.shape), 'exact', torch.equal(u, v),
              'max', d.abs().max().item(), 'rms', d.square().mean().sqrt().item())
    elif isinstance(u, dict):
        for k in u:
            walk(u[k], v[k], key + '/' + k)
    elif isinstance(u, (tuple, list)):
        for i, (z, w) in enumerate(zip(u, v)):
            walk(z, w, key + f'/{i}')
    else:
        assert u is v, key


for key in x:
    if key not in ('input_ids', 'positions'):
        walk(x[key], y[key], key)
