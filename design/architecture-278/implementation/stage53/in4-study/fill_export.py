"""Read-only native In4 fill extraction; not refill or DRC."""
from pathlib import Path
import hashlib,json,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[5]
p=ROOT/'.circuit-cache/stage49-fresh/osc-jack-left.kicad_pcb'
sha=hashlib.sha256(p.read_bytes()).hexdigest()
if sha!='05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441' or pcbnew.GetBuildVersion()!='10.0.6':raise ValueError('baseline/oracle')
b=pcbnew.LoadBoard(str(p));zones=[z for z in b.Zones() if z.GetNetname()=='+12V' and z.IsOnLayer(pcbnew.In4_Cu)]
if len(zones)!=1:raise ValueError('zone count')
z=zones[0];ps=z.GetFilledPolysList(pcbnew.In4_Cu)
if ps.OutlineCount()!=1 or ps.HoleCount(0):raise ValueError('expected fractured outline')
p=ps.COutline(0)
r=dict(board_sha256=sha,version=pcbnew.GetBuildVersion(),zone_uuid=z.m_Uuid.AsString(),clearance_mm=pcbnew.ToMM(z.GetLocalClearance()),minimum_thickness_mm=pcbnew.ToMM(z.GetMinThickness()),points=[[p.CPoint(i).x/1e6,p.CPoint(i).y/1e6] for i in range(p.PointCount())])
Path(sys.argv[1]).write_text(json.dumps(r,sort_keys=True)+'\n')
