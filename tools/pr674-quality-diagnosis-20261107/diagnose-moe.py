import json
import torch

from flaggems_vllm import moe_align_block_size_triton, topk_softmax


torch.manual_seed(674)
device = "cuda"
records = []


def validate(routes, outputs, block_size):
    sorted_ids, experts, total = (tensor.cpu() for tensor in outputs)
    routes = routes.cpu().flatten()
    count = total.item()
    assert 0 <= count <= sorted_ids.numel(), (count, sorted_ids.numel())
    active = sorted_ids[:count]
    valid = active < routes.numel()
    assert torch.equal(active[valid].sort().values, torch.arange(routes.numel(), dtype=torch.int32)), active.tolist()
    for position in range(0, count, block_size):
        group = active[position:position + block_size]
        group = group[group < routes.numel()]
        assert (routes[group.long()] == experts[position // block_size]).all(), (position, group.tolist())


for rows in (1, 2, 4, 8, 16, 32):
    routes = torch.randint(0, 256, (rows, 8), dtype=torch.int32, device=device)
    block_size = 16
    size = min(routes.numel() + 256 * (block_size - 1), routes.numel() * block_size)
    outputs = (
        torch.empty(size, dtype=torch.int32, device=device),
        torch.empty((size + block_size - 1) // block_size, dtype=torch.int32, device=device),
        torch.empty(1, dtype=torch.int32, device=device),
    )

    def run_align():
        moe_align_block_size_triton(routes, 256, block_size, *outputs)

    run_align()
    validate(routes, outputs, block_size)
    stream = torch.cuda.Stream()
    stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(stream):
        run_align()
    torch.cuda.current_stream().wait_stream(stream)
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, stream=stream):
        run_align()
    for replay in range(5):
        routes.copy_(torch.randint(0, 256, routes.shape, dtype=torch.int32, device=device))
        graph.replay()
        validate(routes, outputs, block_size)
    record = {"op": "moe_align", "rows": rows, "replays": 5, "passed": True}
    records.append(record)
    print(json.dumps(record), flush=True)

    logits = torch.randn((rows, 256), dtype=torch.float32, device=device)
    weights = torch.empty((rows, 8), dtype=torch.float32, device=device)
    indices = torch.empty((rows, 8), dtype=torch.int32, device=device)
    source = torch.empty_like(indices)

    def run_topk():
        topk_softmax(weights, indices, source, logits, True)

    def validate_topk():
        scores = logits.cpu().softmax(-1)
        expected_weights, expected_ids = scores.topk(8, dim=-1)
        expected_weights /= expected_weights.sum(-1, keepdim=True)
        assert torch.equal(indices.cpu().long(), expected_ids)
        torch.testing.assert_close(weights.cpu(), expected_weights, rtol=1e-4, atol=1e-6)

    run_topk()
    validate_topk()
    stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(stream):
        run_topk()
    torch.cuda.current_stream().wait_stream(stream)
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, stream=stream):
        run_topk()
    for replay in range(5):
        logits.copy_(torch.randn_like(logits))
        graph.replay()
        validate_topk()
    record = {"op": "topk_softmax", "rows": rows, "replays": 5, "passed": True}
    records.append(record)
    print(json.dumps(record), flush=True)

print(json.dumps({"summary": records}), flush=True)
