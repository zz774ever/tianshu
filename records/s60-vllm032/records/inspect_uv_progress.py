from pathlib import Path
import os
import time
root=Path('/proc/2285/fd')
def snapshot():
    result={}
    if not root.exists():
        print('Installer exited',flush=True)
        return result
    for fd in root.iterdir():
        try:
            path=os.readlink(fd)
            if '/.cache/uv/.tmp' in path and '.so' in path:
                result[path]=(fd.stat().st_size,Path('/proc/2285/fdinfo',fd.name).read_text().splitlines()[0])
        except OSError:
            pass
    return result
before=snapshot()
time.sleep(10)
after=snapshot()
for path,(size,pos) in sorted(after.items()):
    print(path,size,pos,'growth_10s',size-before.get(path,(0,''))[0],flush=True)
