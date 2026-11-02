"""Cold replay of newest live capture, with explicit input-identity checks."""
from pathlib import Path
from types import SimpleNamespace
import torch
from vllm_fl.dispatch.backends.vendor.gcu.impl.normalization import rms_norm_gcu
import os
if os.environ.get('REPLAY_FL_RUNTIME'):
    from vllm_fl.worker.runtime import _initialize_fl_runtime
    _initialize_fl_runtime(0)
root=Path(__file__).resolve().parent
key='model.layers.6.post_attention_layernorm'
live=torch.load(root/'layers-japan-rms-context.pt',map_location='cpu',weights_only=True)[key]
old=torch.load(root/'layers-japan-prefill-single6.pt',map_location='cpu',weights_only=True)[key]
for i,(a,b) in enumerate(zip(live['input'],old['input'])):
    print('live versus old input',i,torch.equal(a,b),'neq',int((a!=b).sum()),flush=True)
obj=SimpleNamespace(weight=live['context']['weight'].to('gcu'),variance_epsilon=live['context']['epsilon'])
x,r=(t.to('gcu') for t in live['input'])
for precision in ('highest','high','medium'):
    torch.set_float32_matmul_precision(precision)
    with torch.inference_mode():
        y,_=rms_norm_gcu(obj,x,r)
        y=y.cpu()
    print('precision',precision,'versus live',int((y!=live['output'][0]).sum()),'value',y[1,262].item(),flush=True)
