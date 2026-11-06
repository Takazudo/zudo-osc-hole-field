"""Read-only native ground-fill and exact local-object inspection."""
from pathlib import Path
import hashlib,json,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from native_guard import check_native
BASE_HASH='d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'

def probe(path,output):
 raw=path.read_text()
 if hashlib.sha256(raw.encode()).hexdigest()!=BASE_HASH:raise ValueError('baseline')
 b=pcbnew.LoadBoard(str(path));check_native(b,raw);conn=b.GetConnectivity();conn.RecalculateRatsnest();check_native(b,raw)
 zones=[]
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for layer in b.GetEnabledLayers().CuStack():
   if not z.IsOnLayer(layer):continue
   ps=z.GetFilledPolysList(layer)
   points=[]
   for ix in range(26300,27601,25):
    for iy in range(12500,13901,25):
     if ps.Contains(pcbnew.VECTOR2I(ix*10000,iy*10000)):points.append([ix/100,iy/100])
   zones.append({'uuid':z.m_Uuid.AsString(),'net':z.GetNetname(),'layer':b.GetLayerName(layer),'filled_polygon_count':ps.OutlineCount(),'sample_pitch_mm':.25,'filled_sample_points_native_mm':points})
 output.write_text(json.dumps({'board_sha256':BASE_HASH,'version':pcbnew.GetBuildVersion(),'native_open_edges':conn.GetUnconnectedCount(False),'zones':zones,'limits':'Exact native fill membership at sampled points only; not a via-clearance or connectivity acceptance test.'},indent=2)+'\n')
 print(json.dumps({'opens':conn.GetUnconnectedCount(False),'zones':[(z['net'],z['layer'],len(z['filled_sample_points_native_mm'])) for z in zones]}))
if __name__=='__main__':probe(Path(sys.argv[1]),Path(sys.argv[2]))
