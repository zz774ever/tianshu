"""Diagnostic: capture only valid logical KV history at the selected layer step."""
import functools
import os
from pathlib import Path
import torch
import capture_layers as capture
from vllm_fl.dispatch.backends.vendor.gcu.impl.attention import AttentionGCUImpl

_original = AttentionGCUImpl.forward
_done = False

@functools.wraps(_original)
def forward(self, layer, query, key, value, kv_cache, attn_metadata,
            output=None, output_scale=None, output_block_scale=None):
    global _done
    selected = (not _done and capture._active and attn_metadata is not None
                and layer.layer_name == 'model.layers.7.self_attn.attn')
    q = capture.cpu(query) if selected else None
    result = _original(self, layer, query, key, value, kv_cache, attn_metadata,
                       output, output_scale, output_block_scale)
    if selected:
        meta = attn_metadata
        ids, pos = capture._data['input_ids'], capture._data['positions']
        matches = ((ids == 271) & (pos == 24)).nonzero().flatten()
        assert matches.numel() == 1
        token = matches.item()
        starts = meta.query_start_loc.cpu().tolist()
        seq = next(i for i in range(len(starts)-1) if starts[i] <= token < starts[i+1])
        length = int(meta.seq_lens[seq].item())
        assert length == 25 and starts[seq+1]-starts[seq] == 1
        block_size = kv_cache.shape[2]
        table = meta.block_table[seq].cpu().tolist()
        # Canonical [block, head, token, 2*dim]; omit unused pages/tail slots.
        chunks = [kv_cache[table[t//block_size], :, t%block_size, :]
                  for t in range(length)]
        data = {'query': q[token:token+1], 'kv': capture.cpu(torch.stack(chunks)),
                'output': capture.cpu(result[token:token+1]),
                'token_row': token, 'sequence_row': seq, 'scale': self.scale,
                'metadata': {k: capture.cpu(v) if isinstance(v, torch.Tensor) else v
                             for k,v in vars(meta).items()}}
        torch.save(data, Path(os.environ['CAPTURE_ATTENTION_CACHE']))
        _done = True
    return result

AttentionGCUImpl.forward = forward
