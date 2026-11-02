from pathlib import Path
import re
p = Path('/workspace/s60-adaptation/runner032-merge.py')
s = p.read_text()
blocks = list(re.finditer(r'^<<<<<<< [^\n]*\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n', s, re.M | re.S))
assert len(blocks) == 5
choices = ['', blocks[1][2], blocks[2][1].split('def _get_parameter_for_reload')[0], blocks[3][2], '']
for m, choice in reversed(list(zip(blocks, choices))):
    s = s[:m.start()] + choice + s[m.end():]
s = s.replace('    is_residual_scattered_for_sp,\n', '')
# Utilities formerly reached by relative import must stay in upstream namespace.
s = s.replace('from .utils import (', 'from vllm.v1.worker.utils import (')
s = s.replace('v0.28.0/vllm/v1/worker/gpu_model_runner.py', 'v0.32.0/vllm/v1/worker/gpu_model_runner.py')
assert not re.search(r'^<<<<<<<|^=======|^>>>>>>>', s, re.M)
compile(s, str(p), 'exec')
Path('/workspace/vllm-plugin-FL/vllm_fl/worker/model_runner.py').write_text(s)
