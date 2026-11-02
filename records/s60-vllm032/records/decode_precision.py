"""Capture original five-prompt decode candidates without replacing decode by prefill."""
import argparse
import os
if os.environ.get('S60_REPORT_TOPK_CPU') == '1':
    import report_topk_cpu
if os.environ.get('CAPTURE_HEAD_DIR'):
    import capture_head
if os.environ.get('CAPTURE_LAYERS_PATH'):
    import capture_layers
if os.environ.get('CAPTURE_ATTENTION_CACHE'):
    import capture_attention_cache
if os.environ.get('S60_SINGLE_ROUND_RMS') == '1':
    import single_round_rms
if os.environ.get('S60_ORACLE_VARIANCE') == '1':
    import oracle_variance_rms
import json
from pathlib import Path
from vllm import LLM, SamplingParams


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--prompts', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--head-dtype', choices=('model', 'float32'))
    p.add_argument('--native-ops', action='store_true')
    a = p.parse_args()
    prompts = [r['prompt'] for r in json.loads(Path(a.prompts).read_text())]
    extra = {'compilation_config': {'custom_ops': ['none']}} if a.native_ops else {}
    if a.head_dtype is not None:
        extra['hf_overrides'] = {'head_dtype': a.head_dtype}
    llm = LLM(model=a.model, tensor_parallel_size=1, enforce_eager=True,
              dtype='bfloat16', max_model_len=512, max_num_seqs=4,
              gpu_memory_utilization=0.35, **extra)
    try:
        outputs = llm.generate(prompts, SamplingParams(temperature=0, max_tokens=32, logprobs=20))
        rows = []
        for out in outputs:
            r = out.outputs[0]
            rows.append({'prompt': out.prompt, 'token_ids': list(r.token_ids), 'text': r.text,
                         'top': [{str(k): {'logprob': v.logprob, 'rank': v.rank,
                                          'text': v.decoded_token} for k, v in step.items()}
                                 for step in r.logprobs]})
        Path(a.output).write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        print('Saved', a.output, flush=True)
    finally:
        llm.llm_engine.engine_core.shutdown()


if __name__ == '__main__':
    main()
