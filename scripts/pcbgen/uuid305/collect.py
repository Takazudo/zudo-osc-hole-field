"""Read-only pinned native collector. Run only after explicit guard admission."""
import argparse,collections,hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from adapter import mapping,bind_native,fingerprint,serialized_capture
from policy import check_policy
from scripts.pcbgen.copper_identity import load_board_text

def collect(original,proposal,manifest_path,observed,phase,native_view):
 import pcbnew
 policy=check_policy(Path.cwd())
 if not Path('/.dockerenv').is_file() or Path.cwd()!=Path('/work'):raise ValueError('reviewed wrapper Docker context required')
 if pcbnew.GetBuildVersion()!=policy['pcbnew_version']:raise ValueError('native pcbnew build mismatch')
 version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
 if version!='10.0.6':raise ValueError('pinned10.0.6 required')
 paths=[original,proposal,manifest_path,observed]+[observed.with_suffix(s) for s in ('.kicad_pro','.kicad_dru')]
 raw={p:p.read_bytes() for p in paths};sha=lambda x:hashlib.sha256(x).hexdigest()
 manifest=json.loads(raw[manifest_path]);maps=mapping(load_board_text(original),load_board_text(proposal),manifest)
 expected=maps[0 if phase.startswith('before') else 1]
 board=pcbnew.LoadBoard(str(observed));tracks=list(board.GetTracks());rows=[]
 def native_signature(t):
  layers=sorted(board.GetLayerName(l) for l in t.GetLayerSet().Seq())
  if t.Type()==pcbnew.PCB_VIA_T:
   kind='via';shape=[[t.GetPosition().x,t.GetPosition().y],t.GetWidth(pcbnew.F_Cu),t.GetDrillValue()]
   # Source via layer pair denotes span endpoints; native layer set expands span.
   layers=[board.GetLayerName(t.TopLayer()),board.GetLayerName(t.BottomLayer())];layers.sort()
  elif t.Type()==pcbnew.PCB_TRACE_T:kind='segment';shape=[[t.GetStart().x,t.GetStart().y],[t.GetEnd().x,t.GetEnd().y],t.GetWidth()]
  else:raise ValueError('unsupported native copper kind')
  return [t.m_Uuid.AsString(),kind,t.GetNetname(),layers,shape]
 for t in tracks:rows.append({'signature':native_signature(t)})
 bound=bind_native(rows,expected)
 def token(t):
  if t.Type()==pcbnew.PCB_PAD_T:return 'pad:'+t.m_Uuid.AsString()
  return expected[fingerprint(native_signature(t))]
 pads=[];seeds=tracks[:]
 for fp in board.GetFootprints():
  for p in fp.Pads():
   seeds.append(p);pads.append([token(p),fp.GetReference(),p.GetNumber(),p.GetNetname(),p.GetPosition().x,p.GetPosition().y,p.GetSize().x,p.GetSize().y,p.GetDrillSize().x,p.GetDrillSize().y,list(p.GetLayerSet().Seq()),p.GetOrientationDegrees()])
 if len({r[0] for r in pads})!=len(pads):raise ValueError('duplicate pad UUID unsupported')
 conn=board.GetConnectivity();conn.RecalculateRatsnest();members={}
 for item in seeds:
  if item.GetNetCode()<=0:continue
  group=sorted({token(item),*(token(x) for x in conn.GetConnectedItems(item) if x.Type()!=pcbnew.PCB_ZONE_T)})
  members[token(item)]=(item.GetNetname(),group)
 # Every member must independently report the same group: catches UUID-based native dedup inconsistencies.
 for key,(net,group) in members.items():
  for member in group:
   if members.get(member)!=(net,group):raise ValueError('native connectivity membership inconsistent')
 groups=sorted({(net,tuple(g)) for net,g in members.values()});by_net=collections.Counter(net for net,g in groups)
 opened=sum(v-1 for v in by_net.values())
 if opened!=conn.GetUnconnectedCount(False):raise ValueError('occurrence groups disagree with native ratsnest')
 zones=[]
 for z in board.Zones():
  for layer in z.GetLayerSet().Seq():
   poly=z.GetFilledPolysList(layer)
   if poly.ArcCount():raise ValueError('zone arc signature unsupported')
   zones.append([z.m_Uuid.AsString(),z.GetNetname(),layer,sha(poly.Format().encode())])
 if native_view.exists() or native_view.resolve() in {p.resolve() for p in paths}:raise ValueError('fresh distinct native view required')
 pcbnew.SaveBoard(str(native_view),board)
 serial=serialized_capture(load_board_text(native_view),expected)
 if any(p.read_bytes()!=b for p,b in raw.items()):raise ValueError('source changed during read-only collection')
 return dict(**serial,native_view_sha256=sha(native_view.read_bytes()),phase=phase,native_version=version,pcbnew_version=pcbnew.GetBuildVersion(),oracle_image=policy['image'],input_sha256={str(p):sha(raw[p]) for p in (original,proposal,manifest_path)},observed_sha256=sha(raw[observed]),mapping_sha256=sha(raw[manifest_path]),producer_sha256={p.name:sha(p.read_bytes()) for p in (Path(__file__),Path(__file__).with_name('adapter.py'))},context_sha256={s:sha(raw[observed.with_suffix(s)]) for s in ('.kicad_pro','.kicad_dru')},copper_tokens=sorted(bound),pads=sorted(pads),zones=sorted(zones),islands=groups,open_edges=opened,warning_complete=False,adopted=False)
if __name__=='__main__':
 import collections
 p=argparse.ArgumentParser()
 for n in ('original','proposal','manifest','observed','output'):p.add_argument(n,type=Path)
 p.add_argument('--phase',choices=['before','after','before_fresh','after_fresh'],required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('fresh output required')
 a.output.write_text(json.dumps(collect(a.original,a.proposal,a.manifest,a.observed,a.phase,a.output.with_suffix('.native-view.kicad_pcb')),indent=2)+'\n')
