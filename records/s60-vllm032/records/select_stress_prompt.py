"""Select the genuine failing Japan request for an aligned single-request probe."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent
rows = json.loads((root / 'stress-prompts.json').read_text())
selected = [r for r in rows if 'capital of Japan' in r['prompt']]
assert len(selected) == 1
(root / 'japan-prompt.json').write_text(json.dumps(selected, ensure_ascii=False))
print(selected)
