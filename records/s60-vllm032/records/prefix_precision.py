"""Teacher-forced, identical-prefix probe at observed cross-device divergences."""
import argparse
import json
from pathlib import Path
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--reference', required=True)
    p.add_argument('--candidate', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--native-ops', action='store_true')
    a = p.parse_args()
    ref = json.loads(Path(a.reference).read_text())
    target = json.loads(Path(a.candidate).read_text())
    tokenizer = AutoTokenizer.from_pretrained(a.model)
    cases = []
    for r, t in zip(ref, target):
        assert r['prompt'] == t['prompt']
        pos = next((i for i, (x, y) in enumerate(zip(r['token_ids'], t['token_ids'])) if x != y), None)
        if pos is not None:
            ids = tokenizer.encode(r['prompt']) + r['token_ids'][:pos]
            cases.append(dict(prompt=r['prompt'], position=pos + 1,
                              prompt_token_ids=ids, reference_next=r['token_ids'][pos],
                              candidate_next=t['token_ids'][pos]))
    assert cases, 'No divergent prefixes to probe'
    extra = {'compilation_config': {'custom_ops': ['none']}} if a.native_ops else {}
    llm = LLM(model=a.model, enforce_eager=True, dtype='bfloat16',
              tensor_parallel_size=1, max_model_len=512, max_num_seqs=4,
              gpu_memory_utilization=0.35, **extra)
    try:
        outputs = llm.generate([{'prompt_token_ids': c['prompt_token_ids']} for c in cases],
                               SamplingParams(temperature=0, max_tokens=1, logprobs=20))
        for c, out in zip(cases, outputs):
            result = out.outputs[0]
            c['selected'] = list(result.token_ids)
            c['top'] = {str(k): {'logprob': v.logprob, 'rank': v.rank,
                                  'text': v.decoded_token}
                        for k, v in result.logprobs[0].items()}
        Path(a.output).write_text(json.dumps(cases, indent=2, ensure_ascii=False))
        print(json.dumps(cases, indent=2, ensure_ascii=False), flush=True)
    finally:
        llm.llm_engine.engine_core.shutdown()


if __name__ == '__main__':
    main()
