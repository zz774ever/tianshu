import os
from datetime import timedelta


def main():
    import torch
    from torch import distributed
    from vllm_fl.distributed.device_communicators.flagcx import PyFlagcxCommunicator

    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    distributed.init_process_group("gloo", timeout=timedelta(seconds=120))
    communicator = None
    try:
        world_size = distributed.get_world_size()
        assert world_size >= 2, "Use torchrun with at least two processes"
        communicator = PyFlagcxCommunicator(distributed.group.WORLD, torch.device("cuda", local_rank))
        assert communicator.available and not communicator.disabled, getattr(communicator, "init_error", None)
        tensor = torch.full((1024,), float(distributed.get_rank() + 1), device=f"cuda:{local_rank}")
        result = communicator.all_reduce(tensor)
        torch.cuda.synchronize()
        expected = world_size * (world_size + 1) / 2
        assert torch.equal(result, torch.full_like(result, expected)), result[:4]
        print(f"FLAGCX_PASS rank={distributed.get_rank()} world_size={world_size} values={result[:4].tolist()}", flush=True)
        distributed.barrier()
    finally:
        if communicator is not None:
            communicator.destroy()
        distributed.destroy_process_group()


if __name__ == "__main__":
    main()
