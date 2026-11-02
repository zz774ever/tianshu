"""Fetch exact pending PyPI wheels by HTTP ranges; validate published hashes."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.request
import sys
root=Path('/root/autodl-tmp/s60-reference')
log=(root/'install-local.log').read_text()
started=set(re.findall(r'^Downloading (\S+)',log,re.M))
done=set(re.findall(r'^\s*Downloaded (\S+)',log,re.M))
urls=re.findall(r'https://files.pythonhosted.org/\S+\.whl',log)
items=[]
for name in sorted(started-done):
    url=next(u for u in urls if '/'+name.replace('-','_')+'-' in u)
    filename=url.rsplit('/',1)[1]
    version=filename.split('-')[1]
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=30) as r:
        meta=json.load(r)
    item=next(x for x in meta['urls'] if x['filename']==filename)
    assert item['url']==url
    items.append(item)
out=root/'wheelhouse'
out.mkdir(exist_ok=True)
(root/'pending-wheel-manifest.json').write_text(json.dumps(items,indent=2))
probe='--probe' in sys.argv
for item in items[:1] if probe else items:
    dest=out/item['filename']
    size=item['size']
    chunk=1024**2 if probe else 8*1024**2
    ranges=list(range(0,min(size,4*chunk) if probe else size,chunk))
    start=time.monotonic()
    def fetch(offset):
        end=min(size-1,offset+chunk-1)
        part=out/(item['filename']+f'.part{offset}')
        subprocess.run(['curl','-fsSL','--retry','2','--connect-timeout','10',
            '--max-time','180','--range',f'{offset}-{end}',item['url'],'-o',str(part)],check=True)
        assert part.stat().st_size==end-offset+1,(part,part.stat().st_size)
        return part
    with ThreadPoolExecutor(max_workers=8 if not probe else 4) as pool:
        parts=list(pool.map(fetch,ranges))
    if not probe:
        digest=hashlib.sha256()
        with dest.open('wb') as f:
            for part in parts:
                data=part.read_bytes()
                digest.update(data)
                f.write(data)
        assert dest.stat().st_size==size
        assert digest.hexdigest()==item['digests']['sha256']
    total=sum(p.stat().st_size for p in parts)
    print(item['filename'],'probe' if probe else 'SHA256 PASS',total,
          'bytes/sec',round(total/(time.monotonic()-start)),flush=True)
    for part in parts: part.unlink()
