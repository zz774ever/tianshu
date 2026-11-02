import torch
from pathlib import Path
root = Path(__file__).resolve().parent
for side in ('nvidia', 's60'):
    data = torch.load(root / f'layers-{side}-japan14.pt', weights_only=True, map_location='cpu')
    print(side, 'ids', data['input_ids'].tolist(), 'positions', data['positions'].tolist())
