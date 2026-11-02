"""Replay identical Q and native attention parameters, changing only real KV."""
from pathlib import Path
import torch
from flash_attn.vllm_flash_attn import flash_attn_varlen_func
root=Path(__file__).resolve().parent
rows={s:torch.load(root/f'cache-japan-{s}.pt',map_location='cpu',weights_only=True)
      for s in ('single','batch')}
assert torch.equal(rows['single']['query'],rows['batch']['query'])
q=rows['single']['query'].to('gcu')
cuq=torch.tensor([0,1],dtype=torch.int32,device='gcu')
cuk=torch.tensor([0,25],dtype=torch.int32,device='gcu')
outputs={}
for side,data in rows.items():
    k,v=data['kv'].to('gcu').chunk(2,dim=-1)
    actual=[]
    for repeat in range(2):
        y=flash_attn_varlen_func(q=q,k=k.contiguous(),v=v.contiguous(),
            max_seqlen_q=1,cu_seqlens_q=cuq,max_seqlen_k=25,cu_seqlens_k=cuk,
            softmax_scale=data['scale'],causal=True,fa_version=2)
        actual.append(y.cpu())
    assert torch.equal(*actual), 'Non-deterministic fixed-input replay'
    outputs[side]=actual[0]
    delta=actual[0].reshape_as(data['output']).float()-data['output'].float()
    print(side,'replay versus captured native: neq',int((delta!=0).sum()),'max',delta.abs().max().item(),flush=True)
delta=outputs['single'].float()-outputs['batch'].float()
print('fixed-shape cache swap: neq',int((delta!=0).sum()),'max',delta.abs().max().item(),flush=True)
torch.save(outputs,root/'japan-attention-cache-swap.pt')
