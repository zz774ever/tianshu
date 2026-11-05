import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import threading
import time

source = Path('/workspace/vllm-plugin-FL/tools/adaptation-gate-cases')
root = Path('/workspace/adaptation-gate-results') / ('current-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
root.mkdir(parents=True)
manifest = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'hostname': socket.gethostname(), 'root': str(root), 'versions': {}, 'hashes': {}, 'rounds': []}
for package in ['torch', 'torch-gcu', 'vllm', 'vllm-plugin-fl', 'flag-gems', 'flagtree', 'triton', 'pytest', 'openai', 'pillow']:
    try:
        manifest['versions'][package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        manifest['versions'][package] = None
for path in sorted(source.iterdir()):
    if path.suffix in ['.py', '.sh']:
        manifest['hashes'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
for path in sorted((source / 'images').glob('*.png')):
    manifest['hashes'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
manifest['plugin_commit'] = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
base = os.environ.copy()
base.update(TOPS_VISIBLE_DEVICES='5,6', VLLM_PLUGINS='fl', FLAGCX_PATH='/workspace/s60-adaptation/flagcx-runtime', TORCHINDUCTOR_EMULATE_PRECISION_CASTS='1', PYTHONPATH='/workspace/vllm-plugin-FL', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1', LD_LIBRARY_PATH='/usr/local/lib/openmpi:' + base.get('LD_LIBRARY_PATH', ''), TENSOR_PARALLEL_SIZE='2', MAX_MODEL_LEN='32768', PORT='18120', SERVICE_TIMEOUT='1800', REQUEST_TIMEOUT='600', NO_PROXY='localhost,127.0.0.1', no_proxy='localhost,127.0.0.1', PYTEST_ADDOPTS='-p no:cacheprovider', VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS='7200')
for name in ['BASE_URL', 'GPU_MEMORY_UTILIZATION', 'GRAPH_COMPILATION_CONFIG']:
    base.pop(name, None)
manifest['environment'] = {name: base[name] for name in ['TOPS_VISIBLE_DEVICES', 'VLLM_PLUGINS', 'FLAGCX_PATH', 'TORCHINDUCTOR_EMULATE_PRECISION_CASTS', 'PYTHONPATH', 'LD_LIBRARY_PATH', 'TENSOR_PARALLEL_SIZE', 'MAX_MODEL_LEN', 'PORT', 'SERVICE_TIMEOUT', 'REQUEST_TIMEOUT', 'PYTEST_ADDOPTS']}
def save():
    (root / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
save()
print('RESULTS_ROOT=' + str(root), flush=True)
for model, mode in [('27B', 'eager'), ('27B', 'graph'), ('35B-A3B', 'eager'), ('35B-A3B', 'graph')]:
    label = model.lower() + '-' + mode
    directory = root / label
    directory.mkdir()
    environment = base.copy()
    environment.update(MODEL_PATH='/models/Qwen3.6-' + model, SERVED_MODEL_NAME='qwen', RESULTS_DIR=str(directory), SERVER_PID_FILE=str(directory / 'server.pid'))
    entry = {'label': label, 'model': environment['MODEL_PATH'], 'mode': mode, 'results_dir': str(directory), 'serve_command': 'bash run_serve_' + mode + '.sh', 'test_command': 'bash run_test.sh', 'observations': [], 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    manifest['rounds'].append(entry)
    save()
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', 18120)) == 0:
            raise RuntimeError('Port 18120 already in use; no existing service will be stopped')
    server = subprocess.Popen(['bash', 'run_serve_' + mode + '.sh'], cwd=source, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    entry['server_pid'] = server.pid
    def observe():
        for line in server.stdout:
            if any(marker in line for marker in ['Capturing', 'capture', 'Application startup', 'ERROR', 'Error', 'non-default args', 'gpu_memory_utilization', 'cudagraph_mode']):
                print('[' + label + '] ' + line.rstrip(), flush=True)
                entry['observations'].append(line.rstrip())
    reader = threading.Thread(target=observe, daemon=True)
    reader.start()
    try:
        result = subprocess.run(['bash', 'run_test.sh'], cwd=source, env=environment)
        entry['test_exit_code'] = result.returncode
        entry['server_exit_before_cleanup'] = server.poll()
    finally:
        if server.poll() is None:
            os.killpg(server.pid, signal.SIGINT)
            try:
                server.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid, signal.SIGTERM)
                server.wait(timeout=30)
        reader.join(timeout=10)
        entry['server_exit_code'] = server.returncode
        entry['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entry['reports'] = [str(path.relative_to(root)) for path in sorted(directory.rglob('*.json'))]
        save()
        print('ROUND_FINISHED ' + json.dumps(entry, ensure_ascii=False), flush=True)
        time.sleep(10)
manifest['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
save()
print('ALL_ROUNDS_FINISHED ' + str(root), flush=True)
