import json
import importlib.metadata as m
import torch
print(json.dumps({'torch':torch.__version__, 'cuda_build':torch.version.cuda,
                  'vllm':m.version('vllm'), 'available':torch.cuda.is_available()}, indent=2), flush=True)
x = torch.arange(16, device='cuda', dtype=torch.float32)
assert x.sum().item() == 120
print('CUDA basic operation PASS', torch.cuda.get_device_name(), flush=True)
import vllm
print('vLLM import PASS', vllm.__version__, flush=True)
assert vllm.__version__.split('+')[0] == '0.32.0'
