import os
import torch
import torch_gcu
import torch.distributed as dist
from vllm.platforms import current_platform
from vllm_fl.distributed.device_communicators.flagcx import PyFlagcxCommunicator

rank = int(os.environ['LOCAL_RANK'])
torch.gcu.set_device(rank)
dist.init_process_group('gloo')
comm = PyFlagcxCommunicator(dist.group.WORLD, torch.device(f'gcu:{rank}'))
assert comm.available and not comm.disabled, getattr(comm, 'init_error', 'disabled')
x = torch.full((16,), rank + 1.0, device=f'gcu:{rank}')
y = comm.all_reduce(x)
torch.gcu.synchronize()
assert torch.equal(y.cpu(), torch.full((16,), 3.0)), y.cpu()
print(f'FLAGCX_REAL_ALLREDUCE rank={rank} result={y.cpu().tolist()}', flush=True)
dist.destroy_process_group()
