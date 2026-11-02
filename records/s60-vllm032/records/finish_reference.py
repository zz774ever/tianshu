"""Use only verified complete wheels, then execute actual reference tests."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
root=Path('/root/autodl-tmp/s60-reference')
items=json.loads((root/'pending-wheel-manifest.json').read_text())
deadline=time.monotonic()+3600
while True:
    ready=all((root/'wheelhouse'/x['filename']).exists() and
              (root/'wheelhouse'/x['filename']).stat().st_size==x['size'] for x in items)
    if ready: break
    if time.monotonic()>deadline: raise TimeoutError('Verified wheel download incomplete')
    time.sleep(10)
for item in items:
    digest=hashlib.file_digest((root/'wheelhouse'/item['filename']).open('rb'),'sha256').hexdigest()
    assert digest==item['digests']['sha256'],item['filename']
print('All local wheel published SHA256 checks passed',flush=True)
for pid,expected in [(2755,b'run_after_install.py'),(2285,b'uv')]:
    p=Path(f'/proc/{pid}/cmdline')
    if p.exists():
        assert expected in p.read_bytes()
        os.kill(pid,signal.SIGTERM)
time.sleep(3)
python=str(root/'venv/bin/python')
subprocess.run([str(root/'venv/bin/uv'),'pip','install','--python',python,
 '--torch-backend','cu129','--find-links',str(root/'wheelhouse'),
 str(root/'vllm-0.32.0+cu129-cp38-abi3-manylinux_2_28_x86_64.whl')],check=True)
env=dict(os.environ,VLLM_PLUGINS='',CUDA_VISIBLE_DEVICES='0')
subprocess.run([python,str(root/'runtime_probe.py')],env=env,check=True)
subprocess.run([python,str(root/'smoke.py'),'--extended','--output',
 str(root/'results-nvidia-eager-extended.json')],env=env,check=True)
