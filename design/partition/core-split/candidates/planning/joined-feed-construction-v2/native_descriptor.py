#!/usr/bin/env python3
"""Write the concrete native-validation descriptor for the E16 t2 candidate (no dispatch, no admission).

Binds the exact candidate/input hashes, the orchestration commit, the pinned KiCad 10.0.6
image and reviewed-hook digests, the phase/command list, preservation/full-warning/fresh-copy
checks and the resource/cleanup plan. The fields that only a parent admission of an actual
GitHub run can fill (run ID, admitted SHA, reviewed hook digest variable) stay null:
scripts/kicad/ci_native_admission.py refuses any run whose run ID/SHA do not match them.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--replay',type=Path,required=True,help='independent replay OUTDIR (t2)');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
 image=re.search(r"^KICAD_IMAGE='(kicad/kicad@sha256:[0-9a-f]{64})'$",(ROOT/'scripts/kicad/pin.env').read_text(),re.M).group(1)
 cand={b:{'t2_source_json':sha(a.replay/f'{b}-access-t2.json'),'t2_caps_json':sha(a.replay/f'{b}-eval-t2/normalized-caps.json'),'t2_clipped_sheets_json':sha(a.replay/f'{b}-eval-t2/clipped-sheets.json'),
          'retained_t2_port_graph_gz':sha(HERE/f'evidence/e16/{b}-t2-port-graph.json.gz'),'retained_t2_obligations':sha(HERE/f'evidence/e16/{b}-t2-port-obligations.json'),
          'retained_delta_r1_r3_gz':sha(HERE/f'evidence/e16/{b}-access-delta.json.gz'),'retained_delta_r4_t2_gz':sha(HERE/f'evidence/e16/{b}-access-delta-r4-t2.json.gz'),
          'candidate05_pcb':sha(a.replay/f'cand05/{b}.kicad_pcb')} for b in ('KA','KB')}
 d={'schema':'e16-native-validation-descriptor-v1','status':'PREPARED, NOT ADMITTED, NOT DISPATCHED','orchestration_commit':head,
    'candidate':{'epoch':'E16','round':'t2','boards':cand,'reconstruction':'bash replay_e16.sh PYTHON ABS_OUTDIR (replays candidate05 byte-for-byte, then r1..t2; compare_replay.py must exit 0 for both boards)'},
    'oracle':{'kicad_version':'10.0.6','image':image,'run_sh_sha256':sha(ROOT/'scripts/kicad/run.sh'),'pin_env_sha256':sha(ROOT/'scripts/kicad/pin.env'),
              'native_resource_guard_sha256':sha(ROOT/'scripts/kicad/native_resource_guard.py'),'ci_native_admission_sha256':sha(ROOT/'scripts/kicad/ci_native_admission.py')},
    'phases':[
     {'id':'N0-reconstruct','native':False,'command':'bash design/partition/core-split/candidates/planning/joined-feed-construction-v2/replay_e16.sh PYTHON ABS_OUTDIR','pass':'compare_replay.py --board KA and --board KB exit 0; candidate hashes above equal'},
     {'id':'N1-materialize','native':False,'command':'write the t2 access delta (segments and vias) into fresh copies of the candidate05 KA/KB .kicad_pcb, never into boards/**','pass':'fresh-copy hashes recorded; canonical boards/** and placements.lock.json byte-identical before/after',
      'status':'NOT IMPLEMENTED: no reviewed materializer exists yet; it is source work required before any admission request'},
     {'id':'N2-zone-fill','native':True,'command':'scripts/kicad/run.sh pcb ... zone fill on each fresh copy (KiCad 10.0.6, pinned image)','pass':'fill completes; filled zones exported'},
     {'id':'N3-drc','native':True,'command':'scripts/kicad/run.sh pcb drc --severity-all --format json on each filled copy','pass':'full warning and error list retained (no severity filter); every violation classified, none silently waived'},
     {'id':'N4-connectivity','native':True,'command':'native unconnected-item report for +12V/-12V/+5V/AGND on each filled copy','pass':'native open-edge census reconciled pad-by-pad against K?-t2-port-obligations.json; differences reported, not forced'}],
    'checks':{'preservation':'boards/**, design/grid/placements.lock.json and decision.json SHA-256 equal before and after','full_warnings':'DRC JSON retained unfiltered','fresh_copy':'every native phase works on a fresh copy made from the reconstructed candidate; inputs re-hashed after each phase'},
    'resources':{'workers':'at most two native workers globally, reserved by the parent admission','per_worker':'6 GiB no-swap systemd slice, 12 GiB aggregate, >=8 GiB MemAvailable at launch (native_resource_guard.py)',
                 'deadlines':'Python phase 28 min, board phase 43 min (ci_native_admission.py)','cleanup':'watchdog removes only containers with this worker label, verifies no survivors, then exits; worker identity single-use'},
    'binding_fields_unfilled':{'EPIC242_PARENT_ADMISSION_RUN_ID':None,'EPIC242_PARENT_ADMISSION_SHA':None,'EPIC242_REVIEWED_HOOK_SHA256':None,'github_run_attempt':1,
                               'note':'Only a parent admission of the actual GitHub run may fill these; old tokens/receipts are not reusable. This source continuation neither mints nor dispatches.'},
    'native_calls':0}
 a.output.write_text(json.dumps(d,indent=1)+'\n');print(json.dumps({'commit':head,'image':image}))
if __name__=='__main__':main()
