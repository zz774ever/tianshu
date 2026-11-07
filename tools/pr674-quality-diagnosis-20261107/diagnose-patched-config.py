import json

from vllm.config import CUDAGraphMode
from vllm.config.compilation import CompilationMode
from vllm.engine.arg_utils import EngineArgs


for model_name in ("Qwen3.6-35B-A3B", "Qwen3.6-27B"):
    config = EngineArgs(
        model="/models/" + model_name,
        tensor_parallel_size=4,
        max_model_len=32768,
        compilation_config={"cudagraph_capture_sizes": [1, 2, 4, 8, 16, 32]},
    ).create_engine_config()
    compilation = config.compilation_config
    expected_reuse = model_name != "Qwen3.6-35B-A3B"
    assert compilation.mode == CompilationMode.VLLM_COMPILE
    assert compilation.cudagraph_mode == CUDAGraphMode.FULL_AND_PIECEWISE
    assert compilation.cudagraph_capture_sizes == [1, 2, 4, 8, 16, 32]
    assert compilation.ir_enable_torch_wrap is True
    assert compilation.inductor_compile_config.get("allow_buffer_reuse", True) is expected_reuse
    assert compilation.inductor_compile_config.get("inplace_buffers", True) is expected_reuse
    print(json.dumps({
        "model": model_name,
        "compilation_mode": compilation.mode.name,
        "cudagraph_mode": compilation.cudagraph_mode.name,
        "capture_sizes": compilation.cudagraph_capture_sizes,
        "ir_enable_torch_wrap": compilation.ir_enable_torch_wrap,
        "inductor_compile_config": compilation.inductor_compile_config,
        "passed": True,
    }), flush=True)
