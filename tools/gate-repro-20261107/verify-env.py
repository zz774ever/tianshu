import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=Path)
arguments = parser.parse_args()
expected_versions = {
    'vllm': '0.32.0+empty',
    'torch': '2.10.0+corex.4.5.0',
    'flagtree': '0.7.0+iluvatar3.6',
    'flag-gems': '5.5.0.dev0',
    'flaggems-vllm': '0.3.0.dev1',
    'transformers': '5.14.1',
    'numpy': '1.26.4',
}
versions = {name: metadata.version(name) for name in expected_versions}
assert versions == expected_versions, (versions, expected_versions)

import flag_gems
import flaggems_vllm
import numpy as np
import torch
import triton
import vllm
import vllm_fl
from vllm.platforms import current_platform
from vllm_fl.utils import get_flag_gems_whitelist_blacklist

plugin_root = Path(os.environ['PLUGIN_ROOT']).resolve()
venv_root = Path(sys.prefix).resolve()
assert sys.prefix != sys.base_prefix, sys.executable
for command in ('pytest', 'vllm'):
    executable = shutil.which(command)
    assert executable and Path(executable).is_relative_to(venv_root / 'bin'), (command, executable)
assert Path(vllm_fl.__file__).resolve().is_relative_to(plugin_root)
for module in (vllm, flag_gems, flaggems_vllm):
    assert Path(module.__file__).resolve().is_relative_to(venv_root), module.__file__
assert current_platform.vendor_name == 'iluvatar'
assert hasattr(triton._C.libtriton, 'iluvatar')
distribution = metadata.distribution('flagtree')
assert any(Path(distribution.locate_file(entry)).resolve() == Path(triton.__file__).resolve() for entry in distribution.files or ())
assert torch.cuda.is_available() and torch.cuda.device_count() == 4
for device_index in range(4):
    assert torch.ones(1, device=f'cuda:{device_index}').cpu().item() == 1
array = np.arange(4, dtype=np.float32)
assert np.array_equal(torch.from_numpy(array).numpy(), array)
flagcx_root = Path(os.environ['FLAGCX_PATH'])
assert (flagcx_root / 'plugin/interservice/flagcx_wrapper.py').is_file()
ctypes.CDLL(str(flagcx_root / 'build/lib/libflagcx.so'))
from vllm_fl.distributed.device_communicators import flagcx

assert flagcx._flagcx_available
whitelist, blacklist = get_flag_gems_whitelist_blacklist()
assert not whitelist
assert {'slice', 'mm', 'mm_out'}.issubset(blacklist)
padding_mask = torch.zeros(8, dtype=torch.bool, device='cuda')
left = torch.randn((5, 65), dtype=torch.bfloat16, device='cuda')
right = torch.randn((65, 7), dtype=torch.bfloat16, device='cuda')
reference = torch.mm(left, right)
output = torch.empty_like(reference)
with flag_gems.use_gems(exclude=blacklist):
    keys = flag_gems.all_registered_keys()
    assert keys and not {'mm', 'mm.out', 'slice.Tensor'}.intersection(keys)
    padding_mask[:4].fill_(True)
    actual = torch.mm(left, right)
    torch.mm(left, right, out=output)
assert torch.equal(reference, actual) and torch.equal(reference, output)
assert padding_mask.cpu().tolist() == [True] * 4 + [False] * 4
if arguments.model:
    from transformers import AutoProcessor

    AutoProcessor.from_pretrained(arguments.model, local_files_only=True, trust_remote_code=True)
    index = json.loads((arguments.model / 'model.safetensors.index.json').read_text())
    missing = [name for name in set(index['weight_map'].values()) if not (arguments.model / name).is_file()]
    assert not missing, missing
print(json.dumps({
    'python': sys.executable,
    'versions': versions,
    'plugin_commit': subprocess.check_output(['git', '-C', str(plugin_root), 'rev-parse', 'HEAD'], text=True).strip(),
    'modules': {module.__name__: module.__file__ for module in (vllm, vllm_fl, flag_gems, flaggems_vllm, triton, torch)},
    'devices': [torch.cuda.get_device_name(index) for index in range(4)],
    'flagcx': str(flagcx_root),
    'effective_blacklist': blacklist,
    'model': str(arguments.model) if arguments.model else None,
}, ensure_ascii=False, indent=2))
print('PREFLIGHT_PASS: imports/devices/libraries/operator exclusions; model gate still required')
