"""Read-only native contact proof for newly abandoned supply-track branches."""
from pathlib import Path
import argparse
import json
import sys
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'stage41/native-pilot'))
from native_guard import check_native
from identity_guard import digest,kind,value,top_level_spans
ROOT=Path(__file__).resolve().parents[5]


def inspect(candidate,output):
    source=ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb';raw=source.read_text()
    b=pcbnew.LoadBoard(str(source));check_native(b,raw)
    c_raw=candidate.read_text();c=pcbnew.LoadBoard(str(candidate));check_native(c,c_raw)
    baseline=json.loads((ROOT/'.circuit-cache/stage41-baseline/drc-first.json').read_text())
    report=json.loads(candidate.with_name('drc-routed.json').read_text())
    old_ids={i['uuid'] for r in baseline['violations'] if r['type']=='track_dangling' for i in r['items']}
    seeds={i['uuid'] for r in report['violations'] if r['type']=='track_dangling' for i in r['items']}-old_ids
    refs=set(json.loads(candidate.with_name('prepare-receipt.json').read_text())['scope_refs'])
    planned=set(json.loads((ROOT/'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json').read_text())['candidate_B1'])-{'J109','J110','J209','J210','D109'}
    if refs!=planned or len(refs)!=31:raise ValueError('full electronics scope binding')
    tracks=list(b.GetTracks());current=list(c.GetTracks());layers=list(b.GetEnabledLayers().CuStack())
    by={}
    for t in tracks:by.setdefault(t.m_Uuid.AsString(),[]).append(t)
    pads=[(f.GetReference()+':'+p.GetNumber(),p) for f in b.GetFootprints() for p in f.Pads()]
    current_pads=[(f.GetReference()+':'+p.GetNumber(),p) for f in c.GetFootprints() for p in f.Pads()]
    def contact(a,z):
        if not a.GetBoundingBox().Intersects(z.GetBoundingBox()):return []
        return [b.GetLayerName(l) for l in layers if a.IsOnLayer(l) and z.IsOnLayer(l) and a.GetEffectiveShape(l).Collide(z.GetEffectiveShape(l),0)]
    groups=[];seen=set()
    for seed in sorted(seeds):
        if seed in seen:continue
        if len(by.get(seed,[]))!=1:raise ValueError('ambiguous seed occurrence')
        frontier=[by[seed][0]];members={seed:frontier[0]}
        while frontier:
            t=frontier.pop()
            bridging=[p for name,p in pads if name.split(':')[0] in refs and p.GetNetname()==t.GetNetname() and contact(t,p)]
            for other in tracks:
                uid=other.m_Uuid.AsString()
                if uid in members or other.Type()==pcbnew.PCB_VIA_T:continue
                if contact(t,other) or any(contact(p,other) for p in bridging):
                    if other.GetNetname()!=t.GetNetname() or len(by[uid])!=1:raise ValueError('ambiguous/cross-net branch')
                    members[uid]=other;frontier.append(other)
        seen.update(members)
        old_pad_contacts=[];anchors={};new_contacts=[]
        for uid,t in members.items():
            old_pad_contacts += [{'track':uid,'pad':name,'net':p.GetNetname(),'layers':hits} for name,p in pads if (hits:=contact(t,p))]
            for other in tracks:
                oid=other.m_Uuid.AsString()
                if other.Type()==pcbnew.PCB_VIA_T and (hits:=contact(t,other)):
                    anchors[oid]={'uuid':oid,'net':other.GetNetname(),'layers':hits}
            for other in current:
                oid=other.m_Uuid.AsString()
                if oid not in by and (hits:=contact(t,other)):
                    new_contacts.append({'track':uid,'new_copper':oid,'net':other.GetNetname(),'layers':hits})
        now_pads=[{'track':uid,'pad':name,'net':p.GetNetname(),'layers':hits} for uid,t in members.items() for name,p in current_pads if (hits:=contact(t,p))]
        foreign=[p for p in old_pad_contacts if p['pad'].split(':')[0] not in refs]
        groups.append({'seeds':sorted(seeds&members.keys()),'track_ids':sorted(members),'net':members[seed].GetNetname(),
                       'original_pad_contacts':old_pad_contacts,'retained_via_anchors':sorted(anchors.values(),key=lambda r:r['uuid']),
                       'foreign_pad_contacts':foreign,'current_pad_contacts':now_pads,'new_route_contacts':new_contacts,
                       'local_track_retirement_screen':bool(old_pad_contacts) and not foreign and not now_pads and not new_contacts})
    # The router deliberately reconnected one now-unused old copper island.
    # Its two added segments may be withdrawn only with their owning old branch.
    search_path=ROOT/'.circuit-cache/stage42-full-b1-power/signal-proposal-priority-search.json'
    search=json.loads(search_path.read_text())
    orphan=[x for x in search['links'] if x['net']=='-12V' and x['island']==[]]
    if len(orphan)!=1 or len(orphan[0]['copper_uuids'])!=2:raise ValueError('unexpected orphan route')
    withdraw=set(orphan[0]['copper_uuids'])
    for g in groups:
        if g['new_route_contacts'] and {r['new_copper'] for r in g['new_route_contacts']} <= withdraw and not g['foreign_pad_contacts'] and not g['current_pad_contacts'] and g['original_pad_contacts']:
            g['local_track_retirement_screen']=True
            g['withdraw_orphan_route']=sorted(withdraw)
    selected={u for g in groups if g['local_track_retirement_screen'] for u in g['track_ids']}
    if any(not g['local_track_retirement_screen'] for g in groups):raise ValueError('unresolved branch ownership')
    via_ids={r['uuid'] for g in groups for r in g['retained_via_anchors']}
    orphan_details=[]
    for t in current:
        uid=t.m_Uuid.AsString()
        if uid not in withdraw:continue
        outside=[x.m_Uuid.AsString() for x in current if x.m_Uuid.AsString() not in selected|withdraw|via_ids and contact(t,x)]
        touching_pads=[name for name,p in current_pads if contact(t,p)]
        if outside or touching_pads:raise ValueError('orphan route has external functional contacts')
        orphan_details.append({'uuid':uid,'outside_contacts':outside,'pad_contacts':touching_pads})
    if len(orphan_details)!=2:raise ValueError('missing orphan objects')
    via_details=[]
    selected_tracks=frozenset(selected)
    for uid in sorted(via_ids):
        if len(by[uid])!=1:raise ValueError('ambiguous via anchor')
        t=by[uid][0]
        old_out=[x.m_Uuid.AsString() for x in tracks if x.m_Uuid.AsString() not in selected_tracks|{uid} and contact(t,x)]
        new_out=[x.m_Uuid.AsString() for x in current if x.m_Uuid.AsString() not in selected_tracks|withdraw|{uid} and contact(t,x)]
        old_pad=[name for name,p in pads if contact(t,p)]
        new_pad=[name for name,p in current_pads if contact(t,p)]
        planes=[{'net':z.GetNetname(),'layer':b.GetLayerName(l),'uuid':z.m_Uuid.AsString()} for z in b.Zones() if not z.GetIsRuleArea() for l in layers if z.IsOnLayer(l) and z.GetFilledPolysList(l).Contains(t.GetPosition())]
        expected={'-12V':'In3.Cu','+12V':'In4.Cu'}.get(t.GetNetname())
        remove=not old_out and not new_out and not new_pad and all(n.split(':')[0] in refs for n in old_pad) and len(planes)==1 and planes[0]['net']==t.GetNetname() and planes[0]['layer']==expected
        if remove:selected.add(uid)
        via_details.append({'uuid':uid,'retire':remove,'old_outside_copper':old_out,'current_outside_copper':new_out,'old_pad_contacts':old_pad,'current_pad_contacts':new_pad,'original_plane_centers':planes})
    rows=[]
    for index,(a,z) in enumerate(top_level_spans(raw)):
        part=raw[a:z]
        if kind(part) in ('segment','via') and value(part,'uuid') in selected:
            rows.append({'index':index,'kind':kind(part),'uuid':value(part,'uuid'),'net':value(part,'net'),'sha256':digest(part)})
    if len(rows)!=len(selected):raise ValueError('ambiguous retirement occurrence')
    result={'canonical_sha256':digest(raw),'candidate_sha256':digest(c_raw),'version':pcbnew.GetBuildVersion(),
            'new_dangling_seed_ids':sorted(seeds),'branches':groups,'via_contacts':via_details,
            'withdraw_new_copper':sorted(withdraw),'orphan_route_contacts':orphan_details,'search_sha256':digest(search_path.read_text()),'screened_retirements':rows,
            'limits':'Native direct-contact ownership necessary screen only; original zone-center membership does not prove annular contact or current plane connectivity. Full post-removal native partition equivalence is mandatory. Retain anchors with external contacts; removal requires independent review and full identity/connectivity/DRC checks.'}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'seeds':len(seeds),'branches':len(groups),'screened_tracks':len(rows),
                      'blocked':[g['seeds'] for g in groups if not g['local_track_retirement_screen']]}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('output',type=Path);a=p.parse_args();inspect(a.candidate,a.output)
