"""Attribute existing opens before any full-B1 native transformation."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'design/architecture-278/implementation/stage41/native-pilot'))
from acceptance import connectivity_gate


def classify(snapshot, refs):
    if not connectivity_gate(snapshot, snapshot)['accepted_connectivity_only']:
        raise ValueError('invalid complete native snapshot')
    objects = snapshot['objects']
    owned = {k for k, v in objects.items() if v['kind'] == 'pad' and v['ref'] in refs}
    if {objects[k]['ref'] for k in owned} != set(refs):
        raise ValueError('missing B1 package pads')
    rows = []
    for net, groups in snapshot['groups'].items():
        own_groups = [[k for k in group if k in owned] for group in groups]
        own_groups = [g for g in own_groups if g]
        if own_groups:
            rows.append({'net': net, 'components': len(groups), 'b1_components': len(own_groups),
                         'b1_pads': sorted(objects[k]['ref'] + ':' + objects[k]['pin']
                                           for g in own_groups for k in g),
                         'classification': 'shared ground openings' if net == 'AGND' and len(groups) > 1
                         else 'closed' if len(groups) == 1 else 'B1-associated open'})
    return rows


def validate_drc_count(snapshot, drc):
    if len(drc['unconnected_items']) != snapshot['native_open_edges']:
        raise ValueError('DRC open count differs from complete snapshot')


def run(output):
    files = {
        'plan': ROOT / 'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json',
        'baseline': ROOT / '.circuit-cache/stage41-baseline/connectivity-complete.json',
        'baseline_drc': ROOT / '.circuit-cache/stage41-baseline/drc-first.json',
        'stage41': ROOT / '.circuit-cache/stage41-pilot-fresh/connectivity-passfresh.json',
        'stage41_drc': ROOT / '.circuit-cache/stage41-pilot-fresh/drc-passfresh.json',
    }
    data = {k: json.loads(p.read_text()) for k, p in files.items()}
    refs = set(data['plan']['candidate_B1'])
    if len(refs) != 36:
        raise ValueError('B1 package scope drift')
    result = {'source_sha256': {k: hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()},
              'b1_refs': sorted(refs), 'snapshots': {}}
    for name in ('baseline', 'stage41'):
        snap = data[name]
        board = ROOT / ('.circuit-cache/stage41-baseline/osc-jack-left.kicad_pcb' if name == 'baseline'
                        else '.circuit-cache/stage41-pilot-fresh/osc-jack-left.kicad_pcb')
        if hashlib.sha256(board.read_bytes()).hexdigest() != snap['board_sha256']:
            raise ValueError('snapshot/board binding mismatch')
        validate_drc_count(snap, data[name + '_drc'])
        pads = {json.loads(k)[2]: v for k,v in snap['objects'].items() if v['kind'] == 'pad'}
        item_nets = {}
        for key, value in snap['objects'].items():
            uid = json.loads(key)[2] if value['kind'] == 'pad' else value['uuid']
            item_nets.setdefault(uid, set()).add(value['net'])
        nets = {v['net'] for v in pads.values() if v['ref'] in refs}
        rows = []
        for index, edge in enumerate(data[name + '_drc']['unconnected_items']):
            endpoints = [pads.get(x['uuid']) for x in edge['items']]
            direct = [x for x in endpoints if x and x['ref'] in refs]
            # Zone endpoints are deliberately not assigned to a module by location.
            descriptions = [x['description'] for x in edge['items']]
            shared = all(x.startswith('Zone ') and '[AGND]' in x for x in descriptions)
            foreign = all(item_nets.get(x['uuid']) and not item_nets[x['uuid']] & nets
                          for x in edge['items'])
            category = 'direct B1' if direct else 'shared AGND' if shared else 'foreign' if foreign else 'unknown'
            rows.append({'index': index, 'classification': category, 'items': edge['items']})
        result['snapshots'][name] = {'board_sha256': snap['board_sha256'],
            'native_open_edges': snap['native_open_edges'], 'b1_nets': classify(snap, refs),
            'open_items': rows, 'counts': {c: sum(x['classification'] == c for x in rows)
                                         for c in ('direct B1', 'shared AGND', 'foreign', 'unknown')}}
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v['counts'] for k,v in result['snapshots'].items()}))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();run(a.output)
