"""Check PyTorch's first-index argmax contract at observed vocabulary ties."""
import torch
import torch_gcu

for dtype in (torch.float32, torch.bfloat16):
    for n in (1024, 151936):
        x = torch.full((4, n), -10., dtype=dtype)
        pairs = [(13, 382), (50, 1336 if n > 1336 else 999), (0, n-1), (100, 101)]
        for row, (a, b) in enumerate(pairs):
            x[row, a] = 5.
            x[row, b] = 5.
        expected = x.argmax(-1)
        actual = x.to('gcu:3').argmax(-1).cpu()
        print(dtype, n, 'expected', expected.tolist(), 'actual', actual.tolist(), flush=True)
        assert torch.equal(expected, actual), 'GCU argmax violates smallest-index tie contract'
