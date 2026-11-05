import json
from importlib import metadata
from pathlib import Path

import torch
import triton
import triton.language as language


@triton.jit
def add_kernel(input_left, input_right, output, count: language.constexpr):
    offsets = language.program_id(0) * 256 + language.arange(0, 256)
    left = language.load(input_left + offsets, offsets < count, other=0)
    right = language.load(input_right + offsets, offsets < count, other=0)
    language.store(output + offsets, left + right, offsets < count)


assert metadata.version("flagtree") == "0.7.0+iluvatar3.6"
torch.cuda.set_device(0)
free_bytes, total_bytes = torch.cuda.mem_get_info(0)
assert free_bytes > 30 * 1024**3, "Selected GPU is occupied"
results = []
for dtype in (torch.float32, torch.float16, torch.bfloat16):
    for count in (1, 257, 100003):
        input_left = torch.randn(count, device="cuda:0", dtype=dtype)
        input_right = torch.randn_like(input_left)
        output = torch.empty_like(input_left)
        add_kernel[(triton.cdiv(count, 256),)](
            input_left, input_right, output, count
        )
        torch.cuda.synchronize()
        torch.testing.assert_close(output, input_left + input_right, rtol=0, atol=0)
        results.append({"dtype": str(dtype), "count": count, "passed": True})
document = {
    "flagtree": metadata.version("flagtree"),
    "triton": triton.__version__,
    "module": triton.__file__,
    "device": torch.cuda.get_device_name(0),
    "target": str(triton.runtime.driver.active.get_current_target()),
    "results": results,
}
Path("/workspace/adaptation-gate-upgrade-20261105/device-verification.json").write_text(
    json.dumps(document, indent=2) + "\n"
)
print(json.dumps(document, indent=2))
