"""Read-only native ownership screen for B2 local supply branches."""
from pathlib import Path
import json,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from native_guard import check_native
from identity_guard import digest,kind,value,top_level_spans
BASE=ROOT/'.circuit-cache/stage42-full-b1-fresh/osc-jack-left.kicad_pcb'
BASE_HASH='975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b'
REFS={'U3201','U3202','U3203',*('C'+str(n) for n in range(3201,3210)),*('R'+str(n) for n in range(3201,3215)),*('D'+str(n) for n in range(3201,3206))}

def inspect(output):
    raw=BASE.read_text()
    if digest(raw)!=BASE_HASH:raise ValueError('baseline binding')
    b=pcbnew.LoadBoard(str(BASE));check_native(b,raw);layers=list(b.GetEnabledLayers().CuStack())
    tracks=list(b.GetTracks());pads=[(f.GetReference()+':'+p.GetNumber(),p) for f in b.GetFootprints() for p in f.Pads()]
    shared={'+12V','-12V','+5V'}
    local=[(n,p) for n,p in pads if n.split(':')[0] in REFS and p.GetNetname() in shared]
    segments=[t for t in tracks if t.Type()==pcbnew.PCB_TRACE_T and t.GetNetname() in shared]
    by={}
    for t in tracks:by.setdefault(t.m_Uuid.AsString(),[]).append(t)
    def contact(a,z):
        if not a.GetBoundingBox().Intersects(z.GetBoundingBox()):return []
        return [b.GetLayerName(l) for l in layers if a.IsOnLayer(l) and z.IsOnLayer(l) and a.GetEffectiveShape(l).Collide(z.GetEffectiveShape(l),0)]
    seeds=[t for t in segments if any(p.GetNetname()==t.GetNetname() and contact(t,p) for n,p in local)]
    seen=set();groups=[];selected=set();anchors=set()
    for seed in seeds:
        uid=seed.m_Uuid.AsString()
        if uid in seen:continue
        members={uid:seed};queue=[seed]
        while queue:
            t=queue.pop();bridges=[p for n,p in local if p.GetNetname()==t.GetNetname() and contact(t,p)]
            for other in segments:
                oid=other.m_Uuid.AsString()
                if oid in members:continue
                if contact(t,other) or any(contact(p,other) for p in bridges):
                    if other.GetNetname()!=t.GetNetname() or len(by[oid])!=1:raise ValueError('ambiguous/cross-net branch')
                    members[oid]=other;queue.append(other)
        seen.update(members)
        contacts=[{'object':u,'pad':n,'net':p.GetNetname(),'layers':hits} for u,t in members.items() for n,p in pads if (hits:=contact(t,p))]
        foreign=[x for x in contacts if x['pad'].split(':')[0] not in REFS]
        boundary={x.m_Uuid.AsString() for t in members.values() for x in tracks if x.Type()==pcbnew.PCB_VIA_T and contact(t,x)}
        eligible=bool(contacts) and not foreign
        if eligible:selected.update(members);anchors.update(boundary)
        groups.append({'net':seed.GetNetname(),'track_ids':sorted(members),'pad_contacts':contacts,'foreign_pad_contacts':foreign,'boundary_vias':sorted(boundary),'local_track_screen':eligible})
    vias=[]
    for uid in sorted(anchors):
        if len(by[uid])!=1:raise ValueError('ambiguous via occurrence')
        v=by[uid][0]
        outside=[x.m_Uuid.AsString() for x in tracks if x.m_Uuid.AsString() not in selected|{uid} and contact(v,x)]
        touches=[n for n,p in pads if contact(v,p)]
        planes=[{'uuid':z.m_Uuid.AsString(),'net':z.GetNetname(),'layer':b.GetLayerName(l)} for z in b.Zones() if not z.GetIsRuleArea() for l in layers if z.IsOnLayer(l) and z.GetFilledPolysList(l).Contains(v.GetPosition())]
        expected={'+12V':'In4.Cu','-12V':'In3.Cu'}.get(v.GetNetname())
        eligible=not outside and all(n.split(':')[0] in REFS for n in touches) and len(planes)==1 and planes[0]['net']==v.GetNetname() and planes[0]['layer']==expected
        if eligible:selected.add(uid)
        vias.append({'uuid':uid,'net':v.GetNetname(),'outside_copper':outside,'pad_contacts':touches,'original_plane_centers':planes,'retire_screen':eligible})
    rows=[]
    for index,(a,z) in enumerate(top_level_spans(raw)):
        p=raw[a:z]
        if kind(p) in ('segment','via') and value(p,'uuid') in selected:rows.append({'index':index,'kind':kind(p),'uuid':value(p,'uuid'),'net':value(p,'net'),'sha256':digest(p)})
    if len(rows)!=len(selected):raise ValueError('ambiguous retirement raw occurrence')
    check_native(b,raw)
    result={'baseline_sha256':BASE_HASH,'scope_refs':sorted(REFS),'branches':groups,'via_contacts':vias,'screened_retirements':rows,'limits':'Necessary baseline direct-contact ownership screen only. Plane-center evidence is not current native zone contact. Fresh layout, complete retained partitions and DRC remain mandatory.'}
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'branches':len(groups),'retirements':len(rows),'retained_branches':sum(not g['local_track_screen'] for g in groups),'retained_vias':sum(not v['retire_screen'] for v in vias)}))
if __name__=='__main__':inspect(Path(sys.argv[1]))
