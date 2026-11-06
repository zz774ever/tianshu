#!/usr/bin/env bash
set -euo pipefail
root=/workspace/minimal-gate-container-20261107
container=fl-gate-minimal-20261107
image=local/iluvatar-gate:pr674-7a94aee-gems55-20261107
python "$root/summarize-results.py" > "$root/evidence/package-gate-verification.json"
bash "$root/docker-local.sh" exec "$container" bash -c 'test -z "$(pgrep -f "^/usr/local/bin/python.*/usr/local/bin/vllm" || true)"'
bash "$root/docker-local.sh" exec "$container" bash -c 'rm -rf /tmp/gate-original-runtime /tmp/check-runtime-graph.py /tmp/torchinductor_root /root/.cache/vllm /root/.flaggems'
bash "$root/docker-local.sh" exec "$container" cp /input/gate-env.sh /input/run-one.sh /input/run-four.sh /input/inspect-env.py /input/provenance.json /opt/gate/
bash "$root/docker-local.sh" cp "$root/evidence/final-summary.json" "$container:/opt/gate/validation-summary.json"
bash "$root/docker-local.sh" exec "$container" bash -c 'test -f /opt/vllm-plugin-FL/tools/adaptation-gate-cases/run_test.sh; test -f /opt/FlagCX/build/lib/libflagcx.so; test -f /opt/FlagCX/plugin/interservice/flagcx_wrapper.py; python -c "import sys; assert sys.prefix == sys.base_prefix"'
bash "$root/docker-local.sh" stop "$container"
bash "$root/docker-local.sh" commit \
  --change 'LABEL org.opencontainers.image.description="PR674 minimal system-Python adaptation gate environment; external models and matching Iluvatar driver required"' \
  --change 'LABEL io.flagos.gate.known-quality-failure="true"' \
  --change 'WORKDIR /opt/gate' \
  "$container" "$image" > "$root/evidence/packaged-image-id.txt"
bash "$root/docker-local.sh" image inspect --format '{{.Id}} {{.Size}}' "$image" > "$root/evidence/packaged-image-identity.txt"
mkdir -p "$root/artifacts"
bash "$root/docker-local.sh" save --output "$root/artifacts/iluvatar-gate-pr674-7a94aee-gems55-20261107.tar" "$image"
tar -cf "$root/artifacts/gate-install-inputs-20261107.tar" -C "$root" inputs
cd "$root/artifacts"
sha256sum *.tar > SHA256SUMS
ls -lh *.tar
