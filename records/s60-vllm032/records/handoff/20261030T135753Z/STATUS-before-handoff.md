# S60 / vLLM 0.32.0 adaptation — IN PROGRESS, NOT ACCEPTED

## Immutable scope
- Project `/workspace/vllm-plugin-FL`, branch `adapt/vllm032-from-050` (base `64c9d21`).
- Actual model `/models/Qwen3-0.6B`, BF16; no substitute weights.
- Official upstream `v0.32.0`, commit `5df63a7203cdb9328d824a27b682e77c7b9928be`, empty build at `/workspace/s60-adaptation/src/vllm`. Upstream source not patched.
- Logs and diagnostic scripts below are relative to `/workspace/s60-adaptation` and are not production plugin files.

## Implemented in plugin
- Three-way reconciliation of FL Worker/ModelRunner against upstream 0.28 and target 0.32, preserving FL device/stream/graph/dispatch facilities.
- Removed obsolete imports/PP contracts; CUDA allocator settings restricted to CUDA.
- GCU native IR priorities; 0.32 attention cache layout and block-size contracts.
- Stride-aware Triton cache scatter for standardized KV views, preserving packed FlagGems path and index bounds.
- Narrow GCU Inductor ABI/resource/i64 option adapters, with regression tests.
- GCU FlagCX device context, current stream and legacy stream-handle bridge.

## Personally observed supporting tests
- `logs/unit-regression-9.log`: 66 passed, 1 skipped (earlier combined focused run).
- `logs/unit-inductor-2.log`: 87 passed; real embedding/RMS compiled proxy also completed (`logs/embedding-proxy.log`).
- `logs/unit-full032-warmup.log`: 1160 passed, 229 skipped, 1 collection error (`torch_npu` absent), including latest FlagCX and GCU dispatch warmup changes. Exact `pytest tests/ -q` was also executed (`logs/tests-all032-warmup.log`), exiting 2 on collection, not a full-suite pass.
- `logs/unit-worker-warmup.log`: 9 passed, including execution of the actual pre-trace dispatch warmup guard for GCU/NPU/CUDA and disabled compilation.
- `logs/unit-flagcx-gcu.log`: 2 passed after FlagCX stream edits.
- `logs/flagcx-collective.log`: real two-rank GCU FlagCX all-reduce, both ranks assert all 16 results equal 3.0. Runtime root `flagcx-runtime` uses authenticated historical wrapper and installed wheel library. Qwen3-0.6B BF16 TP=2 eager also completed using FlagCX (`logs/smoke-tp2-flagcx.log`); both 16-token outputs in `results-tp2-flagcx.json` exactly match TP=1 eager.

