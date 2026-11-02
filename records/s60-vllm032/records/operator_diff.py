"""Compare actual upstream normalization bodies and GCU compiled results."""
import ast
import json
from pathlib import Path
import torch
import torch_gcu
from vllm_fl.dispatch.backends.vendor.gcu.impl.inductor import apply_inductor_gcu_patch
apply_inductor_gcu_patch()
source = Path('/workspace/s60-adaptation/src/vllm/vllm/ir/ops/layernorm.py')
tree = ast.parse(source.read_text())
namespace = {'torch': torch, 'Tensor': torch.Tensor}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ('rms_norm', 'fused_add_rms_norm'):
        node.decorator_list = []
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(source), 'exec'), namespace)
torch.manual_seed(42)
results = []
for name in ('rms_norm', 'fused_add_rms_norm'):
    f = namespace[name]
    compiled = torch.compile(f, fullgraph=True, dynamic=False)
    for n, h in ((1,128),(13,128),(13,1024),(32,1024)):
        x = torch.randn(n,h, device='gcu', dtype=torch.bfloat16)
        w = torch.randn(h, device='gcu', dtype=torch.bfloat16)
        args = (x,w,1e-6) if name == 'rms_norm' else (x,torch.randn_like(x),w,1e-6)
        expected = f(*args)
        actual = compiled(*args)
        a = actual if isinstance(actual,tuple) else (actual,)
        b = expected if isinstance(expected,tuple) else (expected,)
        for i,(got,ref) in enumerate(zip(a,b)):
            delta = (got.float()-ref.float()).abs().cpu()
            row = {'op':name,'shape':[n,h],'output':i,'max_abs':delta.max().item(),'mean_abs':delta.mean().item(),'ref_max':ref.abs().max().item()}
            results.append(row)
            print(row,flush=True)
Path('/workspace/s60-adaptation/operator-diff.json').write_text(json.dumps(results,indent=2))
