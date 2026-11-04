import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Qwen3-4B BF16 text smoke on the adapted runtime")
    parser.add_argument("--model", required=True)
    parser.add_argument("--tp", type=int, choices=(1, 2, 4), default=1)
    parser.add_argument("--graph", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error("Output exists; use a new path to preserve previous results")
    if not (Path(args.model) / "config.json").is_file():
        parser.error("Model directory must contain config.json")

    import vllm
    from vllm import LLM, SamplingParams

    assert vllm.__version__.split("+")[0] == "0.32.0", vllm.__version__
    options = {}
    if args.graph:
        options["compilation_config"] = {
            "mode": 0, "cudagraph_mode": "FULL", "custom_ops": ["all"],
            "ir_enable_torch_wrap": False,
        }
    model = LLM(
        model=args.model, tensor_parallel_size=args.tp,
        dtype="bfloat16", enforce_eager=not args.graph,
        max_model_len=512, max_num_seqs=2, gpu_memory_utilization=0.65,
        **options,
    )
    prompts = ["The capital of France is", "The speed of light in vacuum is approximately"]
    generated = model.generate(prompts, SamplingParams(temperature=0, max_tokens=16))
    assert len(generated) == len(prompts), "Missing generation results"
    records = []
    for result in generated:
        completion = result.outputs[0]
        assert completion.token_ids and completion.text.strip(), "Empty generation"
        records.append({"prompt": result.prompt, "text": completion.text,
                        "token_ids": list(completion.token_ids)})
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"status": "PASS", "vllm_version": vllm.__version__,
              "vllm_path": vllm.__file__, "model": args.model,
              "tp": args.tp, "graph": args.graph, "outputs": records}
    with output.open("x") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
