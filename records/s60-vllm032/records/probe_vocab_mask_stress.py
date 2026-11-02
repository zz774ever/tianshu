import torch
import torch_gcu
from vllm_fl.dispatch.backends.vendor.gcu.impl.vocab_mask import get_masked_input_and_mask

cases = 0
for dtype in (torch.int32, torch.int64):
    for shape in ((0,), (1,), (17,), (3, 257)):
        for bounds in ((0, 8, 2, 20, 24), (8, 16, 2, 24, 28), (0, 8, 0, 8, 8)):
            count = torch.Size(shape).numel()
            values = torch.arange(count, dtype=dtype).remainder(35) - 3
            if dtype == torch.int64 and count > 2:
                values[1] = 2**33
                values[2] = -(2**33)
            values = values.reshape(shape)
            start, end, padding, added_start, added_end = bounds
            original = (values >= start) & (values < end)
            added = (values >= added_start) & (values < added_end)
            offset = start * original + (added_start - (end - start) - padding) * added
            expected = (original | added) * (values - offset)
            actual, mask = get_masked_input_and_mask(values.to('gcu:0'), *bounds)
            torch.gcu.synchronize()
            torch.testing.assert_close(actual.cpu(), expected)
            torch.testing.assert_close(mask.cpu(), ~(original | added))
            cases += 1
print(f'PASS: {cases} GCU vocabulary masks against CPU, empty/single/multiblock/2D/int32/int64/large IDs')
