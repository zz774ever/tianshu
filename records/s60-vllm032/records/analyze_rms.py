"""Compare actual aligned first norm against explicit rounding contracts."""
import torch
from safetensors import safe_open
from pathlib import Path
root = Path('/workspace/s60-adaptation')
a, b = [torch.load(root / f'layers-{s}.pt', weights_only=True, map_location='cpu') for s in ('nvidia','s60')]
x = a['model.embed_tokens']['output']
assert torch.equal(x, b['model.embed_tokens']['output'])
with safe_open('/models/Qwen3-0.6B/model.safetensors', framework='pt', device='cpu') as f:
    w = f.get_tensor('model.layers.0.input_layernorm.weight')
import json
eps = json.loads(Path('/models/Qwen3-0.6B/config.json').read_text())['rms_norm_eps']
for dtype in (torch.float32, torch.float64):
    z = x.to(dtype)
    norm = z * torch.rsqrt(z.square().mean(-1, keepdim=True) + eps)
    for mode in ('single','double'):
        out = ((norm*w.to(dtype)) if mode == 'single' else (norm.to(w.dtype)*w)).to(x.dtype)
        for side, data in [('NV',a),('S60',b)]:
            y = data['model.layers.0.input_layernorm']['output']
            d = (out.float()-y.float()).abs()
            print(dtype,mode,side,'neq',torch.count_nonzero(d).item(),'max',d.max().item())
