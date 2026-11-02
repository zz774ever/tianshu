"""Terminate only verified obsolete diagnostic process trees."""
import psutil
import signal

for pid, expected in ((433024, 'prefix_precision.py'), (435940, 'decode_precision.py')):
    try:
        p = psutil.Process(pid)
        cmd = ' '.join(p.cmdline())
        if expected not in cmd or '/workspace/s60-adaptation/' not in cmd:
            raise RuntimeError(f'PID {pid} is not expected diagnostic: {cmd}')
        children = p.children(recursive=True)
        for child in reversed(children):
            try:
                child.send_signal(signal.SIGTERM)
                print('TERM', child.pid)
            except psutil.NoSuchProcess:
                pass
        p.terminate()
        _, alive = psutil.wait_procs([p] + children, timeout=3)
        for child in alive:
            child.kill()
            print('KILL', child.pid)
    except psutil.NoSuchProcess:
        print('Already exited', pid)
