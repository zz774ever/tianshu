from pathlib import Path
source = Path('/workspace/s60-adaptation/smoke.py').read_text()
assert "model='/models/Qwen3-0.6B'" in source
source = source.replace("model='/models/Qwen3-0.6B'", "model='/root/autodl-tmp/s60-reference/model'")
Path('/workspace/s60-adaptation/nvidia_smoke.py').write_text(source)
