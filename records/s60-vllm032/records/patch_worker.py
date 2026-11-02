from pathlib import Path
p = Path('/workspace/vllm-plugin-FL/vllm_fl/worker/worker.py')
s = p.read_text()
s = s.replace('from vllm.v1.worker.utils import is_residual_scattered_for_sp, request_memory', 'from vllm.v1.worker.utils import request_memory')
start = s.index('        num_scheduled_tokens = scheduler_output.total_num_scheduled_tokens\n', s.index('    def execute_model('))
end = s.index('        if forward_pass and not get_pp_group().is_first_rank:', start)
s = s[:start] + s[end:]
s = s.replace('                    all_gather_tensors=all_gather_tensors,\n', '')
s = s.replace('            all_gather_tensors=all_gather_tensors,\n', '')
p.write_text(s)
