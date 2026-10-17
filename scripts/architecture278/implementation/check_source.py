"""Current source checkpoint: immutable historical reproduction plus scoped owner update."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
OWNED=('design/architecture-278/implementation/','scripts/architecture278/implementation/')


def validate_paths(paths):
    bad=[p for p in paths if not p.startswith(OWNED)]
    if bad:raise ValueError('outside isolated candidate scope: '+', '.join(bad))


def main():
    # Stage33 verifies every previous byte except reviewed entrypoints against 9a3b9116.
    # Historical strict hash guards execute at that immutable commit, not against rewritten reports.
    subprocess.run([sys.executable,str(Path(__file__).with_name('stage33_large_radius.py')),
                    '--check','--check-history','--check-review'],cwd=ROOT,check=True)
    print('PASS isolated candidate current acceptance scope; canonical bytes unchanged; native NOT RUN')


if __name__=='__main__':main()
