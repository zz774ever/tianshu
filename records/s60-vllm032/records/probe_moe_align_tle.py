import importlib
import sys

import torch
import torch_gcu

backend = importlib.import_module(
    'flag_gems.runtime.backend._enflame.fused.gcu300.moe_align_block_size'
)
mode = sys.argv[1]
if mode == 'legacy':
    backend.HAS_TLE = False
elif mode == 'inspect':
    original = backend.moe_align_block_size_tle_atomic_fused_coop

    class InspectLaunch:
        def __getitem__(self, grid):
            launch = original[grid]

            def invoke(*args, **kwargs):
                try:
                    return launch(*args, **kwargs)
                except Exception as error:
                    print('ATOMIC_ERROR', type(error).__name__, repr(error), flush=True)
                    raise SystemExit(2) from error

            return invoke

    backend.moe_align_block_size_tle_atomic_fused_coop = InspectLaunch()
else:
    raise ValueError(mode)

for rows in (1, 8, 512):
    ids = (torch.arange(rows * 8).reshape(rows, 8) * 17 % 256).to(torch.int32)
    sorted_ids, experts, padded = backend.moe_align_block_size(ids.to('gcu:0'), 32, 256)
    torch.gcu.synchronize()
    count = int(padded.cpu().item())
    counts = torch.bincount(ids.flatten().long(), minlength=256)
    expected = int(((counts + 31) // 32 * 32).sum())
    assert count == expected, (count, expected)
    actual_ids = sorted_ids.cpu()[:count].long()
    actual_experts = experts.cpu()[:count // 32].long()
    seen = actual_ids[actual_ids < ids.numel()]
    torch.testing.assert_close(seen.sort().values, torch.arange(ids.numel()))
    flat_ids = ids.flatten()
    for block in range(count // 32):
        tokens = actual_ids[block * 32:(block + 1) * 32]
        tokens = tokens[tokens < ids.numel()]
        assert bool((flat_ids[tokens] == actual_experts[block]).all())
    print('PASS', mode, rows, count, flush=True)
