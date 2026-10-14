#!/usr/bin/env python3
"""Pack the 2026-10-13 continuation evidence index: files, hashes, commands, environment, resources.

Reads only retained evidence and the given run directories' step ledgers; writes
evidence/e16/continuation-20261013/index.json. The 2026-10-12/13 index.json stays as written.
"""
import argparse,glob,hashlib,json,platform,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;EV=HERE/'evidence/e16'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def steps(run):
 out=[]
 for f in sorted(glob.glob(str(Path(run)/'steps'/'*.json'))):
  d=json.loads(Path(f).read_text());out.append({'step':d['step'],'exit_code':d['exit_code'],'elapsed_seconds':d['elapsed_seconds'],'peak_rss_KiB':d['peak_rss_KiB']})
 return {'steps':len(out),'all_exit_zero':all(x['exit_code']==0 for x in out),'max_elapsed_seconds':max((x['elapsed_seconds'] for x in out),default=None),
         'max_peak_rss_GiB':round(max((x['peak_rss_KiB'] for x in out),default=0)/1024**2,3),'slowest':sorted(out,key=lambda x:-x['elapsed_seconds'])[:3]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--replay',type=Path,required=True);p.add_argument('--finite',type=Path,required=True);p.add_argument('--coupled',type=Path,required=True)
 p.add_argument('--refine',type=Path,required=True);p.add_argument('--pilot',type=Path,required=True,help='P1 run prefix (…-pilot-KB-p1)');p.add_argument('--source-sensitivity',type=Path,required=True);p.add_argument('--python',required=True);p.add_argument('--output',type=Path,default=EV/'continuation-20261013/index.json');a=p.parse_args()
 env=json.loads(subprocess.run([a.python,'-c','import sys,json,numpy,scipy,shapely;print(json.dumps({"python":sys.version.split()[0],"numpy":numpy.__version__,"scipy":scipy.__version__,"shapely":shapely.__version__,"geos":".".join(map(str,shapely.geos_version))}))'],capture_output=True,text=True,check=True).stdout)
 files=sorted(str(q.relative_to(HERE)) for q in EV.rglob('*') if q.is_file() and 'continuation-20261013' not in q.parts and q.stat().st_mtime>Path(EV/'index.json').stat().st_mtime)
 methods=['compare_replay.py','selective_annulus.py','fragments.py','finite_adapter.py','finite_units.py','finite_solve.py','run_finite_e16.py','run_coupled_e16.py','summarize_coverage.py','summarize_coupled.py',
          'diagnose_omissions.py','residual_atlas.py','pilot_preflight.py','pilot_construct.py','load_ledger.py','native_descriptor.py','package_continuation.py','verify_kcl.py','compare_refinement.py','summarize_depth.py']
 d={'schema':'e16-continuation-index-v1','date':'2026-10-13','environment':dict(env,platform=platform.platform(),requirements='scripts/pcbgen/numerical-requirements.txt',
    venv='uv venv --python /usr/bin/python3.12 VENV; uv pip install -r scripts/pcbgen/numerical-requirements.txt'),
    'commands':{'replay':'bash replay_e16.sh PYTHON ABS_OUTDIR  (under bash $HOME/.claude/scripts/heavy-guard.sh --)',
                'compare':'python3 compare_replay.py --run ABS_OUTDIR --board KA|KB --output evidence/e16/replay/20261013-t2-independent/K?-replay-comparison.json',
                'finite':'python run_finite_e16.py --python PYTHON --run REPLAY_OUTDIR --output ABS_FINITE_OUTDIR [--resume]',
                'coverage':'python summarize_coverage.py --finite ABS_FINITE_OUTDIR --ledger evidence/e16/load-ledger-20261013.json.gz --output evidence/e16/finite-coverage-t2.json',
                'coupled':'python run_coupled_e16.py --python PYTHON --finite ABS_FINITE_OUTDIR --output ABS_COUPLED_OUTDIR [--case ...] [--depth ...] [--resume]',
                'matrix':'python summarize_coupled.py --coupled ABS_COUPLED_OUTDIR --finite ABS_FINITE_OUTDIR --output evidence/e16/coupled-matrix-t2.json',
                'ledger':'python3 load_ledger.py --output DIR [--check]',
                'atlas':'python residual_atlas.py --board K? --source REPLAY/K?-eval-t2/normalized-caps.json --planes-dir ABS_FINITE_OUTDIR/K? --graph ... --census ... --ledger ... --output evidence/e16/K?-t2-residual-atlas.json.gz',
                'diagnosis':'python diagnose_omissions.py --board K? --net=NET --source REPLAY/K?-access-t2.json --planes ABS_FINITE_OUTDIR/K?/planes-NET.json.gz --graph ... --census ... --retained evidence/e16/finite-network-t2-ports.json.gz --output evidence/e16/omissions/K?-NET.json',
                'kcl_audit':'python verify_kcl.py --coupled ABS_COUPLED_OUTDIR --finite ABS_FINITE_OUTDIR --output evidence/e16/node-kcl-audit-t2.json',
                'depth_summary':'python summarize_depth.py --coupled ABS_COUPLED_OUTDIR --output evidence/e16/coupled-depth-sensitivity-t2.json  (after run_coupled_e16.py --resume --case nominal-average --depth staged-caps-bands --depth barrel-upper-1p6-per-interval)',
                'mesh_sensitivity':'python run_finite_e16.py ... --board KA --net=+5V and --board KB --net=-12V with --pitch 0.5 --face-pitch 0.125 (refined) or --origin 0.37 0.21 (shifted); python finite_solve.py dpoint ... --start 0 --stop 1000000 for baseline and variants; python compare_refinement.py --baseline DP --variant refined=DP --variant shifted-origin=DP --output evidence/e16/mesh-sensitivity-K?-NET.json',
                'source_sensitivity':'python run_coupled_e16.py --python PYTHON --finite ABS_FINITE_OUTDIR --output ABS_OUTDIR --config evidence/e16/coupled-network-config-single-land.json --case nominal-average; python summarize_coupled.py --coupled ABS_OUTDIR --finite ABS_FINITE_OUTDIR --config evidence/e16/coupled-network-config-single-land.json --output evidence/e16/coupled-source-sensitivity-t2.json',
                'pilot_construct':'python pilot_construct.py --preflight evidence/e16/pilot/KB-preflight-c-same-net-drills-exempt.json --seal evidence/e16/pilot/KB-seal.json --source REPLAY/KB-access-t2.json --graph REPLAY/KB-eval-t2/port-graph.json --census REPLAY/KB-eval-t2/port-obligations.json --python PYTHON --output ABS_P1  (then run_finite_e16.py --run P1RUN --round p1 --board KB --net=+5V and run_coupled_e16.py --net=+5V --case nominal-average with KA linked from the t2 finite run)',
                'preflight':'python pilot_preflight.py --source ... --planes ... --graph ... --census ... --pad-id UUID [--window-margin-mm M --max-length-mm L] --output evidence/e16/pilot/K?-preflight-*.json'},
    'resources':{'replay':steps(a.replay),'finite':steps(a.finite),'coupled':steps(a.coupled),'source_sensitivity':steps(a.source_sensitivity),
                 'pilot_p1_finite':steps(Path(str(a.pilot)+'-finite')),'pilot_p1_coupled':steps(Path(str(a.pilot)+'-coupled')),
                 'mesh_refined':steps(a.refine/'refined'),'mesh_shifted':steps(a.refine/'shifted'),
                 'bounds':'every unit: one process under timeout 180 s, serialized behind the host heavy-run guard. Replay, finite-coverage and mesh units: RLIMIT_AS 2 GiB. Coupled solver units (finite_solve.py): a kernel cgroup scope MemoryMax=2 GiB, MemorySwapMax=0, verified inside the unit (SuperLU address-space reservations made RLIMIT_AS reject 1.2 GiB-resident factorisations). Peak RSS per step is in each run\'s steps/ ledgers.'},
    'run_directories':{'replay':str(a.replay),'finite':str(a.finite),'coupled':str(a.coupled),'mesh_sensitivity':str(a.refine),'pilot_p1':str(a.pilot),'source_sensitivity':str(a.source_sensitivity),
                       'note':'Run directories are local caches outside the repository. The retained results bind the run outputs they read by SHA-256 (bindings in coupled-matrix, coupled-source-sensitivity, depth, KCL-audit, mesh-sensitivity and coverage files) and are reproducible with the commands above from tracked sources (candidate05 replays byte-for-byte); the cached intermediates themselves are not retained.'},
    'negative_outcomes':['KA pilot: no legal additive corridor within the sealed limits; no construction (pilot/KA-pilot-outcome.json). The first preflights of both boards wrongly applied hole clearance to same-net drills (independent review); corrected and re-run under the same limits.',
                         'KB pilot: credited (6 pads, 0 newly disconnected), but its new pads see 28.8-31.3 mOhm of copper (pilot/KB-p1/electrical-rerun.json).',
                         'Copper requirements (1 mOhm rail, 0.5 mOhm common AGND) fail at every evaluated pad but one; the KA trunk alone exceeds them on every net, case and stack (coupled-matrix-t2.json, coupled-depth-sensitivity-t2.json).',
                         'Node-level KCL tolerance 1e-9 NOT MET (1.7e-9 to 5.2e-8 at the double-precision evaluation floor; node-kcl-audit-t2.json).',
                         'Supported load on structurally unresolved pads cannot be served (nominal +12V 90.8 mA, -12V 101.0 mA).',
                         'Most fitted-IC supply current is unmapped; full-scope budget acceptance is false (load-ledger-20261013.json.gz).'],
    'superseded_runs':{'finite (pre-review: tangent contacts conducted, held lands spilled)':'20261013-finite-t2','coupled (RLIMIT_AS rejected SuperLU at 1.2 GiB resident)':'20261013-coupled-t2-failed-rlimit / -failed-memory',
                       'coupled (unrefined solves)':'20261013-coupled-t2-superseded-unrefined','note':'local cache directories next to the run directories; kept, not used for any reported result'},
    'resume_state':'All runs completed. Every driver accepts --resume and reuses only steps whose input, method and output hashes still match; stale or partial outputs move to rejected/.',
    'methods_sha256':{m:sha(HERE/m) for m in methods if (HERE/m).exists()},
    'files_sha256':{f:sha(HERE/f) for f in files},'native_calls':0,'accepted':False}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=1)+'\n');print(json.dumps({'files':len(files),'methods':len(d['methods_sha256'])}))
if __name__=='__main__':main()
