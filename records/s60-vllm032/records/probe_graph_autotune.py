import importlib.util
from pathlib import Path

import torch
import torch_gcu
import triton
from torch._inductor.runtime import triton_heuristics as heuristics
from torch._inductor.runtime.hints import DeviceProperties
from torch_gcu.gcu.inductor.backend_register import GCUConfig, GCUTritonConfigGenerator, GCUInductorPatcher

GCUInductorPatcher().register_device_interface()
adapter_path = '/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/gcu/impl/inductor.py'
spec = importlib.util.spec_from_file_location('gcu_adapter_probe', adapter_path)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
adapter._install_gcu_i64_compile_options(heuristics)
adapter._install_gcu_resource_errors(heuristics)
source = Path('/workspace/s60-adaptation/replay_graph_cast_kernel.py').read_text()
source = source.replace(', fp_downcast_rounding="rtne"', '')
path = Path('/workspace/s60-adaptation/replay_graph_cast_original.py')
path.write_text(source)
spec = importlib.util.spec_from_file_location('replay_graph_cast_original', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
kernel = module.triton_poi_fused___and___arange_eq_index_lt_remainder_select_split_where_6
meta = {
    'signature': dict(zip(kernel.arg_names, ['*i64', '*bf16', '*bf16', '*bf16', 'i64', 'i32', 'i32', 'constexpr', 'constexpr'])),
    'device': DeviceProperties.create(torch.device('gcu:0')),
    'constants': {}, 'configs': [{}],
}
generator = GCUTritonConfigGenerator(GCUConfig())
autotuner = generator.pointwise(
    {'y': 512, 'x': 32}, meta, filename=str(path),
    inductor_meta={'force_disable_caches': True},
)(kernel)
configs = list(autotuner.configs)
print('GENERATED:', [cfg.kwargs for cfg in configs], flush=True)
autotuner.precompile(warm_cache_only=True)
print('COMPILED:', len(autotuner.compile_results), 'of', len(configs), flush=True)
positions_cpu = torch.arange(1536, dtype=torch.int64).reshape(3, 512) * 131 % 262144
positions_cpu[1, ::2] -= 262144
positions_cpu[2, ::3] -= 262144
values_cpu = ((torch.arange(262144 * 64, dtype=torch.int32) % 997) - 498).reshape(262144, 64).to(torch.bfloat16)
positions = positions_cpu.to('gcu')
values = values_cpu.to('gcu')
columns = torch.arange(32)
selected = torch.where((columns % 3 == 2) & (columns < 30), 2, torch.where(columns % 3 == 1, 1, 0))
indices = positions_cpu[selected[:, None], torch.arange(512)].T
expected = [values_cpu[indices, columns + offset] for offset in (0, 32)]
outputs = [torch.empty((512, 32), dtype=torch.bfloat16, device='gcu') for _ in range(2)]
for result in autotuner.compile_results:
    config = result.config
    kernel[(triton.cdiv(32, config.kwargs['XBLOCK']), triton.cdiv(512, config.kwargs['YBLOCK']))](
        positions, values, *outputs, 512, 512, 32,
        **config.kwargs, num_warps=config.num_warps, num_stages=config.num_stages, enable_i64=True,
    )
    torch.gcu.synchronize()
    for output, reference in zip(outputs, expected):
        torch.testing.assert_close(output.cpu(), reference, rtol=0, atol=0)
    print('NONZERO PASS:', config.kwargs, flush=True)
assert autotuner.compile_results
print('PASS: real vendor configs, actual Torch precompile loop, nonzero CPU oracle', flush=True)
