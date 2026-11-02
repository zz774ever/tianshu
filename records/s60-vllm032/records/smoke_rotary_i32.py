import torch
from vllm.model_executor.layers.rotary_embedding.base import RotaryEmbedding
original=RotaryEmbedding.forward_static
def bounded_positions(positions,query,key,head_size,rotary_dim,cos_sin_cache,is_neox_style):
    if query.device.type=='gcu' and cos_sin_cache.shape[0] <= torch.iinfo(torch.int32).max:
        positions=positions.to(torch.int32)
    return original(positions,query,key,head_size,rotary_dim,cos_sin_cache,is_neox_style)
RotaryEmbedding.forward_static=staticmethod(bounded_positions)
from smoke import main
main()
