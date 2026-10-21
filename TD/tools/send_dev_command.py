"""Send a local script to the opt-in development bridge and await its receipt."""
import argparse
import json
from pathlib import Path
import time


def send(source, timeout=15):
    root = Path(__file__).resolve().parents[1] / '.runtime'
    command = root / 'command.py'
    command.write_text(Path(source).read_text(encoding='utf-8-sig'), encoding='utf-8')
    stamp = command.stat().st_mtime_ns
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = json.loads((root / 'result.json').read_text(encoding='utf-8'))
            if result['stamp'] == stamp:
                print(result['output'])
                return 0 if result['ok'] else 1
        except (OSError, ValueError):
            pass
        time.sleep(0.2)
    raise TimeoutError('TD did not acknowledge this command; inspect the existing TD window before retrying')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    args = parser.parse_args()
    raise SystemExit(send(args.source))
