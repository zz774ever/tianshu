import json
import torch
import triton.language as tl
from flaggems_vllm import invoke_fused_moe_triton_kernel, moe_sum

torch.manual_seed(674)
weights = (torch.randn((256, 256, 2048), device="cuda", dtype=torch.bfloat16) * 0.02).contiguous()
config = {"BLOCK_SIZE_M": 16, "BLOCK_SIZE_N": 64, "BLOCK_SIZE_K": 64, "GROUP_SIZE_M": 1, "num_warps": 4, "num_stages": 2}

for rows in (1, 2, 4, 8):
    inputs = torch.randn((rows, 2048), device="cuda", dtype=torch.bfloat16)
    expert_ids = torch.randint(0, 256, (rows * 8,), device="cuda", dtype=torch.int32)
    total = torch.tensor([rows * 8 * 16], device="cuda", dtype=torch.int32)
    output = torch.empty((rows, 8, 256), device="cuda", dtype=torch.bfloat16)
    summed = torch.empty((rows, 256), device="cuda", dtype=torch.bfloat16)

    def run():
        invoke_fused_moe_triton_kernel(inputs, weights, output, None, None, None, None, expert_ids, total, False, 8, config, tl.bfloat16)
        moe_sum(output, summed)

    def validate(label):
        selected = weights[expert_ids.long()].float()
        expected = torch.bmm(selected, inputs.repeat_interleave(8, 0).float().unsqueeze(-1)).squeeze(-1).bfloat16().view_as(output)
        difference = (output.float() - expected.float()).abs()
        record = {"rows": rows, "phase": label, "max_abs": difference.max().item(), "mean_abs": difference.mean().item()}
        print(json.dumps(record), flush=True)
        torch.testing.assert_close(output, expected, rtol=0.03, atol=0.02)
        torch.testing.assert_close(summed.float(), output.float().sum(1), rtol=0.01, atol=0.02)

    run()
    validate("eager")
    stream = torch.cuda.Stream()
    stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(stream):
        run()
    torch.cuda.current_stream().wait_stream(stream)
    expert_ids.fill_(-1)
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, stream=stream):
        run()
    for replay in range(3):
        inputs.copy_(torch.randn_like(inputs))
        expert_ids.copy_(torch.randint(0, 256, expert_ids.shape, device="cuda", dtype=torch.int32))
        graph.replay()
        validate(f"replay-{replay}")
