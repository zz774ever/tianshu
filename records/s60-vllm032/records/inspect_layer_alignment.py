import torch
from pathlib import Path
root=Path('/workspace/s60-adaptation')
for side in ('nvidia','s60'):
    d=torch.load(root/f'layers-{side}-stress14.pt',weights_only=True,map_location='cpu')
    print(side, 'ids',d['input_ids'].tolist(),'positions',d['positions'].tolist())
