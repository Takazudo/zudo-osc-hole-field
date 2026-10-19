"""Native B.Cu AGND contours, with unfracture area audit and fill-hit witnesses."""
from pathlib import Path
import hashlib,json,math,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from native_guard import check_native
from probe import BASE_HASH

def points(chain):return [[pcbnew.ToMM(chain.CPoint(i).x),pcbnew.ToMM(chain.CPoint(i).y)] for i in range(chain.PointCount())]
def extract(path,output):
 raw=path.read_text()
 if hashlib.sha256(raw.encode()).hexdigest()!=BASE_HASH:raise ValueError('baseline')
 b=pcbnew.LoadBoard(str(path));check_native(b,raw);c=b.GetConnectivity();c.RecalculateRatsnest();check_native(b,raw)
 z=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='AGND' and z.IsOnLayer(pcbnew.B_Cu))
 rawpoly=z.GetFilledPolysList(pcbnew.B_Cu);polys=rawpoly.CloneDropTriangulation();before=polys.Area()/1e12;polys.Unfracture();after=polys.Area()/1e12
 data=[{'shell':points(polys.COutline(i)),'holes':[points(polys.CHole(i,h)) for h in range(polys.HoleCount(i))]} for i in range(polys.OutlineCount())]
 perimeter=sum(math.dist(r[i],r[(i+1)%len(r)]) for p in data for r in [p['shell'],*p['holes']] for i in range(len(r)))
 tolerance=perimeter*2e-6+1e-6
 if abs(before-after)>tolerance:raise ValueError('unfracture area drift')
 witnesses=[]
 for ix in range(26800,27101,10):
  for iy in range(13250,13501,10):
   pos=pcbnew.VECTOR2I(ix*10000,iy*10000)
   witnesses.append({'xy':[ix/100,iy/100],'native_hit':bool(z.HitTestFilledArea(pcbnew.B_Cu,pos,0)),'raw_contains':bool(rawpoly.Contains(pos)),'unfractured_contains':bool(polys.Contains(pos))})
 pad=next(p for f in b.GetFootprints() if f.GetReference()=='R8270' for p in f.Pads() if p.GetNumber()=='2')
 conn=[{'kind':str(p.Type()),'uuid':p.m_Uuid.AsString(),'net':p.GetNetname()} for p in c.GetConnectedItems(pad)]
 output.write_text(json.dumps({'board_sha256':BASE_HASH,'zone_uuid':z.m_Uuid.AsString(),'native_open_edges':c.GetUnconnectedCount(False),'native_pad_connected_items':conn,'area_before_mm2':before,'area_after_mm2':after,'area_tolerance_mm2':tolerance,'polygons':data,'witnesses':witnesses},separators=(',',':'))+'\n')
 print(json.dumps({'opens':c.GetUnconnectedCount(False),'pad_neighbors':conn,'raw_vs_hit_mismatches':sum(v['raw_contains']!=v['native_hit'] for v in witnesses),'unfractured_vs_hit_mismatches':sum(v['unfractured_contains']!=v['native_hit'] for v in witnesses)}))
if __name__=='__main__':extract(Path(sys.argv[1]),Path(sys.argv[2]))
