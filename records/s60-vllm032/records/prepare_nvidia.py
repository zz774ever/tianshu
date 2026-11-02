import json
import pathlib
import urllib.request
import subprocess
root = pathlib.Path('/root/autodl-tmp/s60-reference')
root.mkdir(exist_ok=True)
for name, url in [('vllm', 'https://pypi.org/pypi/vllm/0.32.0/json')]:
    with urllib.request.urlopen(url, timeout=40) as f:
        data = json.load(f)
    (root / 'vllm-pypi.json').write_text(json.dumps(data))
    print('VERSION', data['info']['version'], flush=True)
    print('REQUIRES', data['info']['requires_dist'], flush=True)
    for item in data['urls']:
        if 'x86_64' in item['filename']:
            print('WHEEL', item['filename'], item['url'], flush=True)
subprocess.run(['/root/miniconda3/bin/python', '-m', 'venv', str(root / 'venv')], check=True)
