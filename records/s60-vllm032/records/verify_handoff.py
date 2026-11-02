import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

repo = Path('/workspace/vllm-plugin-FL')
snapshot = sorted(Path('/workspace/s60-adaptation/handoff').glob('*/snapshot.json'))[-1].parent
manifest = json.loads((snapshot / 'snapshot.json').read_text())
for name, digest in manifest['files'].items():
    assert hashlib.sha256((snapshot / name).read_bytes()).hexdigest() == digest
with tempfile.TemporaryDirectory(prefix='s60-handoff-') as temporary:
    destination = Path(temporary)
    archive_path = destination / 'head.tar'
    with archive_path.open('wb') as output:
        subprocess.run(['git', '-C', str(repo), 'archive', manifest['head']], stdout=output, check=True)
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination, filter='data')
    subprocess.run(['git', 'apply', '--check', str(snapshot / 'tracked-changes.patch')], cwd=destination, check=True)
    subprocess.run(['git', 'apply', str(snapshot / 'tracked-changes.patch')], cwd=destination, check=True)
    with tarfile.open(snapshot / 'untracked-files.tar.gz') as archive:
        archive.extractall(destination, filter='data')
        untracked = archive.getnames()
    tracked = subprocess.check_output(['git', '-C', str(repo), 'diff', '--name-only', 'HEAD']).decode().splitlines()
    for name in tracked + untracked:
        assert (destination / name).read_bytes() == (repo / name).read_bytes(), name
    assert (snapshot / 'STATUS.md').read_bytes() == Path('/workspace/s60-adaptation/STATUS.md').read_bytes()
    print(f'PASS: manifest hashes and {len(tracked)} tracked + {len(untracked)} untracked files reconstructed byte-for-byte')
