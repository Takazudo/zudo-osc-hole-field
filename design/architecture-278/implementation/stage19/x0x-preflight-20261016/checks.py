import subprocess,json,time
from pathlib import Path
base=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3'); repo=base/'osc-stage19-verifier'; out=base/'osc-stage19-preflight'
commands=[['python3','-B','-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage19*.py'],['python3','-B','-O','-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage19*.py'],['python3','-B','-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage18*.py'],['python3','-B','scripts/architecture278/implementation/stage18_compat.py','--check']]
rows=[]
for i,argv in enumerate(commands):
 start=time.monotonic(); r=subprocess.run(argv,cwd=repo,capture_output=True,text=True,timeout=240)
 (out/f'check-{i}.stdout').write_text(r.stdout); (out/f'check-{i}.stderr').write_text(r.stderr)
 row={'argv':argv,'exit':r.returncode,'elapsed_seconds':time.monotonic()-start}; rows.append(row); print(json.dumps(row),flush=True)
(out/'checks.json').write_text(json.dumps({'checks':rows,'native_executed':False,'circuit_check':'NOT RUN: pnpm absent from existing WSL shell; no install','aggregate_regeneration':'NOT RUN: would invoke out-of-scope native operations'},indent=2)+'\n')
raise SystemExit(any(x['exit']!=0 for x in rows))
