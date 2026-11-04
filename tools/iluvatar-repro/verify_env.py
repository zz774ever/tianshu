import argparse
import ctypes
import json
import os
import sys
from importlib import metadata
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Verify the pinned Iluvatar 0.32 environment")
    parser.add_argument("--min-devices", type=int, default=1)
    args = parser.parse_args()
    if args.min_devices < 1:
        parser.error("--min-devices must be positive")

    import flag_gems
    import torch
    import triton
    import vllm
    import vllm_fl
    from vllm.platforms import current_platform

    expected = {
        "torch": "2.10.0+corex.4.5.0",
        "flagtree": "0.6.2a3+iluvatar3.6",
        "flag-gems": "5.3.5",
    }
    versions = {name: metadata.version(name) for name in expected}
    assert versions == expected, (versions, expected)
    assert vllm.__version__.split("+")[0] == "0.32.0", vllm.__version__
    assert metadata.version("vllm").split("+")[0] == "0.32.0"
    assert triton.__version__.startswith("3.6"), triton.__version__
    assert sys.prefix != sys.base_prefix, "Activate the isolated venv"
    assert Path(sys.prefix).resolve() in Path(vllm.__file__).resolve().parents, vllm.__file__
    repository = Path(os.environ["REPO_DIR"]).resolve()
    assert repository in Path(vllm_fl.__file__).resolve().parents, vllm_fl.__file__
    assert current_platform.vendor_name == "iluvatar", current_platform
    assert torch.cuda.is_available(), "CoreX device is unavailable"
    assert torch.cuda.device_count() >= args.min_devices, torch.cuda.device_count()
    for name, value in {"VLLM_PLUGINS": "fl", "USE_FLAGGEMS": "1", "GEMS_VENDOR": "iluvatar"}.items():
        assert os.environ.get(name) == value, (name, os.environ.get(name))

    distribution = metadata.distribution("flagtree")
    assert any(
        Path(distribution.locate_file(entry)).resolve() == Path(triton.__file__).resolve()
        for entry in distribution.files or ()
    ), f"Active Triton is not owned by FlagTree: {triton.__file__}"
    compiler = triton._C.libtriton
    assert hasattr(compiler, "iluvatar"), "FlagTree lacks the Iluvatar compiler backend"

    root = Path(os.environ["FLAGCX_PATH"]).resolve()
    library = root / "build/lib/libflagcx.so"
    assert (root / "plugin/interservice/flagcx_wrapper.py").is_file()
    ctypes.CDLL(str(library))
    from vllm_fl.distributed.device_communicators import flagcx

    assert flagcx._flagcx_available, "FlagCX Python wrapper is unavailable"
    source = json.loads(metadata.distribution("flaggems-vllm").read_text("direct_url.json") or "{}")
    assert source.get("vcs_info", {}).get("commit_id") == "b5c2c2249319277ccda4d41aa0f65164bd9b2a19", source
    print(json.dumps({
        "status": "PASS",
        "python": sys.executable,
        "versions": {**versions, "vllm": vllm.__version__, "triton": triton.__version__},
        "paths": {"vllm": vllm.__file__, "plugin": vllm_fl.__file__,
                  "flag_gems": flag_gems.__file__, "triton": triton.__file__, "flagcx": str(library)},
        "devices": torch.cuda.device_count(),
        "device_name": torch.cuda.get_device_name(0),
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
