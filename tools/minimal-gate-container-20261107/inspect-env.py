import ctypes
import json
import os
import platform
import sys
from importlib import metadata
from pathlib import Path

packages = [
    'torch', 'vllm', 'vllm-plugin-fl', 'flag-gems', 'flaggems-vllm', 'flagtree',
    'setuptools', 'setuptools-scm', 'wheel', 'numpy', 'transformers', 'tokenizers',
    'huggingface-hub', 'compressed-tensors', 'fastapi', 'starlette', 'pydantic',
    'mcp', 'mistral-common', 'opencv-python-headless', 'xgrammar', 'openai',
    'pillow', 'pytest', 'apache-tvm-ffi', 'model-hosting-container-standards',
    'safetensors', 'aiohttp', 'requests', 'httpx', 'uvicorn', 'einops',
    'packaging', 'pybind11', 'PyYAML', 'sqlalchemy', 'modelscope',
]
versions = {}
for name in packages:
    try:
        versions[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        versions[name] = None
print(json.dumps({'python': sys.version, 'executable': sys.executable,
                  'prefix': sys.prefix, 'base_prefix': sys.base_prefix,
                  'platform': platform.platform(), 'packages': versions}, indent=2), flush=True)
assert sys.prefix == sys.base_prefix
if '--cuda' in sys.argv:
    import torch
    print('torch_import', torch.__file__, flush=True)
    print('cuda_available', torch.cuda.is_available(), flush=True)
    print('cuda_device_count', torch.cuda.device_count(), flush=True)
    assert torch.cuda.is_available()
    assert torch.cuda.device_count() == 4
    for index in range(torch.cuda.device_count()):
        assert torch.ones(1, device=f'cuda:{index}').cpu().item() == 1
    print('CUDA_ALLOCATION_PASS', flush=True)
    values = torch.ones(1, device='cuda')
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    stream = torch.cuda.Stream()
    with torch.cuda.graph(graph, stream=stream):
        output = values + 1
    graph.replay()
    torch.cuda.synchronize()
    assert output.item() == 2
    print('CUDA_GRAPH_CAPTURE_REPLAY_PASS', flush=True)
    libraries = sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                        if any(name in line for name in ['libcudart.so', 'libcuda.so', 'libixthunk.so'])})
    print(json.dumps({'loaded_runtime_libraries': libraries}, indent=2), flush=True)
if '--stack' in sys.argv:
    import flag_gems
    import torch
    import triton
    import vllm
    import vllm_fl
    from vllm_fl.distributed.device_communicators import flagcx

    expected = {'vllm': '0.32.0+empty', 'torch': '2.10.0+corex.4.5.0',
                'flagtree': '0.7.0+iluvatar3.6', 'flag-gems': '5.5.0.dev0',
                'flaggems-vllm': '0.3.0.dev1'}
    for name, version in expected.items():
        assert versions[name] == version, (name, versions[name], version)
    assert Path(vllm_fl.__file__).is_relative_to('/opt/vllm-plugin-FL')
    assert hasattr(triton._C.libtriton, 'iluvatar')
    ctypes.CDLL(os.environ['FLAGCX_PATH'] + '/build/lib/libflagcx.so')
    assert flagcx._flagcx_available
    print(json.dumps({'modules': {module.__name__: module.__file__
                                for module in [torch, vllm, vllm_fl, flag_gems, triton]}}, indent=2))
    print('STACK_CHECK_PASS', flush=True)
