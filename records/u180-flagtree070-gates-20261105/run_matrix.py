import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from importlib import metadata
from pathlib import Path


ROOT = Path("/workspace/adaptation-gate-upgrade-20261105")
CASES = Path("/workspace/vllm-plugin-FL/tools/adaptation-gate-cases")
MODELS = ["Qwen3.6-27B", "Qwen3.6-35B-A3B"]
SERVER_PATTERNS = (
    "Application startup complete", "Loading weights took", "init engine",
    "Capturing CUDA graphs", "Graph capturing finished", "ERROR",
    "Traceback", "GPU KV cache size", "Maximum concurrency",
)
active_processes = []
output_lock = threading.Lock()


def emit(*values):
    with output_lock:
        print(*values, flush=True)


def forward_output(process, label, server):
    for line in process.stdout:
        if not server or any(pattern in line for pattern in SERVER_PATTERNS):
            emit(f"[{label}]", line.rstrip())


def stop_process(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)


def stop_all(signum=None, frame=None):
    for process in reversed(active_processes):
        stop_process(process)
    if signum is not None:
        raise SystemExit(128 + signum)


def launch(command, environment, label, server=False):
    process = subprocess.Popen(
        command, cwd=CASES, env=environment, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True,
    )
    active_processes.append(process)
    threading.Thread(
        target=forward_output, args=(process, label, server), daemon=True
    ).start()
    return process


signal.signal(signal.SIGTERM, stop_all)
signal.signal(signal.SIGINT, stop_all)
assert metadata.version("flagtree") == "0.7.0+iluvatar3.6"
environment = os.environ.copy()
environment.update({
    "CUDA_VISIBLE_DEVICES": "0,1,2,3", "VLLM_PLUGINS": "fl",
    "USE_FLAGGEMS": "1", "GEMS_VENDOR": "iluvatar",
    "FLAGCX_PATH": "/mnt/share/user_homes/iluv/FlagCX",
    "LD_LIBRARY_PATH": "/workspace/driver-extracted/corex/lib64:"
        "/mnt/share/user_homes/iluv/FlagCX/build/lib:/usr/local/corex/lib64:"
        "/usr/local/openmpi/lib:/usr/local/lib",
    "PYTHONPATH": "/workspace/vllm-plugin-FL",
    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1",
    "TENSOR_PARALLEL_SIZE": "4", "MAX_MODEL_LEN": "32768",
    "GPU_MEMORY_UTILIZATION": "0.70", "SERVED_MODEL_NAME": "qwen",
    "PORT": "8132", "SERVICE_TIMEOUT": "1800", "REQUEST_TIMEOUT": "600",
    "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS": "7200",
    "GRAPH_COMPILATION_CONFIG": '{"mode":0,"cudagraph_mode":"FULL_DECODE_ONLY"}',
    "NO_PROXY": "localhost,127.0.0.1", "no_proxy": "localhost,127.0.0.1",
    "PYTEST_ADDOPTS": "-p no:cacheprovider",
})
for name in [
    "BASE_URL", "VLLM_FL_GRAPH_DIAGNOSTICS", "VLLM_SERVER_DEV_MODE",
    "VLLM_ENGINE_ITERATION_TIMEOUT_S", "VLLM_RPC_TIMEOUT", "TORCH_SHOW_CPP_STACKTRACES",
    "CUDA_LAUNCH_BLOCKING",
]:
    environment.pop(name, None)
connection = socket.socket()
connection.settimeout(1)
assert connection.connect_ex(("127.0.0.1", 8132)) != 0, "Port 8132 is occupied"
connection.close()
matrix = []
try:
    for model in MODELS:
        for mode in ["eager", "graph"]:
            label = f"{model}-{mode}"
            result_root = ROOT / "results" / label
            result_root.mkdir(parents=True, exist_ok=False)
            round_environment = environment | {
                "MODEL_PATH": f"/mnt/share/user_homes/models/{model}",
                "RESULTS_DIR": str(result_root),
                "SERVER_PID_FILE": str(result_root / "server.pid"),
            }
            started_at = datetime.now().isoformat()
            started = time.monotonic()
            emit("ROUND_START", label, started_at)
            server = launch(
                ["bash", f"run_serve_{mode}.sh"], round_environment,
                label + "-SERVER", server=True,
            )
            client = launch(
                ["bash", "run_test.sh"], round_environment, label + "-TEST"
            )
            next_heartbeat = started + 30
            timed_out = False
            while client.poll() is None:
                now = time.monotonic()
                if now - started > 3600:
                    timed_out = True
                    stop_process(client)
                    break
                if now >= next_heartbeat:
                    emit("HEARTBEAT", label, "elapsed_seconds", int(now - started),
                         "server_exit", server.poll())
                    next_heartbeat = now + 30
                time.sleep(1)
            reports = []
            for path in sorted(result_root.glob("*/port-*/*.json")):
                document = json.loads(path.read_text())
                summary = {
                    "scenario": document["case"]["scenario"],
                    "path": str(path.relative_to(ROOT)), **document["summary"],
                }
                reports.append(summary)
                emit("CASE_RESULT", label, json.dumps(summary))
                for output in document["output"]:
                    if not output["passed"]:
                        emit("FAILED_RESPONSE", label, output["request_id"],
                             json.dumps({"text": output["text"],
                                 "error": output.get("error"),
                                 "failed_checks": [key for key, value in
                                     output.get("checks", {}).items() if not value]}))
            entry = {
                "model": model, "mode": mode, "started_at": started_at,
                "finished_at": datetime.now().isoformat(),
                "client_exit": client.returncode, "timed_out": timed_out,
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "reports": reports,
                "passed": client.returncode == 0 and len(reports) == 5
                    and all(report["passed"] for report in reports),
            }
            matrix.append(entry)
            (ROOT / "matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
            emit("ROUND_RESULT", json.dumps(entry))
            stop_process(server)
            time.sleep(5)
finally:
    stop_all()
emit("MATRIX_COMPLETE", json.dumps(matrix))
sys.exit(0 if len(matrix) == 4 and all(entry["passed"] for entry in matrix) else 1)
