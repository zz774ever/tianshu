from pathlib import Path
import re
p=Path('/root/autodl-tmp/s60-reference/install-local.log')
s=p.read_text()
started=set(re.findall(r'^Downloading ([^ ]+)',s,re.M))
done=set(re.findall(r'^\s*Downloaded (\S+)',s,re.M))
print('Pending downloads:',sorted(started-done),flush=True)
for name in sorted(started-done):
    lines=[l for l in s.splitlines() if name.replace('-','_') in l and 'https:' in l]
    print(name, '\n'.join(lines[-2:]),flush=True)
