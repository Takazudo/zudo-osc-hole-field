"""Native diagnostic of all eighteen translated power/return paths, not acceptance."""
from pathlib import Path
import json,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from native_guard import check_native
from identity_guard import digest

def diagnose(directory):
    path=directory/'osc-jack-left.kicad_pcb';raw=path.read_text()
    b=pcbnew.LoadBoard(str(path));check_native(b,raw)
    conn=b.GetConnectivity();conn.RecalculateRatsnest();check_native(b,raw)
    mapping=json.loads((directory/'receipt.json').read_text())['mapping']
    routes=json.loads((ROOT/'design/architecture-278/implementation/stage42/full-b1/evidence/power-paths.json').read_text())['paths']
    pads={f.GetReference()+':'+p.GetNumber():p for f in b.GetFootprints() for p in f.Pads()}
    def padkey(k):
        r,p=k.split(':');return mapping[r]+':'+p
    rows=[]
    for route in routes:
        start=pads[padkey(route['from_pad'])]
        connected={int(x.this) for x in conn.GetConnectedItems(start)}|{int(start.this)}
        r={'role':route['role'],'from_pad':padkey(route['from_pad']),'net':route['net']}
        if 'via_mm' in route:
            xy=[round((route['via_mm'][0]+34)*1000000),round(route['via_mm'][1]*1000000)]
            vias=[t for t in b.GetTracks() if t.Type()==pcbnew.PCB_VIA_T and [t.GetPosition().x,t.GetPosition().y]==xy and t.GetNetname()==route['net']]
            r.update(at_nm=xy,plane=route['plane'],matching_vias=len(vias))
            if len(vias)==1:
                via=vias[0];layer=b.GetLayerID(route['plane'])
                zones={z.m_Uuid.AsString() for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()==route['net'] and z.IsOnLayer(layer) and z.GetFilledPolysList(layer).Contains(via.GetPosition())}
                native={x.m_Uuid.AsString() for x in conn.GetConnectedItems(via) if x.Type()==pcbnew.PCB_ZONE_T}
                other=[t for t in b.GetTracks() if int(t.this)!=int(via.this)]+list(pads.values())
                touching=[x.m_Uuid.AsString() for x in other if x.IsOnLayer(layer) and via.GetEffectiveShape(layer).Collide(x.GetEffectiveShape(layer),0)]
                r.update(cap_connected=int(via.this) in connected,filled_plane_contacts=sorted(zones&native),touching_nonzone_on_plane=touching,on_layer=conn.IsConnectedOnLayer(via,layer))
                r['path_connected']=r['cap_connected'] and bool(zones&native) and r['on_layer'] and not touching
            else:r['path_connected']=False
        else:
            target=pads[padkey(route['to_pad'])]
            r.update(to_pad=padkey(route['to_pad']),path_connected=int(target.this) in connected)
        rows.append(r)
    check_native(b,raw)
    output={'board_sha256':digest(raw),'paths':rows,'connected_paths':sum(bool(r['path_connected']) for r in rows),'limits':'Connectivity/filled-plane diagnostic only; DRC, exact route geometry, hardware and physical performance are separate.'}
    (directory/'power-diagnostic.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'connected_paths':output['connected_paths'],'total':len(rows)}))
if __name__=='__main__':diagnose(Path(sys.argv[1]))
