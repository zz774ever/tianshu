import argparse
import hashlib
import json
import sys
from importlib import metadata
from pathlib import Path


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("destination")
arguments = parser.parse_args()
import torch
import triton

package_names = [
    "flagtree", "torch", "vllm", "vllm-plugin-FL", "flag-gems",
    "flaggems-vllm", "numpy", "transformers", "tokenizers", "huggingface-hub",
]
packages = {}
for name in package_names:
    try:
        packages[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        packages[name] = None
torch_root = Path(torch.__file__).parent
torch_paths = [torch_root / "__init__.py", *sorted(torch_root.glob("_C*.so"))]
result = {
    "python": sys.executable,
    "python_version": sys.version,
    "packages": packages,
    "all_distributions": dict(sorted(
        (distribution.metadata["Name"], distribution.version)
        for distribution in metadata.distributions()
        if distribution.metadata.get("Name")
    )),
    "triton_runtime": triton.__version__,
    "triton_path": triton.__file__,
    "torch_hashes": {str(path): digest(path) for path in torch_paths},
}
Path(arguments.destination).write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"packages": packages, "triton_runtime": triton.__version__}))
