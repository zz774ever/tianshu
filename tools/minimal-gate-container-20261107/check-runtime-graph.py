from pathlib import Path

import torch

torch.cuda.init()
values = torch.ones(1, device='cuda')
torch.cuda.synchronize()
graph = torch.cuda.CUDAGraph()
stream = torch.cuda.Stream()
with torch.cuda.graph(graph, stream=stream):
    output = values + 1
graph.replay()
torch.cuda.synchronize()
assert output.item() == 2
for line in Path('/proc/self/maps').read_text().splitlines():
    if any(name in line for name in ['libcudart.so', 'libcuda.so', 'libixthunk.so']):
        print(line.split()[-1])
print('RUNTIME_GRAPH_CAPTURE_REPLAY_PASS')
