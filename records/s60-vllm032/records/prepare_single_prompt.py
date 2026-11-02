import json
from pathlib import Path
root = Path(__file__).parent
rows = json.loads((root / 'results-nvidia-v1-eager-extended.json').read_text())
(root / 'arithmetic-prompt.json').write_text(json.dumps([rows[2]], ensure_ascii=False, indent=2))
