"""Replay the actual first divergent RMSNorm with equal rows at different batch sizes."""
from pathlib import Path
from types import SimpleNamespace
import torch
from safetensors import safe_open
from vllm_fl.dispatch.backends.vendor.gcu.impl.normalization import rms_norm_gcu
root=Path(__file__).resolve().parent
key='model.layers.6.post_attention_layernorm'
records={s:torch.load(root/f'layers-japan-prefill-{s}6.pt',map_location='cpu',weights_only=True)
         for s in ('single','batch')}
with safe_open('/models/Qwen3-0.6B/model.safetensors',framework='pt',device='cpu') as f:
    weight=f.get_tensor(key+'.weight')
obj=SimpleNamespace(weight=weight.to('gcu'),variance_epsilon=1e-6)
outputs={}
for side,data in records.items():
    x,r=data[key]['input']; n=x.shape[0]
    start=0 if side=='single' else 43
    y,res=rms_norm_gcu(obj,x.to('gcu'),r.to('gcu'))
    y=y.cpu(); recorded=data[key]['output'][0]
    print(side,'native replay versus owncapture',torch.equal(y,recorded),'neq',int((y!=recorded).sum()),flush=True)
    outputs[side]=y[start:start+12]
    value=(x.float()+r.float()).to(x.dtype).float()
    for dtype in (torch.float32,torch.float64):
        val=value.to(dtype)
        ref=(val*torch.rsqrt(val.square().mean(-1,keepdim=True)+1e-6)*weight.to(dtype)).to(x.dtype)
        print(side,str(dtype),'oracle selected neq',int((ref[start:start+12]!=outputs[side]).sum()),flush=True)
    # Fix execution shape to one row while retaining all actual data.
    row_y,_=rms_norm_gcu(obj,x[start+1:start+2].to('gcu'),r[start+1:start+2].to('gcu'))
    row_y=row_y.cpu()
    print(side,'one-row versus batch row neq',int((row_y!=y[start+1:start+2]).sum()),flush=True)
    outputs[side+'_row']=row_y
print('single/batch',int((outputs['single']!=outputs['batch']).sum()),flush=True)
print('single/batch fixed1row',int((outputs['single_row']!=outputs['batch_row']).sum()),flush=True)
x,r=records['single'][key]['input']
xg,rg=x.to('gcu'),r.to('gcu')
base=None
for i in range(20):
    y,_=rms_norm_gcu(obj,xg,rg)
    yc=y.cpu()
    if base is None:base=yc
    print('repeat',i,'versusfirst',int((yc!=base).sum()),'versuscapture',int((yc!=records['single'][key]['output'][0]).sum()),flush=True)
print('input strides',x.stride(),r.stride(),xg.stride(),rg.stride(),flush=True)
with torch.inference_mode():
    for side,data in records.items():
        x,r=data[key]['input']
        y,_=rms_norm_gcu(obj,x.to('gcu'),r.to('gcu'))
        yc=y.cpu()
        print(side,'inference versus capture neq',int((yc!=data[key]['output'][0]).sum()),flush=True)
torch.save(outputs,root/'prefill-rms-replay.pt')
