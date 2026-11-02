"""Diagnostic only: CUDA fused RMS weight multiply rounding on actual model."""
import torch
from vllm.model_executor.layers.layernorm import RMSNorm


def forward(self, x, residual=None):
    dtype = x.dtype
    y = x.float()
    if residual is not None:
        y = y + residual.float()
    residual_out = y.to(dtype) if residual is not None else None
    if residual is not None and __import__('os').environ.get('S60_ROUND_RESIDUAL') == '1':
        y = residual_out.float()
    var_input = y if self.variance_size_override is None else y[..., :self.variance_size_override]
    y = y * torch.rsqrt(var_input.square().mean(-1, keepdim=True) + self.variance_epsilon)
    has_weight = self.pass_weight if residual is None else self.pass_weight_add
    if has_weight:
        y = y * self.weight.float()
    y = y.to(dtype)
    return y if residual is None else (y, residual_out)


from vllm_fl.ops.layernorm import RMSNormFL
for cls in (RMSNorm, RMSNormFL):
    cls.forward_native = forward
    cls.forward_oot = forward
    cls.forward_cuda = forward
print('SINGLE_ROUND_RMS diagnostic installed for upstream and FL dispatch', flush=True)
