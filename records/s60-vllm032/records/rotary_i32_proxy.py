import torch
import torch_gcu
from vllm.model_executor.layers.rotary_embedding.base import RotaryEmbedding
from vllm_fl.dispatch.backends.vendor.gcu.impl.inductor import apply_inductor_gcu_patch
apply_inductor_gcu_patch()
def rotate(p,q,k,c):
    return RotaryEmbedding.forward_static(p.to(torch.int32),q,k,128,128,c,True)
torch.manual_seed(42)
f=1/(1000000.0**(torch.arange(0,128,2)/128))
t=torch.outer(torch.arange(512),f)
c=torch.cat((t.cos(),t.sin()),-1).to('gcu',torch.bfloat16)
fn=torch.compile(rotate,fullgraph=True)
for n in (12,2):
    q=torch.randn(n,2048,device='gcu',dtype=torch.bfloat16)
    k=torch.randn(n,1024,device='gcu',dtype=torch.bfloat16)
    for offset in (0,1,7,19,100):
        p=(torch.arange(n,dtype=torch.int32)+offset).to('gcu')
        ref=RotaryEmbedding.forward_static(p,q,k,128,128,c,True)
        got=fn(p,q,k,c)
        print(n,offset,[(a.float()-b.float()).abs().max().item() for a,b in zip(got,ref)],flush=True)
