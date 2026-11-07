#!/usr/bin/env bash
set -euo pipefail
export GATE_DEVICES=12,13,14,15
source /opt/gate/gate-env.sh
export MODEL_PATH=/models/Qwen3.6-35B-A3B
export SERVED_MODEL_NAME=qwen-gate
export PORT=8147
export SERVER_PID_FILE=/results/quality-diagnosis/compiled-server.pid
export VLLM_CACHE_ROOT=/results/quality-diagnosis/compiled-cache
export TRITON_CACHE_DIR=/results/Qwen3.6-35B-A3B-graph/triton-cache
export TORCHINDUCTOR_CACHE_DIR=/results/Qwen3.6-35B-A3B-graph/inductor-cache
export GRAPH_COMPILATION_CONFIG='{"mode":3,"cudagraph_mode":"NONE","cudagraph_capture_sizes":[1,2,4,8,16,32]}'
mkdir -p /results/quality-diagnosis
cd /opt/vllm-plugin-FL
exec bash tools/adaptation-gate-cases/run_serve_graph.sh
