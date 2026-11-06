"""Disposable native refill diagnostics; not DRC/acceptance or physical qualification."""
from pathlib import Path
import hashlib,json,shutil,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_apply import apply
BASE='05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441'
NET='XED7C19D453619667580D'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(proposal,folder):
 base=ROOT/'.circuit-cache/stage49-fresh';board=base/'osc-jack-left.kicad_pcb'
 if sha(board)!=BASE or pcbnew.GetBuildVersion()!='10.0.6':raise ValueError('baseline/oracle')
 if folder.exists():raise ValueError('refuse overwrite diagnostic')
 folder.mkdir()
 for p in base.iterdir():
  if p.name in ['sheets','fp-lib-table','sym-lib-table'] or p.suffix in ['.kicad_pro','.kicad_sch','.kicad_dru']:
   if p.is_dir():shutil.copytree(p,folder/p.name)
   else:shutil.copy2(p,folder/p.name)
 q=json.loads(proposal.read_text())
 if q['removed_uuids'] or any(r['net']!=NET for r in q['copper']):raise ValueError('target-only additions')
 out=folder/board.name;apply(board,q,out)
 b=pcbnew.LoadBoard(str(out));b.BuildConnectivity()
 if not pcbnew.ZONE_FILLER(b).Fill(b.Zones()):raise ValueError('refill')
 c=b.GetConnectivity();c.Build(b);c.RecalculateRatsnest()
 groups={}
 for net in ['-12V',NET]:
  items=[t for t in b.GetTracks() if t.GetNetname()==net]+[p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()==net]
  seen=set();rows=[]
  for t in items:
   if int(t.this) in seen:continue
   members=[t]+[v for v in c.GetConnectedItems(t) if v.Type()!=pcbnew.PCB_ZONE_T and int(v.this)!=int(t.this)]
   ids={int(v.this) for v in members}
   if seen&ids:raise ValueError('overlapping diagnostic groups')
   seen|=ids
   pads=sorted(v.GetParentFootprint().GetReference()+':'+v.GetNumber() for v in members if v.Type()==pcbnew.PCB_PAD_T)
   rows.append({'size':len(ids),'pads':pads})
  if len(seen)!=len(items):raise ValueError('diagnostic inventory')
  groups[net]=sorted(rows,key=lambda r:(r['size'],r['pads']))
 opens=c.GetUnconnectedCount(False);pcbnew.SaveBoard(str(out),b)
 result={'baseline_sha256':BASE,'proposal_sha256':sha(proposal),'board_sha256':sha(out),'version':pcbnew.GetBuildVersion(),'opens':opens,'groups':groups,'drc':'NOT RUN; refill diagnostic only'}
 (folder/'probe.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