## Historical correctness investigation (superseded by latest update below)
- Eager two-prompt greedy generation completed twice with identical token IDs (`results-tp1-graphFalse.json`, `results-eager-current.json`). Outputs begin ` France...` and ` lazy dog...`.
- Graph generation completed but outputs are anomalous (`results-tp1-graphTrue.json`). Compiled/no-capture generates EXACTLY the same anomalous outputs (`results-compiled-no-capture.json`). Neither matches eager.
- Therefore compilation success is NOT correctness. Controlled comparison localizes the discrepancy to the compiled path, not graph replay alone. Root cause remains open.
- Controlled `backend=eager` plus explicit `custom_ops=['none']` matches eager exactly (`results-compile-eager-native.json`), implicating Inductor rather than vLLM graph splitting alone.
- `custom_ops=['all']` first hit lazy dispatch RLock; GCU pre-trace warmup fixes that obstacle, but the next run fails Dynamo tracing of FlagGems RMSNorm logging. This is not an accepted workaround.
- Actual upstream native normalization microtests (`operator-diff.json`) show small BF16 rounding deltas; residual addition matches exactly. These do not establish the cause of anomalous generation.
- Real-model subgraph differential (`logs/subgraph-probe3.log`) localized large errors to Q/K while V had only small BF16 deltas; embedding/residual outputs were exact.
- CPU-oracle lookup test (`logs/index-diff.log`) proves compiled GCU int64 `index_select` reads incorrect rows (FP32 max error 2304, BF16 2312); eager int64 and eager/compiled int32 are exact. Generated-code test (`logs/index-codegen.log`) reads indices `[7,0,8,0,9,0,...]` from int64 `[7,8,9,...]`, consistent with incorrect 32-bit element addressing. A cast inside the compiled graph does NOT fix this.
- Actual upstream RoPE with an int32 input ABI (`logs/rotary-i32-abi-proxy.log`) reduces errors to BF16 rounding (max 0.03125 across 10 shape/offset cases), versus up to 7.46875 with int64 ABI. This is a microtest, NOT yet an end-to-end fix.
- Source audit identifies unsafe global dtype replacement in TorchGCU `GCUCompileHelper.compile_to_module` (`backend_register.py:1473-1481`): `int64/i64` become `int32/i32` without converting tensor storage. Diagnostic `preserve_codegen.py` delegates to the installed Torch native helper instead; fresh-cache CPU-oracle lookup tests are exact for all eight dtype/ABI/mode combinations (`logs/index-diff-preserve-fresh.log`). This is not yet a production fix.
- Model validation with this helper first failed on vLLM artifact serialization (`logs/smoke-preserve-codegen.log`), before inference. Two diagnostic runs are in progress: compile cache disabled with independent caches (`logs/smoke-preserve-codegen-v2.log`), and fresh cache with supported Torch cache-key tag plus serialization diagnostics (`logs/smoke-preserve-save.log`). Neither has yet established model correctness.

## Latest production-code and validation update
- Plugin delegates TorchGCU code generation to native `GraphLowering._compile_to_module`, retaining dtype ABIs; salts both Torch compiler and vLLM config cache keys. CPU-oracle lookup regression is exact in all eight tested combinations.
- Focused regression: 68 passed (`logs/unit-codegen-config.log`). Full unit invocation: 1165 passed, 229 skipped, 1 collection error (`torch_npu`, `logs/unit-full-codegen.log`). Exact `pytest tests/ -q` exited 2 at collection (`logs/tests-all032-codegen.log`), not a full-suite pass.
- Production Graph generation completed (`results-graph-production.json`). Prompt 1 matches eager through token 10 then differs at token 11; prompt 2 matches all 16 tokens. Earlier diagnostic results above are historical, not current production status.
- Spawned-engine differential (`logs/codegen-subgraph-v2.log`): 292 initialized outputs, worst absolute-error/reference-peak ratio 0.0115385. Previous large Q/K errors disappear, but remaining BF16 drift is unresolved.
- Documented Torch rounding preservation (`TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1`) completed: compiled/no-capture and uninstrumented Graph both exactly match eager on the two prompts, 32 tokens total (`results-codegen-eager-rounding.json`, `results-graph-rounding.json`; verified with `compare_tokens.py`). Subgraphs still have numeric deltas; this is limited token-regression evidence, NOT NVIDIA alignment. Option is diagnostic/environment-only, not enabled by default in production code. Extended regression completed: five prompts (English, Chinese, arithmetic, code), 32 tokens each, all 160 tokens match exactly (`results-eager-extended.json`, `results-graph-extended.json`; verified with `compare_tokens.py`, exit 0). This remains a same-hardware comparison, not NVIDIA ground truth.
- Actual eager OpenAI HTTP API: two concurrent completions each returned HTTP 200 and 16 tokens; streaming emitted `[DONE]` and identical text to nonstreaming (`results-serve-eager.json`, `logs/check-serve-eager.log`). Graph serving with `TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1` also passed the same actual HTTP concurrency/streaming assertions (`results-serve-graph.json`, `logs/check-serve-graph.log`); this does not establish NVIDIA precision alignment.

