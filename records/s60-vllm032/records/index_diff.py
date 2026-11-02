import torch
import torch_gcu
from vllm_fl.dispatch.backends.vendor.gcu.impl.inductor import apply_inductor_gcu_patch
apply_inductor_gcu_patch()
def select(c,p):
    return c.index_select(0,p)
for dtype in (torch.float32,torch.bfloat16):
    cpu=torch.arange(512*128,dtype=torch.float32).reshape(512,128).to(dtype)
    for itype in (torch.int64,torch.int32):
        p=torch.arange(7,19,dtype=itype)
        c=cpu.to('gcu'); g=p.to('gcu')
        oracle=select(cpu,p)
        for name,fn in [('eager',select),('compiled',torch.compile(select,fullgraph=True))]:
            out=fn(c,g).cpu()
            print(dtype,itype,name,'max',(out.float()-oracle.float()).abs().max().item(),'first',out[0,:8].tolist(),flush=True)
