"""Exact native ownership screen for three abandoned local supply branches.

This does not authorize a cut by itself: final native foreign/shared pad-group
comparison after replacement connections remains mandatory.
"""
from pathlib import Path
import argparse
import json
import sys
import pcbnew
from identity_guard import digest, kind, value
from native_guard import check_native
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans
BRANCHES = [
    {'name': 'negative-IC-and-bypass', 'net': '-12V', 'plane': 'In3.Cu',
     'pads': ['U3102:11', 'C3107:1'], 'ids': ['ad4076c4-6993-563e-b756-f16bade968a8', 'd2685cd1-1b40-5f7b-812a-95ff8f967dee', 'b6a3e08a-344c-56dd-8210-3445bca58110']},
    {'name': 'positive-IC', 'net': '+12V', 'plane': 'In4.Cu', 'pads': ['U3102:4'],
     'ids': ['a7cc00f2-c575-500f-a42b-35d1ad78df1b', 'f2390319-3bbf-503b-8ce7-f134408e6163']},
    {'name': 'positive-bypass', 'net': '+12V', 'plane': 'In4.Cu', 'pads': ['C3106:1'],
     'ids': ['f442ae45-59e3-5ef8-a34a-b31090e70cfe', '7222cef1-7777-575d-9c3f-191c117c080d']},
]


def inspect(output):
    path = ROOT / 'boards/osc-jack-left/osc-jack-left.kicad_pcb'; raw = path.read_text()
    if digest(raw) != 'e984c0a01156b5f282f0c849077c61572df30ee0c70dfe6c9db94fbfcfe52107': raise ValueError('baseline binding')
    b = pcbnew.LoadBoard(str(path)); check_native(b, raw)
    tracks = list(b.GetTracks()); layers = list(b.GetEnabledLayers().CuStack())
    pads = [(f.GetReference()+':'+p.GetNumber(), p) for f in b.GetFootprints() for p in f.Pads()]
    raw_items = {}
    for index, (a, z) in enumerate(top_level_spans(raw)):
        part = raw[a:z]
        if kind(part) in ('segment', 'via'):
            raw_items.setdefault(value(part, 'uuid'), []).append({'index': index, 'kind': kind(part), 'uuid': value(part, 'uuid'), 'net': value(part, 'net'), 'sha256': digest(part)})
    for branch in BRANCHES:
        branch['retire_ids'] = branch['ids'] if branch['net'] == '-12V' else branch['ids'][:1]
        branch['retained_anchor_ids'] = [u for u in branch['ids'] if u not in branch['retire_ids']]
    results = []
    def contact(a, z):
        return [b.GetLayerName(l) for l in layers if a.IsOnLayer(l) and z.IsOnLayer(l) and a.GetEffectiveShape(l).Collide(z.GetEffectiveShape(l), 0)]
    for branch in BRANCHES:
        objects = [t for t in tracks if t.m_Uuid.AsString() in branch['ids']]
        if len(objects) != len(branch['ids']) or any(t.GetNetname() != branch['net'] for t in objects): raise ValueError('branch object mismatch')
        details = []; actual_pads = set(); adjacency = {u: set() for u in branch['ids']}; vias_on_plane = 0
        for t in objects:
            uid = t.m_Uuid.AsString(); removing = uid in branch['retire_ids']; outside = []
            for other in tracks:
                oid = other.m_Uuid.AsString()
                if oid == uid: continue
                hits = contact(t, other)
                if hits:
                    if oid in adjacency: adjacency[uid].add(oid)
                    else: outside.append({'uuid': oid, 'net': other.GetNetname(), 'layers': hits})
            pad_hits = [{'pad': name, 'net': p.GetNetname(), 'layers': hits} for name, p in pads if (hits := contact(t, p))]
            if removing: actual_pads.update(p['pad'] for p in pad_hits)
            zones = []
            if t.Type() == pcbnew.PCB_VIA_T:
                for z in b.Zones():
                    if z.GetIsRuleArea(): continue
                    for l in layers:
                        if z.IsOnLayer(l) and z.GetFilledPolysList(l).Contains(t.GetPosition()):
                            zones.append({'uuid': z.m_Uuid.AsString(), 'net': z.GetNetname(), 'layer': b.GetLayerName(l)})
                if removing and (len(zones) != 1 or zones[0]['net'] != branch['net'] or zones[0]['layer'] != branch['plane']): raise ValueError('unproved via plane role')
                vias_on_plane += 1
            if removing and (outside or any(p['pad'] not in branch['pads'] or p['net'] != branch['net'] for p in pad_hits)): raise ValueError('external branch contact: '+str(outside)+str(pad_hits))
            if len(raw_items[uid]) != 1: raise ValueError('ambiguous raw branch occurrence')
            details.append({**raw_items[uid][0], 'pad_contacts': pad_hits, 'outside_copper_contacts': outside, 'proposed_retirement': removing, 'via_plane_contains_center': zones})
        seen = {branch['ids'][0]}
        while True:
            more = seen | {v for u in seen for v in adjacency[u]}
            if more == seen: break
            seen = more
        if seen != set(branch['ids']) or actual_pads != set(branch['pads']) or vias_on_plane != 1: raise ValueError('incomplete local branch proof')
        results.append({**branch, 'objects': details, 'native_contact_graph_connected': True})
    result = {'canonical_sha256': digest(raw), 'native_version': pcbnew.GetBuildVersion(), 'branches': results,
              'limits': 'Exact local contact/plane-center screen only. Cut plus replacement still requires full native foreign/shared connectivity equality.'}
    output.write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps({'branches':len(results),'reviewed_objects':sum(len(r['objects']) for r in results), 'proposed_retirements':sum(len(r['retire_ids']) for r in results),'status':'LOCAL CONTACT SCREEN PASS; cut acceptance pending'}))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();inspect(a.output)
