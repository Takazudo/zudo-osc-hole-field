"""Run the supplemental Playwright review under the shared guard, bounded to 60s.
Usage: python3 review_scroll.py PLAYWRIGHT_MODULE CHROME_EXECUTABLE NEW_OUTPUT_DIR
"""
from pathlib import Path
import signal
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from check_browser import bounded_run


def interrupted(signum, frame):
    raise KeyboardInterrupt(signum)


signal.signal(signal.SIGTERM, interrupted)
command = ['node', str(Path(__file__).with_suffix('.mjs')), *sys.argv[1:]]
# The sibling logs persist even if Node times out before writing its receipt.
output = Path(sys.argv[3])
with output.with_suffix('.stdout.txt').open('w') as stdout, output.with_suffix('.stderr.txt').open('w') as stderr:
    status = bounded_run(command, stdout, stderr)
print(f'Playwright supplemental review exit_status={status}')
sys.exit(status)
