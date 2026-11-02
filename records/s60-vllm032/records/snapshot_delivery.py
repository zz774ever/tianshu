"""Capture reviewable changes without modifying the working tree."""
import hashlib
import json
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

repo = Path('/workspace/vllm-plugin-FL')
root = Path('/workspace/s60-adaptation')
out = root / 'handoff' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out.mkdir(parents=True, exist_ok=False)

def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])

subprocess.run(['git', '-C', str(repo), 'diff', '--check'], check=True)
(out / 'tracked-changes.patch').write_bytes(git('diff', '--binary', 'HEAD'))
(out / 'git-status.txt').write_bytes(git('status', '--short', '--branch'))
(out / 'git-diff-stat.txt').write_bytes(git('diff', '--stat', 'HEAD'))
untracked = git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
with tarfile.open(out / 'untracked-files.tar.gz', 'w:gz') as archive:
    for raw in untracked:
        if raw:
            name = raw.decode()
            archive.add(repo / name, arcname=name)
(out / 'STATUS.md').write_bytes((root / 'STATUS.md').read_bytes())
manifest = {
    'repository': str(repo),
    'branch': git('branch', '--show-current').decode().strip(),
    'head': git('rev-parse', 'HEAD').decode().strip(),
    'vllm_target': '0.32.0',
    'precision': 'user accepted recorded differences; not a strict-match pass',
    'files': {},
}
for path in sorted(out.iterdir()):
    manifest['files'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
(out / 'snapshot.json').write_text(json.dumps(manifest, indent=2) + '\n')
with tarfile.open(out / 'untracked-files.tar.gz') as archive:
    assert sorted(archive.getnames()) == sorted(x.decode() for x in untracked if x)
for name, digest in manifest['files'].items():
    assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
assert manifest['branch'] == 'adapt/vllm032-from-050'
print(out)
print(json.dumps(manifest, indent=2))
