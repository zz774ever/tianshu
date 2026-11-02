"""Diagnostic-only probability reporting: preserve device sampling, rank on CPU.

Imported at module scope so multiprocessing-spawn workers install it too.
No upstream or plugin source is modified.
"""
import torch
from vllm.v1.outputs import LogprobsTensors
from vllm.v1.sample.sampler import Sampler


def gather_on_cpu(logprobs, num_logprobs, token_ids):
    device = logprobs.device
    x = logprobs.detach().cpu()
    ids = token_ids.detach().cpu().unsqueeze(-1)
    values, indices = torch.topk(x, num_logprobs, dim=-1)
    selected = x.gather(-1, ids)
    ranks = (x >= selected).sum(-1)
    return LogprobsTensors(
        torch.cat((ids, indices), dim=1).to(device=device, dtype=torch.int32),
        torch.cat((selected, values), dim=1).to(device),
        ranks.to(device))


Sampler.gather_logprobs = staticmethod(gather_on_cpu)
