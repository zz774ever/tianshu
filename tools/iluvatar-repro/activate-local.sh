if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo 'Use: source /workspace/tianshu-delivery/tools/iluvatar-repro/activate-local.sh' >&2
    exit 2
fi

export REPRO_ROOT="${REPRO_ROOT:-/workspace/tianshu-manual}"
export ENV_DIR="${ENV_DIR:-/workspace/validation/venv}"
export REPO_DIR="${REPO_DIR:-/workspace/pr674-plugin}"
export FLAGCX_PATH="${FLAGCX_PATH:-/mnt/share/user_homes/iluv/FlagCX}"
export COREX_DRIVER_LIB_DIR="${COREX_DRIVER_LIB_DIR:-/workspace/driver-extracted/corex/lib64}"
source "$(dirname -- "${BASH_SOURCE[0]}")/activate.sh"
