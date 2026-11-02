import torch
import torch_gcu
from vllm_fl.dispatch.backends.vendor.gcu.impl.inductor import apply_inductor_gcu_patch

# Same i32 indices and BF16 embedding + RMS arithmetic as the failed fusion.
apply_inductor_gcu_patch()
def f(ids, weight):
    x = torch.nn.functional.embedding(ids, weight)
    return x * torch.rsqrt(x.float().square().mean(-1, keepdim=True) + 1e-6)
ids = torch.tensor([0, 9, 17, 31], dtype=torch.int32, device='gcu')
w = torch.arange(32 * 1024, device='gcu', dtype=torch.float32).reshape(32, 1024).to(torch.bfloat16)
y = torch.compile(f, fullgraph=True)(ids, w)
torch.testing.assert_close(y.cpu(), f(ids, w).cpu(), rtol=0.02, atol=0.02)
print('GCU compiled i32 embedding/RMS proxy PASS')
