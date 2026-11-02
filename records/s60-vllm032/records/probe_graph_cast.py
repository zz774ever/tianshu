from pathlib import Path
import torch
import torch_gcu
import triton
import triton.language as tl

log = Path('/workspace/s60-adaptation/logs/gate-27b-graph-collectives.log').read_text()
start = log.index('def triton_poi_fused___and___arange_eq_index_lt_remainder_select_split_where_6(')
source = log[start:log.index('\n', start)] + '\n'
for line in log[start:].splitlines()[1:]:
    if 'triton_heuristics.py:874] ' not in line:
        break
    body = line.split('triton_heuristics.py:874] ', 1)[1]
    if body.startswith('metadata:') or body.startswith('Traceback'):
        break
    source += body + '\n'
source = source.replace('.to(tl.bfloat16)', '.to(tl.bfloat16, fp_downcast_rounding="rtne")').rstrip() + '\n'
path = Path('/workspace/s60-adaptation/replay_graph_cast_kernel.py')
path.write_text('import triton\nimport triton.language as tl\n@triton.jit\n' + source)
import importlib.util
spec = importlib.util.spec_from_file_location('replay_graph_cast_kernel', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
kernel = getattr(module, source.split('(')[0].split()[1])
positions = torch.zeros((3, 512), dtype=torch.int64, device='gcu')
values = torch.zeros((262144, 64), dtype=torch.bfloat16, device='gcu')
outputs = [torch.empty((512, 32), dtype=torch.bfloat16, device='gcu') for _ in range(2)]
for yblock, xblock in [(512, 2), (128, 4), (32, 32), (1, 32)]:
    try:
        kernel[(triton.cdiv(32, xblock), triton.cdiv(512, yblock))](positions, values, *outputs, 512, 512, 32, YBLOCK=yblock, XBLOCK=xblock, num_warps=4)
        torch.gcu.synchronize()
        for output in outputs:
            torch.testing.assert_close(output.cpu(), torch.zeros((512, 32), dtype=torch.bfloat16))
        print(f'PASS: YBLOCK={yblock} XBLOCK={xblock}', flush=True)
    except Exception as error:
        print(f'FAIL: YBLOCK={yblock} XBLOCK={xblock}: {str(error).splitlines()[0]}', flush=True)
