"""Diagnostic only: capture actual hidden states and same-input CPU head oracle."""
import os
from pathlib import Path
import torch
from vllm.model_executor.layers.logits_processor import LogitsProcessor

_original = LogitsProcessor._get_logits
_counter = 0
_weights = None


def capture(self, hidden_states, lm_head, embedding_bias, skip_gather=False):
    global _counter, _weights
    result = _original(self, hidden_states, lm_head, embedding_bias, skip_gather)
    if result is not None and _counter < 16:
        ids = [13, 382, 50, 1336]
        if _weights is None:
            _weights = lm_head.weight.detach()[ids].cpu().double()
        h = hidden_states.detach().cpu()
        oracle = h.double() @ _weights.t()
        if embedding_bias is not None:
            oracle += embedding_bias.detach()[ids].cpu().double()
        directory = Path(os.environ['CAPTURE_HEAD_DIR'])
        directory.mkdir(parents=True, exist_ok=True)
        torch.save({'hidden': h, 'ids': ids, 'weight': _weights,
                    'device': result.detach()[:, ids].cpu(),
                    'oracle': oracle,
                    'oracle_rounded': oracle.to(result.dtype)},
                   directory / f'head-{_counter:02d}.pt')
        _counter += 1
    return result


LogitsProcessor._get_logits = capture