## Dependencies and acceptance blockers
- Actual v0.32 CI setup passed (`logs/ci-setup-v032-local-transport.log`): pinned package checks, editable plugin installation, canonical FlagGems-vllm installation, compiler/index-fill verification, final imports, and accelerator availability. GitHub TLS interrupted the first fetch. A shallow official v0.2.0 clone was verified at exact commit `b5c2c2249319277ccda4d41aa0f65164bd9b2a19`; command-scoped Git URL rewriting used this local repository as transport, with unchanged official package URL and commit. No global transport configuration was added.
- Official NVIDIA vLLM 0.32.0+cu129 reference outputs have now been obtained on RTX 4090; CUDA runtime execution passed. All ten model/tokenizer files were SHA-256 verified. V1 and V2 reference runners match all 160 tokens. Strict comparison to S60 eager and Graph fails: Paris, fox and Chinese prompts match all 32 tokens; arithmetic first diverges at token 7 and code at token 13 (1-based). V1 with `VLLM_USE_FLASHINFER_SAMPLER=0` completed cleanly and reproduces these mismatches; runner selection does not eliminate them. Reference JSON: `results-nvidia-v1-eager-extended.json`. Strict precision acceptance is still open.
- Full adaptation gate (`tools/adaptation-gate-cases`, both Qwen3.6 models, eager/graph, text/image/concurrency) has NOT been executed; no full three-stack acceptance claim.
- Eager and Graph serving/concurrency/streaming passed the limited tests above; Graph required the documented rounding environment option. The complete suite remains unverified. CI setup and Docker source recipe now target vLLM 0.32.0, and actual setup passed in this environment; Docker image build/publication and workflow execution remain unverified. The CI image configuration still references the historical 0.28 digest and must not be treated as a validated 0.32 image.
- Do not use this branch's compiled/graph mode for correctness-sensitive work until discrepancy is resolved and precision verified.

## Reproduce latest verified comparison
```bash
cd /workspace/vllm-plugin-FL
VLLM_PLUGINS=fl TOPS_VISIBLE_DEVICES=0 python /workspace/s60-adaptation/smoke.py --extended --output /workspace/s60-adaptation/results-eager-extended-rerun.json
TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1 VLLM_PLUGINS=fl TOPS_VISIBLE_DEVICES=2 python /workspace/s60-adaptation/smoke.py --graph --extended --output /workspace/s60-adaptation/results-graph-extended-rerun.json
python /workspace/s60-adaptation/compare_tokens.py /workspace/s60-adaptation/results-eager-extended-rerun.json /workspace/s60-adaptation/results-graph-extended-rerun.json
```
The rounding environment variable is required for the verified Graph comparison; default Graph without it still diverged. Do not treat this as an unconditional Graph precision pass. The temporary eager HTTP server was stopped after validation.

NVIDIA reference installation and generation have completed in `/root/autodl-tmp/s60-reference/venv`, leaving the existing host Python unchanged. Official vLLM 0.32.0+cu129 and PyTorch 2.13.0+cu129 executed successfully on RTX 4090 driver 560.35.03. Remote process inspection confirmed no remaining installer, downloader or smoke process; V1 generation logs show clean shutdown. Do not repeat installation or reference generation just because a local background job handle was lost. `logs/nvidia-reference-complete.log` records initial installation and V2 inference; remote `nvidia-v1-native-sampler.log` records the controlled V1 run. The strict comparison remains failed as documented above. Full hardware-adaptation CI and the broader gate remain unverified.

## NVIDIA divergence diagnosis: original decode

`decode-nvidia.json` and `decode-s60.json` record top-20 probabilities for the original five-prompt, 32-token decode. Both runs reproduce all 160 tokens of their respective earlier baselines. S60 uses diagnostic `report_topk_cpu.py` only for probability reporting, avoiding the multi-minute Triton `topk_stage2_kernel` compilation; model execution and greedy selection remain on device.

At arithmetic token 7 (1-based), NVIDIA tokens 13 and 382 have equal logprob; S60 token 382 exceeds token 13 by 0.125. At code token 13, NVIDIA tokens 50 and 1336 have equal logprob; S60 token 1336 exceeds token 50 by 0.125. Evidence: `decode-comparison.json`.

