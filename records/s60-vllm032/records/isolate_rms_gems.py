"""Controlled identical-data comparison before/after global FlagGems enable."""
from pathlib import Path
import torch
root=Path(__file__).resolve().parent
key='model.layers.6.post_attention_layernorm'
data=torch.load(root/'layers-japan-rms-context.pt',map_location='cpu',weights_only=True)[key]
x,r=(v.to('gcu') for v in data['input']); w=data['context']['weight'].to('gcu')
def stages():
    vals={}
    vals['sum']=(x.float()+r.float()).to(x.dtype)
    vals['square']=vals['sum'].float().square()
    vals['mean']=vals['square'].mean(-1,keepdim=True)
    vals['eps']=vals['mean']+1e-6
    vals['rsqrt']=torch.rsqrt(vals['eps'])
    vals['normalized']=vals['sum'].float()*vals['rsqrt']
    vals['weighted']=vals['normalized']*w.float()
    vals['cast']=vals['weighted'].to(x.dtype)
    return {k:v.cpu() for k,v in vals.items()}
a=stages()
from vllm_fl.worker.runtime import _initialize_fl_runtime
_initialize_fl_runtime(0)
b=stages()
for k in a:
    delta=a[k].float()-b[k].float()
    print(k,'neq',int((a[k]!=b[k]).sum()),'max',delta.abs().max().item(),flush=True)
    if k in ('mean','rsqrt','weighted','cast'):
        print('row1',k,a[k][1].flatten()[:3].tolist(),b[k][1].flatten()[:3].tolist(),flush=True)
torch.save({'native':a,'gems':b},root/'rms-gems-stages.pt')
