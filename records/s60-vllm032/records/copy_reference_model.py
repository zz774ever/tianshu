import hashlib
import os
from pathlib import Path
import paramiko
root = Path('/models/Qwen3-0.6B')
remote = '/root/autodl-tmp/s60-reference/model'
c = paramiko.SSHClient()
c.load_system_host_keys()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('connect.westx.seetacloud.com', port=49162, username='root', password=os.environ['SSH_REFERENCE_PASSWORD'], timeout=30, look_for_keys=False, allow_agent=False)
s = c.open_sftp()
for path in ['/root/autodl-tmp/s60-reference', remote]:
    try: s.mkdir(path)
    except OSError: pass
manifest = {}
for p in sorted(root.iterdir()):
    if not p.is_file(): continue
    digest = hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda: f.read(8*1024*1024), b''): digest.update(data)
    manifest[p.name] = digest.hexdigest()
    print('COPY', p.name, p.stat().st_size, flush=True)
    s.put(str(p), remote+'/'+p.name)
    print('DONE', p.name, manifest[p.name], flush=True)
Path('/workspace/s60-adaptation/model-sha256.txt').write_text(''.join(f'{v}  {k}\n' for k,v in manifest.items()))
s.close()
c.close()
