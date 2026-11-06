#!/usr/bin/env bash
set -euo pipefail
root=/workspace/minimal-gate-container-20261107
bash "$root/docker-local.sh" create -it \
  --name fl-gate-minimal-20261107 \
  --hostname fl-gate-minimal \
  --shm-size=32g --privileged --network host \
  -v /dev:/dev \
  -v "$root/host-driver:/run/iluvatar-host-driver:ro" \
  -v /mnt/share/user_homes/models:/models:ro \
  -v "$root/inputs:/input:ro" \
  -v "$root/evidence:/results" \
  --workdir /opt/gate --entrypoint /bin/bash \
  harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18
bash "$root/docker-local.sh" start fl-gate-minimal-20261107
