"""Candidate checkpoint guard; never invokes native tools or aggregate regeneration."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
BASE='d218fc537818dcbbd470eb15d192cfc8d0be5f0a'
OWNED=('design/architecture-278/implementation/','scripts/architecture278/implementation/')

def validate_paths(paths):
    bad=[p for p in paths if not p.startswith(OWNED)]
    if bad:raise ValueError('outside isolated candidate scope: '+', '.join(bad))

def main():
    paths=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    paths+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    validate_paths(paths)
    subprocess.run([sys.executable,str(ROOT/'scripts/architecture278/check_packet.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(Path(__file__).with_name('candidate.py')),'--check'],cwd=ROOT,check=True)
    for generator in ('front_evidence.py','mechanical_feasibility.py','assembly.py','assembly_mechanical_review.py','placement_search.py'):
        subprocess.run([sys.executable,str(Path(__file__).with_name(generator)),'--check'],cwd=ROOT,check=True)
    print('PASS isolated candidate scope; PR285 and all canonical bytes unchanged; native NOT RUN')
if __name__=='__main__':main()
