import torch
from vllm_fl.worker.model_runner import ModelRunnerFL
original=ModelRunnerFL.__init__
def init(self,*args,**kwargs):
    original(self,*args,**kwargs)
    assert self.max_model_len < torch.iinfo(torch.int32).max
    self.positions=self.positions.to(torch.int32)
ModelRunnerFL.__init__=init
from smoke import main
main()
