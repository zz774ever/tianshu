"""Actual aligned first-layer QKV versus CPU float64 projection."""
from pathlib import Path
import torch
from safetensors import safe_open
root=Path('/workspace/s60-adaptation')
a,b=[torch.load(root/f'layers-{s}.pt',weights_only=True,map_location='cpu') for s in ('nvidia','s60-single-v2')]
name='model.layers.0.self_attn.qkv_proj'
x=a[name]['input'][0]
assert torch.equal(x,b[name]['input'][0])
with safe_open('/models/Qwen3-0.6B/model.safetensors',framework='pt',device='cpu') as f:
    w=torch.cat([f.get_tensor(f'model.layers.0.self_attn.{p}_proj.weight') for p in ('q','k','v')])
y=(x.double() @ w.double().T).to(x.dtype)
for side,record in [('nvidia',a),('s60',b)]:
    z=record[name]['output'][0]
    d=(y.float()-z.float()).abs()
    print(side,'shape',tuple(y.shape),'neq',torch.count_nonzero(d).item(),'max',d.max().item())
    bad=torch.nonzero(d)
    for i,j in bad[:10].tolist():
        print(i,j,'observed',z[i,j].item(),'oracle',y[i,j].item())
