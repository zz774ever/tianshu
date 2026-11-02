import json
from pathlib import Path
import torch
import torch_gcu
from vllm.model_executor.layers.rotary_embedding.common import ApplyRotaryEmb
from vllm_fl.dispatch.backends.vendor.gcu.impl.inductor import apply_inductor_gcu_patch
apply_inductor_gcu_patch()
torch.manual_seed(42)
def rotate(x, positions, cache):
    cos, sin = cache.index_select(0, positions).chunk(2, dim=-1)
    return ApplyRotaryEmb.forward_static(x, cos, sin)
freq = 1.0 / (1000000.0 ** (torch.arange(0,128,2,dtype=torch.float32)/128))
theta = torch.outer(torch.arange(512,dtype=torch.float32),freq)
cache = torch.cat((theta.cos(),theta.sin()),-1).to(device='gcu',dtype=torch.bfloat16)
compiled = torch.compile(rotate,fullgraph=True,dynamic=False)
rows=[]
for n in (12,2):
    x=torch.randn(n,16,128,device='gcu',dtype=torch.bfloat16)
    for offset in (0,1,7,19,100):
        pos=(torch.arange(n,device='cpu')+offset).long().to('gcu')
        ref=rotate(x,pos,cache).float().cpu()
        got=compiled(x,pos,cache).float().cpu()
        delta=(got-ref).abs()
        row={'shape':list(x.shape),'offset':offset,'max':delta.max().item(),'mean':delta.mean().item(),'refmax':ref.abs().max().item()}
        print(row,flush=True);rows.append(row)
Path('/workspace/s60-adaptation/rotary-diff.json').write_text(json.dumps(rows,indent=2))
