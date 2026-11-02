import torch
import torch_gcu
from vllm_fl.ops.fused_moe import router

logits = torch.tensor([[1., 2., 4., 0.], [3., 0., 2., 1.], [0., 2., 1., 4.]])
padding = torch.tensor([False, True, False])
router._get_padding_mask = lambda count: padding.to('gcu:0')
for dtype in (torch.int32, torch.int64):
    for renormalize in (False, True):
        weights, ids, _ = router.fused_topk(torch.zeros(3, 4, device='gcu:0'), logits.to('gcu:0'), 2, renormalize, dtype)
        expected_weights, expected_ids = logits.softmax(-1).topk(2, dim=-1)
        if renormalize:
            expected_weights /= expected_weights.sum(-1, keepdim=True)
        expected_ids = torch.where(padding[:, None], -1, expected_ids).to(dtype)
        torch.gcu.synchronize()
        torch.testing.assert_close(weights.cpu(), expected_weights)
        torch.testing.assert_close(ids.cpu(), expected_ids)
print('PASS: real GCU FL routing with padding, both ID dtypes and renormalization modes')
