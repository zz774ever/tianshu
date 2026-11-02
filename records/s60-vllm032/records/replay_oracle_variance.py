from pathlib import Path
from types import SimpleNamespace
import torch
from vllm_fl.worker.runtime import _initialize_fl_runtime
_initialize_fl_runtime(0)
from oracle_variance_rms import forward
root=Path(__file__).resolve().parent
key='model.layers.6.post_attention_layernorm'
d=torch.load(root/'layers-japan-rms-context.pt',map_location='cpu',weights_only=True)[key]
x,r=d['input']; w=d['context']['weight']; eps=d['context']['epsilon']
v=(x.float()+r.float()).to(x.dtype).double()
ref=(v*torch.rsqrt(v.square().mean(-1,keepdim=True)+eps)*w.double()).to(x.dtype)
obj=SimpleNamespace(weight=w.to('gcu'),variance_epsilon=eps)
with torch.inference_mode():
    out,res=forward(obj,x.to('gcu'),r.to('gcu'))
    out=out.cpu();res=res.cpu()
print('oracle variance boundary',out[1,262].item(),'CPU64neq',int((out!=ref).sum()),'residual_exact',torch.equal(res,v.to(x.dtype)),flush=True)
assert torch.equal(out,ref)