Independent GCU argmax tests passed the first-index tie contract for FP32/BF16 and lengths 1024/151936 (`logs/argmax-ties.log`). The evidence identifies a logits difference, not an argmax tie violation. The responsible model operator is still unknown. A teacher-forced prefill probe changed NVIDIA selections too, so it cannot replace original decode diagnosis. Strict alignment remains failed.

Focused follow-up regression: 86 passed in 12.35 s (`logs/unit-nvidia-followup.log`). The controlled custom-ops-disabled run completed and reproduced all 160 S60 tokens (`decode-s60-native.json`), retaining both NVIDIA mismatches. Disabling these custom operations did not eliminate the discrepancy.

Actual `lm_head` captures on both devices also reproduced each device's 160-token baseline. Across 16 captured calls per device, four candidate logits exactly matched a CPU float64 projection using the same actual hidden states and weight rows, rounded back to BF16 (all measured maximum errors were zero). This limits evidence against the sampled head GEMM; it does not establish agreement of upstream hidden states. Scheduler rows differed between devices, so cross-device hidden-state comparisons require matching actual input IDs and positions. Evidence: `head-s60/`, `head-nvidia/`, `logs/head-analysis.log`.

## Aligned first-layer investigation

`layers-nvidia.pt` and `layers-s60.pt` contain the same actual 13-token arithmetic prefill. `analyze_layers.py` asserts equal input IDs and positions before comparison. Embedding outputs are exact. The first differing output is layer 0 input RMSNorm (max absolute difference 0.015625, RMS 0.000603106).

CPU replay with the actual embedding and checkpoint norm weight (`analyze_rms.py`, `logs/rms-analysis.log`) distinguishes rounding contracts: NVIDIA output exactly equals FP32 normalization and weight multiplication followed by BF16 conversion. S60 output exactly equals normalization converted to BF16 before weight multiplication. The two contracts differ at 3,616 of 13,312 elements. FP64 replay gives the same distinction. Target vLLM native IR explicitly casts before multiplying; this explains this first local difference but has not yet proved the cause of the generated-token mismatches. Diagnostic single-round RMSNorm runs have completed (results below); no production RMSNorm change has been made.

### Controlled RMS rounding results (diagnostic only)

The corrected diagnostic intercepts `RMSNormFL.forward_oot`, not just upstream `forward_native`. On the aligned actual arithmetic prefill, the first RMS output and QKV input now match NVIDIA exactly (`logs/layers-single-v2-analysis.log`). First remaining difference is QKV output, max 0.00390625. This verifies a local normalization rounding difference, not an end-to-end solution.

Both full five-prompt diagnostic variants were run: single-round weight multiplication with FP32 residual accumulation, and single-round multiplication with residual sum rounded before variance as in upstream CUDA kernels. Neither passes strict alignment. In both, fox, Chinese and code match all 32 tokens; arithmetic first differs at token 7 and Paris newly differs at token 11. Evidence: `logs/compare-single-extended.log`, `logs/compare-cuda-rms-extended.log`. No production RMS change was applied: the local improvement does not justify a cross-prompt regression.

Using identical captured QKV inputs and real checkpoint weights, CPU float64 projection rounded to BF16 differs from NVIDIA at 41/53,248 elements (max 0.00390625) and S60 at 3/53,248 (max 0.0001220703125). Evidence: `logs/qkv-oracle.log`. These oracle counts alone do not identify the GPU accumulation algorithm or explain decode divergence. Standalone NVIDIA actual-QKV replay completed (`logs/probe-nv-qkv-v2.log`): BF16 GEMM reproduces the captured output exactly with reduced-precision reduction both enabled and disabled; separate Q/K/V projections also reproduce it. FP32 GEMM differs from CPU float64 at 8 elements, versus 41 for BF16. Thus neither that reduction flag nor concatenated projection explains the captured difference. Existing ground truth is unchanged.

### Native FP32 head controlled comparison

