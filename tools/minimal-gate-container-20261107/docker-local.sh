#!/usr/bin/env bash
set -euo pipefail
exec /workspace/minimal-gate-container-20261107/runtime/docker/docker --host unix:///workspace/minimal-gate-container-20261107/runtime/docker.sock "$@"
