"""Check local variance reduction on genuine captured RMS inputs."""
from pathlib import Path
import torch
root=Path(__file__).resolve().parent
key='model.layers.6.post_attention_layernorm'
data=torch.load(root/'layers-japan-rms-context.pt',map_location='cpu',weights_only=True)[key]
x,r=(v.to('gcu') for v in data['input'])
w=data['context']['weight'].to('gcu')
value=(x.float()+r.float()).to(x.dtype).float()
square=value.square()
native=square.mean(-1,keepdim=True).cpu()
from vllm_fl.worker.runtime import _initialize_fl_runtime
_initialize_fl_runtime(0)
for name,variance in [('mean',square.mean(-1,keepdim=True)),('sumdiv',square.sum(-1,keepdim=True)/square.shape[-1])]:
    out=(value*torch.rsqrt(variance+1e-6)*w.float()).to(x.dtype).cpu()
    cpu_value=value.cpu()
    ref=(cpu_value*torch.rsqrt(native+1e-6)*w.cpu().float()).to(x.dtype)
    print(name,'variance_neq_native',int((variance.cpu()!=native).sum()),'output_neq_native',int((out!=ref).sum()),'target',out[1,262].item(),flush=True)
