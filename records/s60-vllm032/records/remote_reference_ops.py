"""Authorized NVIDIA host operations; credential supplied only via environment."""
import argparse
import os
import sys
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
import paramiko

p = argparse.ArgumentParser()
p.add_argument('command', nargs='?')
p.add_argument('--put', nargs=2)
p.add_argument('--get', nargs=2)
a = p.parse_args()
c = paramiko.SSHClient()
c.load_system_host_keys()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('connect.westx.seetacloud.com', port=49162, username='root',
          password=os.environ['SSH_REFERENCE_PASSWORD'], timeout=25,
          auth_timeout=25, banner_timeout=25, look_for_keys=False, allow_agent=False)
try:
    if a.put or a.get:
        s = c.open_sftp()
        if a.put:
            s.put(*a.put)
        else:
            s.get(*a.get)
        s.close()
    else:
        _, out, err = c.exec_command(a.command, timeout=900)
        import threading
        def relay(stream, destination):
            for line in iter(stream.readline, ''):
                destination.write(line)
                destination.flush()
        threads = [threading.Thread(target=relay, args=(out, sys.stdout)),
                   threading.Thread(target=relay, args=(err, sys.stderr))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        raise SystemExit(out.channel.recv_exit_status())
finally:
    c.close()
