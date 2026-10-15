"""Fail closed on protected-path changes and stale design-only outputs."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
BASE='65cefd41fc39e064d38319115ad96016a1c6b71c'
ALLOWED=('design/architecture-278/','scripts/architecture278/')
PAGES=('doc/src/content/docs/architecture/osc-modular-design-gate.mdx','doc/src/content/docs/project/next-actions.mdx')

def validate_paths(paths):
    bad=[p for p in paths if not (p.startswith(ALLOWED) or p in PAGES)]
    if bad:raise ValueError('protected/out-of-scope changes: '+', '.join(bad))

def main():
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    validate_paths(changed+untracked)
    for script in ('ledger.py','extract.py','mechanics.py','electrical.py'):
        subprocess.run([sys.executable,str(ROOT/'scripts/architecture278'/script),'--check'],cwd=ROOT,check=True)
    print('PASS: owned-output reproduction and protected-path guard; native/physical qualification NOT RUN')
if __name__=='__main__':main()
