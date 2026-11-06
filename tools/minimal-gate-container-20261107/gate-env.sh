#!/usr/bin/env bash
export CUDA_VISIBLE_DEVICES=${GATE_DEVICES:-4,5,6,7}
export COREX_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"
export VLLM_PLUGINS=fl
export USE_FLAGGEMS=1
export GEMS_VENDOR=iluvatar
export FLAGCX_PATH=/opt/FlagCX
export PYTHONPATH=/opt/vllm-plugin-FL
export LD_LIBRARY_PATH=/opt/FlagCX/build/lib:/usr/local/corex/lib64:/usr/local/openmpi/lib:/usr/local/lib
if [[ -f /run/iluvatar-host-driver/libcuda.so.1 ]]; then
    export LD_LIBRARY_PATH="/run/iluvatar-host-driver:$LD_LIBRARY_PATH"
fi
export VLLM_FL_FLAGOS_BLACKLIST_APPEND=slice,mm,mm_out
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export TENSOR_PARALLEL_SIZE=4
export MAX_MODEL_LEN=32768
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=7200
export SERVICE_TIMEOUT=1800
export REQUEST_TIMEOUT=600
export NO_PROXY=localhost,127.0.0.1
export no_proxy="$NO_PROXY"
export PYTEST_ADDOPTS='-p no:cacheprovider'
export PORT=${PORT:-8145}
unset VIRTUAL_ENV BASE_URL VLLM_FL_ILUVATAR_MROPE_IMPL
