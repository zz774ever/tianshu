import os
from pathlib import Path
import sys


def main():
    if sys.prefix == sys.base_prefix:
        raise SystemExit('Activate the isolated venv before preparing its CLI')
    import pytest

    target = Path(sys.prefix) / 'bin/pytest'
    content = (
        f'#!{sys.executable}\n'
        'from pytest import console_main\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    raise SystemExit(console_main())\n'
    )
    if not target.exists() or target.read_text() != content:
        target.write_text(content)
        target.chmod(target.stat().st_mode | 0o111)
    print(f'pytest module: {pytest.__file__}')
    print(f'pytest entry: {target}')
    print(f'interpreter: {sys.executable}')
    assert os.access(target, os.X_OK)


if __name__ == '__main__':
    main()
