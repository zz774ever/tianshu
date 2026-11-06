import hashlib
import json
from pathlib import Path


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


root = Path('/opt/vllm-plugin-FL')
gate = root / 'tools/adaptation-gate-cases'
source = {path.relative_to(root).as_posix(): checksum(path)
          for path in sorted(gate.rglob('*'))
          if path.is_file() and '__pycache__' not in path.parts}
Path('/results/gate-source-sha256.json').write_text(json.dumps(source, indent=2) + '\n')
models = {}
for name in ['Qwen3.6-27B', 'Qwen3.6-35B-A3B']:
    directory = Path('/models') / name
    files = ['config.json', 'preprocessor_config.json', 'processor_config.json',
             'tokenizer_config.json', 'model.safetensors.index.json']
    models[name] = {
        'config': json.loads((directory / 'config.json').read_text()),
        'metadata_sha256': {name: checksum(directory / name)
                            for name in files if (directory / name).is_file()},
        'weight_files': [{'name': path.name, 'bytes': path.stat().st_size}
                         for path in sorted(directory.glob('*.safetensors'))],
        'weight_content_sha256_computed': False,
    }
Path('/results/model-files.json').write_text(json.dumps(models, indent=2) + '\n')
