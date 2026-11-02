"""Controlled real first-QKV GEMM replay, no modification of GT outputs."""
import torch
from safetensors import safe_open
record=torch.load('layers-nvidia.pt',weights_only=True,map_location='cpu')
name='model.layers.0.self_attn.qkv_proj'
x=record[name]['input'][0]
captured=record[name]['output'][0]
with safe_open('model/model.safetensors',framework='pt',device='cpu') as f:
    w=torch.cat([f.get_tensor(f'model.layers.0.self_attn.{p}_proj.weight') for p in ('q','k','v')])
oracle=(x.double()@w.double().T).to(x.dtype)
x,w=x.cuda(),w.cuda()
for reduction in (True,False):
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=reduction
    y=torch.nn.functional.linear(x,w).cpu()
    for label,z in [('captured',captured),('cpu64',oracle)]:
        d=(y.float()-z.float()).abs()
        print('reduced',reduction,'vs',label,'neq',torch.count_nonzero(d).item(),'max',d.max().item(),flush=True)
torch.set_float32_matmul_precision('highest')
for mode in ('fp32', 'separate_qkv'):
    if mode == 'fp32':
        y=torch.nn.functional.linear(x.float(),w.float()).to(x.dtype).cpu()
    else:
        y=torch.cat([torch.nn.functional.linear(x,z) for z in w.split([2048,1024,1024])],-1).cpu()
    for label,z in [('captured',captured),('cpu64',oracle)]:
        d=(y.float()-z.float()).abs()
        print(mode,'vs',label,'neq',torch.count_nonzero(d).item(),'max',d.max().item(),flush=True)
