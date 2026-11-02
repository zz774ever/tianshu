"""Align the complete genuine Japan prefix in independently scheduled prefills."""
from pathlib import Path
import argparse
import torch
p=argparse.ArgumentParser()
p.add_argument('--single',default='layers-japan-prefill-single.pt')
p.add_argument('--batch',default='layers-japan-prefill-batch.pt')
args=p.parse_args()
root=Path(__file__).resolve().parent
single=torch.load(root/args.single,map_location='cpu',weights_only=True)
batch=torch.load(root/args.batch,map_location='cpu',weights_only=True)
ids=single['input_ids']; positions=single['positions']
assert ids.tolist()==[3838,374,279,6722,315,6323,30,20678,264,2805,4226,13]
assert positions.tolist()==list(range(12))
starts=[i for i in range(batch['input_ids'].numel()-11)
        if torch.equal(batch['input_ids'][i:i+12],ids)
        and torch.equal(batch['positions'][i:i+12],positions)]
assert len(starts)==1, starts
start=starts[0]; n=ids.numel(); m=batch['input_ids'].numel()
print('Aligned entire12tokenprompt start',start,'batchtokens',m)

def walk(x,y,key):
    if isinstance(x,torch.Tensor):
        if x.ndim and x.shape[0]%n==0 and y.shape[0]%m==0 and x.shape[0]//n==y.shape[0]//m:
            factor=x.shape[0]//n
            y=y[start*factor:(start+n)*factor]
        assert x.shape==y.shape,(key,x.shape,y.shape)
        delta=x.float()-y.float()
        print(key,'exact',torch.equal(x,y),'neq',int((x!=y).sum()),'max',delta.abs().max().item())
        if x.ndim and x.shape[0]==n:
            for t in range(n):
                if not torch.equal(x[t],y[t]):
                    print('  position',t,'max',(x[t].float()-y[t].float()).abs().max().item())
    elif isinstance(x,dict):
        for k in x:walk(x[k],y[k],key+'/'+k)
    elif isinstance(x,(tuple,list)):
        assert len(x)==len(y)
        for i,(a,b) in enumerate(zip(x,y)):walk(a,b,key+'/'+str(i))
    else:assert x is y
for k in single:
    if k not in ('input_ids','positions'):walk(single[k],batch[k],k)
