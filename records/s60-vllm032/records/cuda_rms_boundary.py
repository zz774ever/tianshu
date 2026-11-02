"""Replay actual S60 norm inputs on official NVIDIA vLLM custom ops."""
from pathlib import Path
import torch
import vllm._custom_ops as ops
root=Path(__file__).resolve().parent
key='model.layers.6.post_attention_layernorm'
data=torch.load(root/'layers-japan-rms-context.pt',map_location='cpu',weights_only=True)[key]
x,r=data['input'];w=data['context']['weight'];eps=data['context']['epsilon']
v=(x.float()+r.float()).to(x.dtype).double()
ref=(v*torch.rsqrt(v.square().mean(-1,keepdim=True)+eps)*w.double()).to(x.dtype)
for name,xx,rr in [('full',x,r),('row',x[1:2],r[1:2])]:
    xx=xx.cuda().clone();rr=rr.cuda().clone();ww=w.cuda()
    ops.fused_add_rms_norm(xx,rr,ww,eps)
    out=xx.cpu()
    reference=ref if name=='full' else ref[1:2]
    print(name,'boundary',out[1 if name=='full' else 0,262].item(),'CPU64neq',int((out!=reference).sum()),flush=True)
    torch.save(out,root/('rms-cuda-'+name+'.pt'))
