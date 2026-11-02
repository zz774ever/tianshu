import torch
import torch_gcu
from vllm_fl.dispatch.backends.vendor.gcu.impl.inductor import apply_inductor_gcu_patch
apply_inductor_gcu_patch()
def f(c,p):
    return c.index_select(0,p.to(torch.int32))
c=torch.arange(512*128,dtype=torch.float32).reshape(512,128).to('gcu')
p=torch.arange(7,19,dtype=torch.int64).to('gcu')
o=torch.compile(f,fullgraph=True)(c,p).cpu()
print(o[:,0].tolist(),flush=True)
print(f(c,p).cpu()[:,0].tolist(),flush=True)
