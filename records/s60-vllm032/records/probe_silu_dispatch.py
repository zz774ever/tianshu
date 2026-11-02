import torch
from vllm.config import VllmConfig, set_current_vllm_config
from vllm.model_executor.layers.activation import SiluAndMul
import vllm_fl.ops.activation as activation

from vllm_fl.worker.runtime import _initialize_fl_runtime

_initialize_fl_runtime(0)
config = VllmConfig()
config.compilation_config.custom_ops = ['none', '+SiluAndMul']
with set_current_vllm_config(config):
    layer = SiluAndMul()
    print('LAYER', type(layer), 'METHOD', layer._forward_method, flush=True)
    assert isinstance(layer, activation.SiluAndMulFL)
    assert layer._forward_method.__func__ is activation.SiluAndMulFL.forward_oot
    for rows, width in [(1, 1024), (8, 1024), (512, 1024)]:
        source = torch.linspace(-5, 5, rows * width * 2).reshape(rows, width * 2).to(torch.bfloat16)
        expected = torch.nn.functional.silu(source[:, :width]).mul(source[:, width:])
        actual = layer(source.to('gcu')).cpu()
        torch.testing.assert_close(actual, expected, rtol=0.02, atol=0.02)
        print('PASS', rows, width, flush=True)
print('DISPATCH_AND_GCU_PASS', flush=True)
