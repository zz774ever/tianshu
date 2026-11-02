import ctypes
import importlib.util
p='/workspace/s60-adaptation/flagcx_wrapper.py'
s=importlib.util.spec_from_file_location('flagcx_wrapper',p)
m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)
lib=ctypes.CDLL('/usr/local/lib/python3.12/site-packages/flagcx/libflagcx.so')
missing=[f.name for f in m.FLAGCXLibrary.exported_functions if not hasattr(lib,f.name)]
print('missing required symbols:',missing)
if missing:
 raise SystemExit(1)
x=m.FLAGCXLibrary('/usr/local/lib/python3.12/site-packages/flagcx/libflagcx.so')
print('FlagCX device handle initialized:',bool(x.devHandle))
