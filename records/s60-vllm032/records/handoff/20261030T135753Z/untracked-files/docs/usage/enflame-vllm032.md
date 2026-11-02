# Enflame S60: vLLM 0.32.0 adaptation status

This branch targets official vLLM `v0.32.0`, commit
`5df63a7203cdb9328d824a27b682e77c7b9928be`, installed with
`VLLM_TARGET_DEVICE=empty`. The existing Enflame CI image and the deployment
instructions in `enflame.md` describe vLLM 0.28. They are not a validated
0.32 dependency image. Do not relabel that image as a 0.32 image.

The Qwen3-0.6B BF16 checks on S60 have completed eager generation, TP=2
with a real FlagCX collective, and eager/Graph HTTP concurrency and streaming.
A five-prompt greedy comparison (32 tokens per prompt) matched all 160 tokens
between eager and Graph when the rounding option below was enabled. These
checks compare S60 execution modes. Official NVIDIA vLLM 0.32.0+cu129
reference generation has now completed on RTX 4090 with identical, SHA-256
verified model files. Strict NVIDIA alignment failed: arithmetic first differs
at token 7 and code at token 13 (1-based); the other three prompts match all
32 tokens. NVIDIA V1 and V2 runners match all 160 tokens, so changing the
reference runner does not eliminate these differences.

The current working-tree GCU RMSNorm candidate changes normalization rounding.
With the original BF16 head, arithmetic still differs at token 7 and Paris newly
differs at token 11; code now matches. This Paris regression remains unresolved.
With the native FP32 head, the candidate matches all 160 tokens on the original
five prompts, but only eight of ten additional prompts match (Japan first differs
at token 14, JSON at token 16). Changing the head configuration does not replace
the original BF16 acceptance gate. The RMSNorm candidate is not release-validated.
No precision pass is claimed. These checks do not establish support for other
model architectures.

## Compiled execution

The plugin preserves integer pointer types during GCU Inductor code generation.
The vendor's global int64-to-int32 source replacement can otherwise corrupt
lookup addresses without converting the underlying tensor storage. Compiler
and vLLM cache keys distinguish the corrected generated code.

BF16 compiled execution also requires the following setting for the verified
Qwen3-0.6B comparison:

```bash
export TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1
```

Without that setting, default compiled generation diverged from eager.
It is an environment option, not a production default installed by the plugin.
Retain it for the tested configuration and independently verify precision for
each deployment. Successful compilation or HTTP readiness does not verify
output correctness.

## Outstanding acceptance

NVIDIA reference generation is complete, but strict precision alignment failed
as described above. Resolving that discrepancy, the full adaptation-gate
matrix, and 0.32 CI image validation remain open. The Dockerfile now pins the official
0.32.0 commit and CI setup requires `0.32.0+empty`; a new image has not been
built or published. Actual setup passed package checks, plugin and pinned
FlagGems-vllm installation, compiler verification, imports, and device checks.
The first GitHub fetch failed with a GnuTLS connection termination; the passing
run used a shallow official clone as transport after verifying the exact
pinned commit. The CI image configuration still references the historical
0.28 digest and requires a newly built and validated 0.32 image. Full unit execution also encountered
an unavailable optional `torch_npu` dependency during collection; supporting
passes do not constitute a complete suite pass.

Keep the vendor PyTorch, FlagTree, and FlagGems packages pinned when installing
an empty vLLM build. Install the plugin with `--no-build-isolation --no-deps`
to avoid replacing the vendor runtime. A release requires the same dependency
stack in CI and the deployed environment, plus completed precision and gate
results on the submitted commit.
