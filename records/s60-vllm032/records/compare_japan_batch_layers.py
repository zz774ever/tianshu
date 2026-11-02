"""Compare actual S60 single/batch Japan token at position24, not call ordinal."""
from pathlib import Path
import argparse
import torch
p = argparse.ArgumentParser()
p.add_argument('--single', default='layers-s60-japan14.pt')
p.add_argument('--batch', default='layers-s60-japan-batch.pt')
a = p.parse_args()
root = Path(__file__).resolve().parent
single = torch.load(root/a.single, weights_only=True, map_location='cpu')
batch = torch.load(root/a.batch, weights_only=True, map_location='cpu')
assert single['input_ids'].tolist() == [271] and single['positions'].tolist() == [24]
rows = ((batch['input_ids'] == 271) & (batch['positions'] == 24)).nonzero().flatten()
assert rows.numel() == 1, rows
row = rows.item()
count = batch['input_ids'].numel()
print('Aligned token271 position24: batch row',row,'of',count)

def walk(a,b,key):
    if isinstance(a,torch.Tensor):
        assert isinstance(b,torch.Tensor)
        if a.ndim and a.shape[0] == 1 and b.shape[0] == count:
            b = b[row:row+1]
        assert a.shape == b.shape, (key,a.shape,b.shape)
        delta = a.float()-b.float()
        print(key,'exact',torch.equal(a,b),'max',delta.abs().max().item(),
              'rms',delta.square().mean().sqrt().item())
    elif isinstance(a,dict):
        for k in a: walk(a[k],b[k],key+'/'+k)
    elif isinstance(a,(tuple,list)):
        assert len(a)==len(b)
        for i,(x,y) in enumerate(zip(a,b)): walk(x,y,key+'/'+str(i))
    else: assert a is b
for key in single:
    if key not in ('input_ids','positions'):
        walk(single[key],batch[key],key)
