from pathlib import Path
import torch
from safetensors import safe_open
root=Path(__file__).resolve().parent
key='model.layers.6.post_attention_layernorm'
data=torch.load(root/'layers-japan-rms-context.pt',map_location='cpu',weights_only=True)[key]
context=data['context']
print({k:v for k,v in context.items() if k!='weight'})
with safe_open('/models/Qwen3-0.6B/model.safetensors',framework='pt',device='cpu') as f:
    weight=f.get_tensor(key+'.weight')
print('live weight',context['weight'].dtype,'checkpoint',weight.dtype,'equal',torch.equal(context['weight'],weight))
x,r=data['input']; w=context['weight']; epsilon=context['epsilon']
value=(x.float()+r.float()).to(x.dtype).float()
ref=(value*torch.rsqrt(value.square().mean(-1,keepdim=True)+epsilon)*w.float()).to(x.dtype)
for name in ('output','repeat_actual','repeat_clone'):
    y=data[name][0]
    print(name,'versusCPUref',int((y!=ref).sum()),'versusoutput',int((y!=data['output'][0]).sum()))
    for idx in (y!=ref).nonzero().tolist()[:8]:
        print('diff',idx,'actual',y[tuple(idx)].item(),'ref',ref[tuple(idx)].item())
