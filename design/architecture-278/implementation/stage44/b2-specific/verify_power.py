"""Check actual filled-plane contacts for the twelve proposed supply/return vias."""
from pathlib import Path
import argparse
import json
from collections import Counter
import math
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stage41/native-pilot"))
from identity_guard import digest


EXPECTED = []
for ic, cap, pin, net, plane in [
    ('U3202','C3206','4','+12V','In4.Cu'), ('U3202','C3207','11','-12V','In3.Cu'),
    ('U3201','C3204','13','+12V','In4.Cu'), ('U3201','C3205','4','-12V','In3.Cu'),
    ('U3203','C3208','4','+12V','In4.Cu'), ('U3203','C3209','11','-12V','In3.Cu')]:
    EXPECTED.extend([
        ('IC-to-bypass supply',ic+':'+pin,cap+':1',net,None),
        ('supply plane fanout',cap+':1',None,net,plane),
        ('bypass ground return',cap+':2',None,'AGND','In1.Cu'),
    ])


def validate_manifest(paths):
    actual=Counter((r['role'],r['from_pad'],r.get('to_pad'),r['net'],r.get('plane')) for r in paths)
    if actual!=Counter(EXPECTED):raise ValueError('exact eighteen power paths required')
    for r in paths:
        if ('via_mm' in r)!=(r['role']!='IC-to-bypass supply'):
            raise ValueError('path geometry type mismatch')


def pad_face(board, pad):
    # KiCad PAD.GetLayer() can report F.Cu for rear SMD pads; use the parent
    # footprint side and require the actual pad layer set to contain it.
    layer=pad.GetParentFootprint().GetLayer()
    name=board.GetLayerName(layer)
    if name not in ('F.Cu','B.Cu') or not pad.IsOnLayer(layer):
        raise ValueError('power pad missing on footprint face')
    return name


def verify(board_path, paths_path, proposal_path, output):
    import pcbnew
    from native_guard import check_native
    raw=board_path.read_text();b=pcbnew.LoadBoard(str(board_path));check_native(b,raw)
    conn=b.GetConnectivity();conn.RecalculateRatsnest();check_native(b,raw)
    paths=json.loads(paths_path.read_text())['paths'];validate_manifest(paths);results=[]
    proposal=json.loads(proposal_path.read_text());rows=proposal['copper'];used=set()
    audit=json.loads(board_path.with_name('identity-audit.json').read_text())
    if not audit['accepted_identity_only'] or audit['raw_sha256']!=digest(raw) or digest(proposal_path.read_text()) not in audit['proposal_sha256']:
        raise ValueError('power proposal is not bound to current complete audit')
    if proposal['removed_uuids'] or len(rows)!=30:raise ValueError('exact thirty additive power objects required')
    def segment(start,end,net,face):
        matches=[r for r in rows if r['kind']=='segment' and r['net']==net and r['layer']==face and ((r['start_nm']==start and r['end_nm']==end) or (r['start_nm']==end and r['end_nm']==start))]
        if len(matches)!=1:raise ValueError('missing/ambiguous explicit power segment')
        used.add(matches[0]['uuid'])
    point=lambda p:[p.GetPosition().x,p.GetPosition().y]
    pads={f.GetReference()+':'+p.GetNumber():p for f in b.GetFootprints() for p in f.Pads()}
    for route in paths:
        source=pads[route['from_pad']]
        if source.GetNetname()!=route['net']:raise ValueError('source net mismatch')
        connected={int(x.this) for x in conn.GetConnectedItems(source)}|{int(source.this)}
        row=dict(route)
        if 'via_mm' in route:
            pos=tuple(round(x*1000000) for x in route['via_mm'])
            matches=[t for t in b.GetTracks() if t.Type()==pcbnew.PCB_VIA_T and (t.GetPosition().x,t.GetPosition().y)==pos and t.GetNetname()==route['net']]
            if len(matches)!=1:raise ValueError('ambiguous/missing power via')
            via=matches[0];layer=b.GetLayerID(route['plane'])
            explicit=[r for r in rows if r['kind']=='via' and r['uuid']==via.m_Uuid.AsString() and r['net']==route['net'] and tuple(r['at_nm'])==pos]
            if len(explicit)!=1:raise ValueError('via not in exact power proposal')
            used.add(explicit[0]['uuid']);segment(point(source),list(pos),route['net'],pad_face(b,source))
            length=math.dist(point(source),pos)/1000000
            if [round(x*1000000) for x in route['start_mm']]!=point(source):raise ValueError('fanout source pose mismatch')
            zones=[z.m_Uuid.AsString() for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()==route['net'] and z.IsOnLayer(layer) and z.GetFilledPolysList(layer).Contains(via.GetPosition())]
            # KiCad's SWIG wrapper cannot marshal initializer_list<KICAD_T>.
            # Prove that any connection on this layer can only be a zone:
            # reject every touching non-zone pad/track/via, even same-net ones.
            others=[t for t in b.GetTracks() if int(t.this)!=int(via.this)]+list(pads.values())
            touching=[x.m_Uuid.AsString() for x in others if x.IsOnLayer(layer) and via.GetEffectiveShape(layer).Collide(x.GetEffectiveShape(layer),0)]
            native_zones={x.m_Uuid.AsString() for x in conn.GetConnectedItems(via) if x.Type()==pcbnew.PCB_ZONE_T}
            if touching or not (set(zones)&native_zones):raise ValueError('intended-layer connection not uniquely attributable to filled zone')
            row.update(via_uuid=via.m_Uuid.AsString(),filled_plane_centers=zones,
                       native_connected_filled_zones=sorted(set(zones)&native_zones),
                       touching_non_zone_objects_on_plane=touching,
                       native_connected_on_intended_layer=conn.IsConnectedOnLayer(via,layer),
                       native_connected_to_cap=int(via.this) in connected)
            if not zones or not row['native_connected_on_intended_layer'] or not row['native_connected_to_cap']:raise ValueError('power plane/return connection missing')
        else:
            target=pads[route['to_pad']]
            if pad_face(b,source)!=pad_face(b,target):raise ValueError('cross-face bypass path')
            segment(point(source),point(target),route['net'],pad_face(b,source))
            length=math.dist(point(source),point(target))/1000000
            row['native_pin_cap_connected']=target.GetNetname()==route['net'] and int(target.this) in connected
            if not row['native_pin_cap_connected']:raise ValueError('IC bypass supply connection missing')
        if not math.isclose(length,route['length_mm'],abs_tol=1e-8):raise ValueError('manifest length mismatch')
        results.append(row)
    if used!={r['uuid'] for r in rows} or len(used)!=30:raise ValueError('unused/duplicate proposed power objects')
    check_native(b,raw)
    result={'board_sha256':digest(raw),'version':pcbnew.GetBuildVersion(),'paths':results,
            'accepted_native_connections_only':True,'limits':'Native geometric connectivity only; no measured impedance, inductance, analog performance or physical verification.'}
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'verified_paths':len(results),'plane_fanouts':sum('via_mm' in r for r in results)}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('board','paths','proposal','output'):p.add_argument(name,type=Path)
    a=p.parse_args();verify(a.board,a.paths,a.proposal,a.output)
