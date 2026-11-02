"""Remove only Git-ignored Python/pytest caches from the delivery repository."""
from pathlib import Path
import shutil
import subprocess
root = Path('/workspace/vllm-plugin-FL')
raw = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--others', '--ignored', '--exclude-standard', '--directory', '-z'])
count = 0
for item in raw.decode().split('\0'):
    if not item:
        continue
    path = root / item.rstrip('/')
    if path.name in {'__pycache__', '.pytest_cache'} and path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        count += 1
print('Removed ignored cache directories:', count)
print('Retained runtime-generated _version.py and all source/tests/evidence.')
