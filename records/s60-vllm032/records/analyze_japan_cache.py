"""Compare captured real histories and independently evaluate dense attention."""
from pathlib import Path
import torch
root = Path(__file__).resolve().parent
records = {side: torch.load(root/f'cache-japan-{side}.pt', map_location='cpu', weights_only=True)
           for side in ('single', 'batch')}
a,b = records.values()
for name in ('query', 'kv', 'output'):
    x,y = a[name],b[name]
    assert x.shape == y.shape, (name,x.shape,y.shape)
    delta=x.float()-y.float()
    print(name, list(x.shape), 'exact',torch.equal(x,y), 'max',delta.abs().max().item(),
          'neq',int((x!=y).sum()))
for t in range(a['kv'].shape[0]):
    x,y=a['kv'][t],b['kv'][t]
    if not torch.equal(x,y):
        print('KV differing position',t,'max',(x.float()-y.float()).abs().max().item(),
              'neq',int((x!=y).sum()))
for side,data in records.items():
    print(side,'metadata', {k:(v.tolist() if isinstance(v,torch.Tensor) else v)
                           for k,v in data['metadata'].items() if k not in ('block_table','scheduler_metadata')})
    q=data['query'].double().reshape(1,-1,data['kv'].shape[-1]//2)
    k,v=data['kv'].double().chunk(2,dim=-1)
    groups=q.shape[1]//k.shape[1]
    k=k.repeat_interleave(groups,dim=1)
    v=v.repeat_interleave(groups,dim=1)
    scores=torch.einsum('qhd,khd->hqk',q,k)*data['scale']
    ref=torch.einsum('hqk,khd->qhd',scores.softmax(dim=-1),v)
    actual=data['output'].reshape_as(ref)
    rounded=ref.to(actual.dtype)
    print(side,'CPU64 attention rounded mismatch',int((rounded!=actual).sum()),
          'max',(rounded.float()-actual.float()).abs().max().item())
