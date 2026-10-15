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
    for generator in ('front_evidence.py','mechanical_feasibility.py','assembly.py','assembly_mechanical_review.py','placement_search.py','stage3_crossing_audit.py','stage3_reservations.py','cluster_refinement.py','direct_study.py','stage3_direct_mechanical.py','stage4_regions.py','stage4_requirements.py','stage4_power_inventory.py','stage4_candidate.py','stage4_occupied.py','stage4_mechanical.py','stage5_hosting_options.py','stage5_electrical.py','stage5_rebudget.py','stage5_dual_metrics.py','stage5_mechanical.py','stage6_rebudget.py','stage6_electrical.py','stage6_hosting.py','stage6_mechanical.py','stage7_mechanical.py','stage7_interfaces.py','stage7_electrical.py','stage7_demonstrator.py','stage8_mechanical.py','stage8_locality.py','stage8_rebudget.py','stage8_currents.py','stage8_assessment.py','stage8_visualize.py','stage9_process.py','stage9_support.py','stage9_electrical.py','stage9_comparison.py','stage10_inventory.py','stage10_mechanical.py','stage10_interfaces.py','stage10_assessment.py','stage10_visualize.py','stage11_identity.py','stage11_support.py','stage11_electrical.py','stage11_assessment.py'):
        subprocess.run([sys.executable,str(Path(__file__).with_name(generator)),'--check'],cwd=ROOT,check=True)
    print('PASS isolated candidate scope; PR285 and all canonical bytes unchanged; native NOT RUN')
if __name__=='__main__':main()
