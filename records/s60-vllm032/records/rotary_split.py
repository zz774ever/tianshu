import torch
import torch_gcu
from vllm.model_executor.layers.rotary_embedding.common import ApplyRotaryEmb
from vllm_fl.dispatch.backends.vendor.gcu.impl.inductor import apply_inductor_gcu_patch
apply_inductor_gcu_patch()
torch.manual_seed(42)
def select(cache,pos):
    return cache.index_select(0,pos)
def rotate(x,cs):
    c,s=cs.chunk(2,-1)
    return ApplyRotaryEmb.forward_static(x,c,s)
def report(name,a,b):
    d=(a.float()-b.float()).abs().cpu()
    print(name,'max',d.max().item(),'mean',d.mean().item(),flush=True)
freq=1.0/(1000000.0**(torch.arange(0,128,2)/128))
t=torch.outer(torch.arange(512),freq)
cache=torch.cat((t.cos(),t.sin()),-1).to('gcu',torch.bfloat16)
p=torch.arange(7,19).long().to('gcu')
x=torch.randn(12,16,128,device='gcu',dtype=torch.bfloat16)
cs=select(cache,p)
report('index_select',torch.compile(select,fullgraph=True)(cache,p),cs)
report('rotation_only',torch.compile(rotate,fullgraph=True)(x,cs),rotate(x,cs))
def mul(x,c):
    return x*c.unsqueeze(-2)
def mix(x,cs):
    c,s=cs.chunk(2,-1)
    x1,x2=x.chunk(2,-1)
    return torch.cat((x1*c.unsqueeze(-2)-x2*s.unsqueeze(-2), x2*c.unsqueeze(-2)+x1*s.unsqueeze(-2)),-1)
report('multiply',torch.compile(mul,fullgraph=True)(x[...,:64],cs[...,:64]),mul(x[...,:64],cs[...,:64]))
report('manual_rotation',torch.compile(mix,fullgraph=True)(x,cs),mix(x,cs))
