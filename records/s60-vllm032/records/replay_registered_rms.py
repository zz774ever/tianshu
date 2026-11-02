"""Real captured input: independent registered RMS, before/after FL runtime."""
from pathlib import Path
import torch
import torch_gcu
root=Path(__file__).resolve().parent
key='model.layers.6.post_attention_layernorm'
data=torch.load(root/'layers-japan-rms-context.pt',map_location='cpu',weights_only=True)[key]
x,r=data['input']; w=data['context']['weight']; eps=data['context']['epsilon']
v=(x.float()+r.float()).to(x.dtype)
v64=v.double()
ref=(v64*torch.rsqrt(v64.square().mean(-1,keepdim=True)+eps)*w.double()).to(x.dtype)
op=torch.ops.TRITON_GCU.demo.v0_rms_norm
vg=v.to('gcu'); wg=w.to('gcu')
for stage in ('cold','fl_runtime'):
    if stage=='fl_runtime':
        from vllm_fl.worker.runtime import _initialize_fl_runtime
        _initialize_fl_runtime(0)
    with torch.inference_mode():
        full=op(vg,wg,eps).cpu()
        row=op(vg[1:2],wg,eps).cpu()
    print(stage,'CPU64neq',int((full!=ref).sum()),'boundary',full[1,262].item(),'rowneq',int((row!=full[1:2]).sum()),flush=True)
