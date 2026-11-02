from pathlib import Path
import re
p=Path('/workspace/s60-adaptation/worker032-merge.py')
s=p.read_text()
pattern=r'^<<<<<<<[^\n]*\n(.*?)^=======\n(.*?)^>>>>>>>[^\n]*\n'
n=0
def resolve(m):
 global n
 n+=1
 a,b=m.groups()
 if n==1:
  return a+b
 if n==2:
  return a+'from vllm.v1.worker.gpu.cudagraph_utils import has_compiled_submodule\n'
 if n==3:
  return a+'\n\n'+b
 if n==4:
  return ('            return GPUModelRunnerV2(self.vllm_config, self.device)  # type: ignore\n'
          '        from vllm_fl.worker.model_runner import ModelRunnerFL as GPUModelRunnerV1\n')
 raise AssertionError(n)
s=re.sub(pattern,resolve,s,flags=re.M|re.S)
assert n==4 and '<<<<<<<' not in s
s=s.replace('blob/v0.28.0/', 'blob/v0.32.0/')
compile(s,'worker.py','exec')
Path('/workspace/vllm-plugin-FL/vllm_fl/worker/worker.py').write_text(s)
print('Reconciled worker conflicts:', n)