Both platforms ran vLLM's native `hf_overrides={'head_dtype': 'float32'}` on the same five prompts, 32 greedy tokens each, without RMS diagnostics. Four prompts match all 32 tokens. Paris alone differs at token 11: NVIDIA token 4126 (` center`) versus S60 token 3283 (` city`). The reference-minus-candidate logprob margin is +0.039211273 on NVIDIA and -0.030513763 on S60. Evidence: `decode-fp32head-comparison.json`, `decode-{nvidia,s60}-fp32head.json`. Removing BF16 head rounding exposes a non-tie ranking difference but does not by itself achieve alignment. NVIDIA's FP32-head output also differs from its original BF16 baseline at Paris 11, arithmetic 7 and code 13. This diagnostic configuration does not replace the original BF16 acceptance gate.


## Current production RMS candidate and wider regression

The working tree now contains a GCU RMSNorm candidate that performs normalization and weight multiplication in FP32 before converting once, including the FlagGems GCU dispatch adapter. Earlier statements above that no production RMS change exists describe the historical diagnostics. Focused normalization/rotary/IR tests pass: 48 passed in 11.50 s (`logs/unit-gcu-normalization-v3.log`). This candidate is not accepted for release.

With the native FP32 head and this production candidate, all 160 tokens of the original five prompts match NVIDIA (`decode-s60-fp32head-production.json`, reference `decode-nvidia-fp32head.json`). On ten additional prompts only eight match; Japan first diverges at token 14, JSON at token 16 (`stress-fp32head-comparison.json`). Their candidate logprob margins change sign, so these are not exact ties. This configuration does not pass general precision validation.

The original BF16-head gate also remains failed with this candidate: arithmetic first differs at token 7 and Paris newly differs at token 11; code, fox and Chinese match (`compare-bf16head-production.json`). The Paris regression prevents promotion of the local RMS improvement as a validated fix.

Cross-device decode-call-14 captures were rejected by `analyze_layers.py` because actual input IDs and positions differed. NVIDIA captured IDs [34615, 44063, 3557, 686], positions [23, 25, 24, 22]; S60 captured IDs [34615, 105773, 3557, 686], positions [23, 24, 24, 22]. Comparing equal model call ordinals in independently scheduled batches is invalid for causal operator diagnosis. The next controlled probe isolates the original Japan prompt before comparing aligned decode inputs.

### Single-request versus batch control

The isolated original Japan prompt completed on both devices with the production RMS candidate and FP32 head. All 32 tokens match cross-device. NVIDIA single-request output also matches its own ten-prompt batch; S60 single-request output differs from its own batch starting at token 14. Evidence: `japan-probe-comparison.json`, actual `analyze_japan_probe.py` output. This demonstrates batch-dependent behavior in the observed S60 configuration, not an accepted precision fix.

Single-request call-14 captures align at input token 271, position 24. First normalization is exact, QKV has a small difference, and final hidden states still differ despite matching selected tokens (`logs/layers-japan14-analysis.log`). Equal selected tokens do not imply identical internal tensors. A same-S60 single/batch comparison is now targeting token 271 at position 24, rather than equal call ordinals; complete prior histories must also be checked before attributing a causal difference.

### Historical KV localization and controlled replay

Actual valid-cache capture at layer 7, Japan input token 271 at position 24: Q is identical; of 25 cached positions, only position 1 differs (554 BF16 elements, maximum absolute difference 0.0625). The attention outputs differ in 44 elements, max 0.001953125 (`logs/japan-cache-analysis.log`). Thus current-step matching Q/K/V alone did not establish matching attention inputs: historical KV matters.

Controlled native attention replay with fixed Q, lengths, layout and parameters, swapping only these two real KV histories, exactly reproduces each captured output, including all 44 differences. Repeated fixed-input calls agree (`logs/japan-attention-cache-swap.log`, `replay_japan_attention.py`). This proves the historical KV difference is sufficient for this observed attention-output difference. It does not yet identify the source of the prefill KV difference.

