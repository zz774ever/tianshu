import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description='Record a command, output, timing and exit status')
    parser.add_argument('--root', required=True)
    parser.add_argument('label')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        parser.error('Pass a command after --')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', args.label):
        parser.error('Use letters, digits, dots, hyphens or underscores in the label')
    started = datetime.datetime.now(datetime.UTC)
    directory = Path(args.root).resolve() / (started.strftime('%Y%m%dT%H%M%S.%fZ-') + args.label)
    directory.mkdir(parents=True)
    script = shlex.join(command)
    (directory / 'command.sh').write_text(script + '\n')
    record = {'label': args.label, 'started_utc': started.isoformat(),
              'argv': command, 'cwd': os.getcwd(), 'status': 'RUNNING',
              'environment': {name: os.environ.get(name) for name in (
                  'VIRTUAL_ENV', 'PYTHONPATH', 'LD_LIBRARY_PATH', 'REPO_DIR', 'FLAGCX_PATH',
                  'COREX_DRIVER_LIB_DIR', 'CUDA_VISIBLE_DEVICES', 'COREX_VISIBLE_DEVICES',
                  'VLLM_PLUGINS', 'USE_FLAGGEMS', 'GEMS_VENDOR')}}
    metadata_file = directory / 'metadata.json'
    metadata_file.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(f'RECORD={directory}\n{script}', flush=True)
    clock = time.monotonic()
    status = 1
    try:
        with (directory / 'output.log').open('wb') as output:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            try:
                for line in process.stdout:
                    output.write(line)
                    output.flush()
                    sys.stdout.buffer.write(line)
                    sys.stdout.buffer.flush()
                status = process.wait()
            except KeyboardInterrupt:
                process.wait()
                status = 130
    except OSError as error:
        status = 127
        with (directory / 'output.log').open('ab') as output:
            output.write((str(error) + '\n').encode())
        print(str(error), file=sys.stderr)
    finally:
        record.update(status='FINISHED', exit_code=status,
                      finished_utc=datetime.datetime.now(datetime.UTC).isoformat(),
                      elapsed_seconds=time.monotonic() - clock)
        metadata_file.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(f'EXIT_CODE={status} RECORD={directory}', flush=True)
    return status if status >= 0 else 128 - status


if __name__ == '__main__':
    raise SystemExit(main())
