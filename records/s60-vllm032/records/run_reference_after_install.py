"""Join the known isolated installer, then test the genuine NVIDIA reference."""
import os
from pathlib import Path
import subprocess
import time
root = Path('/root/autodl-tmp/s60-reference')
installer = Path('/proc/2285/cmdline')
deadline = time.monotonic() + 3600
while installer.exists():
    if time.monotonic() >= deadline:
        raise TimeoutError('Isolated installer has not completed; inspect install-local.log')
    time.sleep(5)
python = str(root / 'venv/bin/python')
env = dict(os.environ, VLLM_PLUGINS='', CUDA_VISIBLE_DEVICES='0')
subprocess.run([python, str(root/'runtime_probe.py')], env=env, check=True)
subprocess.run([python, str(root/'smoke.py'), '--extended', '--output',
                str(root/'results-nvidia-eager-extended.json')], env=env, check=True)