The capture run preserves the Japan output in both single and batch modes. The full batch does not preserve all other outputs: sky differs at token 29 and JSON at token 16 relative to the earlier S60 batch. These variations are recorded in `logs/cache-batch-baseline-check.log`; no overall batch preservation claim is made. Independent prefill captures are tracing the complete, unmodified 12-token Japan prompt to locate where cached position 1 first differs.

Prefill localization: the entire 12-token Japan prompt aligns (offset 43 in a 55-token batch). Boundaries of layers 0–5 match exactly. At layer 6, attention, QKV projections and both inputs to post_attention_layernorm match exactly. The norm output differs in one BF16 element at prompt position 1 (max 0.0009765625); its residual output matches. This propagates through MLP into 164 differences (max 0.00390625). Evidence: `logs/japan-prefill-layer6-analysis.log`. The earlier inference that the current decode attention kernel itself caused the batch discrepancy is not supported; the history originates earlier, at this normalization boundary. A standalone replay of the actual norm inputs is checking batch-shape-dependent reduction.

The standalone RMS hypothesis did not reproduce the model-run discrepancy: replaying both original input shapes and individual rows gives identical selected outputs, also matching CPU FP32/FP64 rounded references. The single replay differs from its earlier model capture by one element; the batch replay matches its capture. Twenty repeated calls agree, and inference_mode does not change the result (`logs/prefill-rms-repeat.log`, `logs/prefill-rms-inference.log`). Consequently batch size alone is not established as the cause. Runtime norm weights, dispatch and input layout are being captured before changing production behavior.

Additional controlled reduction diagnosis: enabling the FL runtime alone reproduces the captured RMSNorm difference. Identical-input stage replay first diverges at the globally overridden FlagGems mean reduction (six FP32 values; maximum 5.96e-8), propagating to one BF16 output. Blacklisting `mean,mean_dim` restores that isolated native result, but does not pass end-to-end validation. Actual comparisons: FP32-head stress 7/10 exact (sky token 29, multiplication token 21, Japan token 14 differ); original BF16 3/5 exact (Paris token 11 and code token 13 differ, arithmetic now exact). Reports: `stress-no-gems-mean-comparison.json`, `bf16-no-gems-mean-comparison.json`. No global mean blacklist has been added to production defaults. Strict NVIDIA token alignment remains unpassed.

Independent registered RMS probe: `TRITON_GCU::demo.v0_rms_norm` executes its own Triton reduction and produces identical outputs before/after FL initialization and for the complete captured tensor versus its selected row. However, both executions retain the single CPU-FP64-rounded boundary difference at [1,262] (-0.2080078125 versus -0.208984375). Evidence: `logs/replay-registered-rms-v2.log`. Independent operator dispatch alone is not a validated fix. The installed vLLM-named fused GCU kernel also computes variance from the unrounded FP32 residual sum, so its source does not satisfy the pinned CUDA residual-rounding contract. No production changes were made for these probes.

The diagnostic CPU-FP64 variance-only substitution does not restore that isolated BF16 boundary after variance is rounded back to FP32 and GCU performs rsqrt/multiplication: actual [1,262] remains -0.2080078125, residual remains exact (`logs/replay-oracle-variance.log`, failed exact-output assertion). Therefore higher-accuracy variance alone is insufficient. A complete FP64 norm oracle is being used only as a causal diagnostic, not as a production implementation or substitute NVIDIA acceptance result.

Complete FP64 RMS diagnostic (real weights and prompts, CPU norm only): isolated capture replay passes all elements and exact residual (`logs/replay-oracle-full.log`). End-to-end comparison does not pass: original BF16 five prompts only 2/5 exact, Paris first mismatch 11, arithmetic 30, code 13 (`bf16-oracle-full-comparison.json`); FP32-head stress 9/10 exact, Japan and JSON now exact, but TCP/UDP first differs at 25 (`stress-oracle-full-comparison.json`). This falsifies the hypothesis that high-accuracy RMS alone is sufficient for the acceptance gate. The CPU diagnostic is not a production change. An identical-input replay on official NVIDIA fused RMS is checking the actual reference rounding rather than assuming CPU FP64 defines CUDA behavior.
