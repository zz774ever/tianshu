"""Inspect real GCU RMS registrations and the captured rounding boundary."""
from pathlib import Path
import torch
import torch_gcu

for name in sorted(torch._C._dispatch_get_all_op_names()):
    if 'rms' in name.lower() and not name.startswith('aten::'):
        base, dot, overload = name.partition('.')
        try:
            print('SCHEMA', torch._C._dispatch_find_schema_or_throw(base, overload).schema())
        except RuntimeError as error:
            print('SCHEMA_ERROR', name, str(error))
root = Path(__file__).resolve().parent
key = 'model.layers.6.post_attention_layernorm'
data = torch.load(root / 'layers-japan-rms-context.pt', map_location='cpu', weights_only=True)[key]
x, residual = data['input']
weight = data['context']['weight']
epsilon = data['context']['epsilon']
value = (x.float() + residual.float()).to(x.dtype).double()
reference = (value * torch.rsqrt(value.square().mean(-1, keepdim=True) + epsilon) * weight.double()).to(x.dtype)
print('CPU64 boundary', reference[1, 262].item(), 'live', data['output'][0][1, 262].item())
print('CPU64 mismatch count', int((reference != data['output'][0]).sum()))
