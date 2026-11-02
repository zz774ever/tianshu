import argparse
import json
from pathlib import Path
from vllm import LLM, SamplingParams
import os
if os.environ.get('S60_SUBGRAPH_PROBE') == '1':
    import subgraph_probe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--graph', action='store_true')
    parser.add_argument('--extended', action='store_true')
    parser.add_argument('--tp', type=int, default=1)
    parser.add_argument('--no-capture', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--native-ops', action='store_true')
    parser.add_argument('--backend')
    parser.add_argument('--custom-ops-all', action='store_true')
    args = parser.parse_args()
    config = {}
    if args.backend:
        config['backend'] = args.backend
    if args.no_capture:
        config['cudagraph_mode'] = 'NONE'
    if args.custom_ops_all:
        config['custom_ops'] = ['all']
    if args.native_ops:
        config['custom_ops'] = ['none']
    extra = {'compilation_config': config} if config else {}
    llm = LLM(model='/root/autodl-tmp/s60-reference/model', tensor_parallel_size=args.tp,
              enforce_eager=not args.graph, dtype='bfloat16',
              max_model_len=512, max_num_seqs=4, gpu_memory_utilization=0.35, **extra)
    try:
        prompts = ['Paris is the capital of', 'The quick brown fox jumps over the']
        if args.extended:
            prompts += ['What is 17 + 25? Answer briefly.',
                        '请简要介绍机器学习。',
                        'Write a Python function to reverse a list.']
        outputs = llm.generate(prompts, SamplingParams(temperature=0,
                               max_tokens=32 if args.extended else 16))
        results = [{'prompt': o.prompt, 'token_ids': list(o.outputs[0].token_ids),
                    'text': o.outputs[0].text} for o in outputs]
        assert len(results) == len(prompts)
        assert all(r['token_ids'] and r['text'].strip() for r in results)
        path = args.output or Path(__file__).parent / f'results-tp{args.tp}-graph{args.graph}.json'
        path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(results, flush=True)
    finally:
        llm.llm_engine.engine_core.shutdown()


if __name__ == '__main__':
    main()
