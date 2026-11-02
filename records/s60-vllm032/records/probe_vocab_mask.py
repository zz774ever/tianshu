import torch
import torch_gcu
from vllm.model_executor.layers import vocab_parallel_embedding as embedding

fn = embedding.get_masked_input_and_mask
original = getattr(fn, '_torchdynamo_orig_callable', fn)
ids = torch.tensor([-1, 0, 9, 10, 11, 19, 20, 23, 24, 29, 30, 2**33], dtype=torch.int64)
for bounds in [(0, 10, 2, 20, 24), (10, 20, 0, 24, 30)]:
    expected = original(ids, *bounds)
    from vllm_fl.dispatch.backends.vendor.gcu.impl.vocab_mask import get_masked_input_and_mask
    actual = get_masked_input_and_mask(ids.to('gcu:0'), *bounds)
    torch.gcu.synchronize()
    for actual_tensor, expected_tensor in zip(actual, expected):
        assert torch.equal(actual_tensor.cpu(), expected_tensor)
print('PASS: eager vocabulary mask on real GCU matches CPU for two shards, padding, added tokens and int64 indices')
