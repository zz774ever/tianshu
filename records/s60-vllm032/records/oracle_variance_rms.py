"""Diagnostic only: replace just RMS variance reduction with CPU FP64 oracle."""
import torch
from vllm.model_executor.layers.layernorm import RMSNorm
from vllm_fl.ops.layernorm import RMSNormFL


def forward(self, x, residual=None):
    dtype=x.dtype
    value=x.float()
    if residual is not None:
        residual=(value+residual.float()).to(dtype)
        value=residual.float()
    partial=getattr(self,'variance_size_override',None)
    v=value if partial is None else value[..., :partial]
    import os
    weighted=getattr(self,'pass_weight' if residual is None else 'pass_weight_add',True)
    if os.environ.get('S60_ORACLE_FULL') == '1':
        high=value.cpu().double()
        part=high if partial is None else high[..., :partial]
        result=high*torch.rsqrt(part.square().mean(-1,keepdim=True)+self.variance_epsilon)
        if weighted:
            result=result*self.weight.cpu().double()
        result=result.to(dtype).to(x.device)
    else:
        variance=v.cpu().double().square().mean(-1,keepdim=True).float().to(x.device)
        result=value*torch.rsqrt(variance+self.variance_epsilon)
        if weighted:
            result=result*self.weight.float()
        result=result.to(dtype)
    return result if residual is None else (result,residual)

for cls in (RMSNorm,RMSNormFL):
    cls.forward_native=forward
    cls.forward_oot=forward
    cls.forward_cuda=forward
print('CPU64 variance diagnostic installed',flush=True)
