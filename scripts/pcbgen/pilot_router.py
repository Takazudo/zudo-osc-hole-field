"""Guarded router-only step for a class-filtered full-board DSN pilot."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.route import read_env,router

def main():
    p=argparse.ArgumentParser();p.add_argument('dsn',type=Path);p.add_argument('ses',type=Path);p.add_argument('receipt',type=Path);p.add_argument('--timeout-sec',type=int,default=120);p.add_argument('--threads',type=int,default=4);p.add_argument('--no-fanout',action='store_true');a=p.parse_args()
    receipt=json.loads(a.receipt.read_text())
    if receipt['ignored_classes']!=['kicad_default','Ground','Rails']:raise ValueError('unexpected ignored classes')
    image,heap,_=read_env();a.ses.unlink(missing_ok=True)
    code,seconds,peak,log=router(a.dsn,a.ses,a.dsn.parent,a.threads,heap,a.timeout_sec,image,fanout=not a.no_fanout,ignored_classes=receipt['ignored_classes'])
    (a.dsn.parent/'pilot-router.log').write_text(log)
    report={'router_exit_code':code,'runtime_sec':round(seconds,3),'peak_memory_mb':round(peak,2),'ses_exists':a.ses.exists(),'fanout_enabled':not a.no_fanout,'skipped_keepout_warnings':log.count('was skipped because its geometry is degenerate'),'fanout_start_lines':[line for line in log.splitlines() if 'Fanout stage started' in line]}
    (a.dsn.parent/'pilot-router.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,sort_keys=True))
    return 0 if code==0 and a.ses.exists() and report['skipped_keepout_warnings']==0 else 2
if __name__=='__main__':raise SystemExit(main())
