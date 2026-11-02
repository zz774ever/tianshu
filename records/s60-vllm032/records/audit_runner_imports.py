import ast
import importlib
from pathlib import Path

path = Path('/workspace/vllm-plugin-FL/vllm_fl/worker/model_runner.py')
for node in ast.parse(path.read_text()).body:
    if not isinstance(node, ast.ImportFrom) or not node.module or not node.module.startswith('vllm.'):
        continue
    try:
        module = importlib.import_module(node.module)
    except Exception as exc:
        print(node.lineno, node.module, type(exc).__name__, str(exc), flush=True)
        continue
    missing = [n.name for n in node.names if not hasattr(module, n.name)]
    if missing:
        print(node.lineno, node.module, 'MISSING', missing, flush=True)
