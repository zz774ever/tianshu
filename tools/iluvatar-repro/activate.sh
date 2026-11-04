if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo 'Use: source /repro/docs/tools/iluvatar-repro/activate.sh' >&2
    exit 2
fi

export REPRO_ROOT="${REPRO_ROOT:-/repro}"
export ENV_DIR="${ENV_DIR:-$REPRO_ROOT/venv}"
export REPO_DIR="${REPO_DIR:-$REPRO_ROOT/src/vllm-plugin-FL}"
export FLAGCX_PATH="${FLAGCX_PATH:-$REPRO_ROOT/src/FlagCX}"

if [[ ! -r "$ENV_DIR/bin/activate" || ! -f "$REPO_DIR/pyproject.toml" ]]; then
    echo 'Create the venv and clone vllm-plugin-FL using the setup guide first.' >&2
    return 2
fi

if [[ -n ${COREX_DRIVER_LIB_DIR:-} && ! -d "$COREX_DRIVER_LIB_DIR" ]]; then
    echo "Missing driver userspace directory: $COREX_DRIVER_LIB_DIR" >&2
    return 2
fi

unset PYTHONPATH VLLM_VENDOR VLLM_ENGINE_ITERATION_TIMEOUT_S VLLM_RPC_TIMEOUT
source "$ENV_DIR/bin/activate"
export PYTHONNOUSERSITE=1
export PYTHONPATH="$REPO_DIR"
export VLLM_PLUGINS=fl
export USE_FLAGGEMS=1
export GEMS_VENDOR=iluvatar
export COREX_VISIBLE_DEVICES="${REPRO_DEVICES:-0,1,2,3}"
export CUDA_VISIBLE_DEVICES="$COREX_VISIBLE_DEVICES"
export LD_LIBRARY_PATH="$FLAGCX_PATH/build/lib:/usr/local/corex/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [[ -n ${COREX_DRIVER_LIB_DIR:-} ]]; then
    export LD_LIBRARY_PATH="$COREX_DRIVER_LIB_DIR:$LD_LIBRARY_PATH"
fi
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600

printf 'Python: %s\nPlugin: %s\nFlagCX: %s\nDevices: %s\n' \
    "$(command -v python)" "$REPO_DIR" "$FLAGCX_PATH" "$CUDA_VISIBLE_DEVICES"
