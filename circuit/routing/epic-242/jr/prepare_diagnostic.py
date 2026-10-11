"""Bind a deliberately ineligible JR cut diagnostic to the accepted e0 input."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'baseline'
BOARD = 'osc-jack-right'
PARENT = '1da1909846dc3255888ecd36c88cee9737c85834'
CUTS = ['442e7644-a809-56c5-ab71-def9002bb651',
        'bdd4ac83-1db1-508d-9e60-d7412a183e2d']
SOURCE_PAD = '39d6be8f-f486-5bef-b690-8424c94627a2'
PREFIX = '.circuit-cache/osc-jack-right-grid-shards-fresh/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def validate_dump(dump, endpoints):
    if dump['board_sha256'] != endpoints['settled_board_sha256']:
        raise ValueError('retained dump is bound to a different board')
    if dump['open_edges'] != 129 or sum(len(g)-1 for g in dump['islands'].values()) != 129:
        raise ValueError('retained complete native edge count changed')
    pads = {p['uuid']: p for p in dump['pads']}
    if len(pads) != len(dump['pads']):
        raise ValueError('duplicate pad identity')
    actual = {}
    for net, groups in dump['islands'].items():
        actual[net] = sorted((len(g), sha(json.dumps(sorted(g), separators=(',', ':')).encode()),
                             tuple(sorted(u for u in g if u in pads))) for g in groups)
    expected = {net: sorted((g['all_member_count'], g['all_sorted_members_sha256'],
                             tuple(sorted(p['uuid'] for p in g['pads']))) for g in groups)
                for net, groups in endpoints['disconnected_nets'].items()}
    if actual != expected:
        raise ValueError('retained full group membership differs from baseline projection')
    for groups in endpoints['disconnected_nets'].values():
        for group in groups:
            for p in group['pads']:
                if any(p[k] != pads[p['uuid']][k] for k in ('ref', 'pad', 'net', 'xy', 'layers')):
                    raise ValueError('retained endpoint identity/pose changed')
    return pads


def boundary_contract(dump):
    objects = [o for kind in ('tracks', 'vias') for o in dump[kind]]
    selected = []
    for uid in CUTS:
        matches = [o for o in objects if o['uuid'] == uid]
        if len(matches) != 1 or matches[0] not in dump['tracks']:
            raise ValueError('diagnostic cut is missing, duplicate or not a segment')
        selected.append(matches[0])
    anchors = []
    for obj in selected:
        if obj['net'] in ('AGND', '+12V', '-12V', '+5V'):
            raise ValueError('diagnostic cannot cut rail/return copper')
        for side in ('a', 'b'):
            xy = obj[side]
            retained = [o['uuid'] for o in objects if o['uuid'] not in CUTS
                        and o['net'] == obj['net'] and
                        ((o.get('layer') == obj['layer'] and xy in (o.get('a'), o.get('b')))
                         or o.get('xy') == xy)]
            for pad in dump['pads']:
                poly = pad['poly']
                if not poly or pad['net'] != obj['net'] or obj['layer'] not in pad['layers']:
                    continue
                # Retained pad contact is an anchor too; the rejected short cut
                # terminates inside RB4614.1 rather than another track endpoint.
                crosses = [(b[0]-a[0])*(xy[1]-a[1])-(b[1]-a[1])*(xy[0]-a[0])
                           for a, b in zip(poly, poly[1:]+poly[:1])]
                if all(c >= 0 for c in crosses) or all(c <= 0 for c in crosses):
                    retained.append(pad['uuid'])
            if not retained:
                raise ValueError('cut lacks an explicit retained outside anchor')
            anchors.append({'cut_uuid': obj['uuid'], 'net': obj['net'],
                            'xy_nm': xy, 'layer': obj['layer'],
                            'retained_touching_uuids': sorted(retained)})
    return selected, anchors


def prepare(archive, output):
    output = output.resolve()
    if output.is_relative_to(ROOT) and not (output.is_relative_to(HERE) or output.is_relative_to(ROOT / '.circuit-cache')):
        raise ValueError('output must stay in the JR lane or disposable cache')
    endpoints = read(BASELINE / 'jr-endpoints.json')
    artifact = read(BASELINE / 'accepted-artifacts.json')['JR']
    archive_bytes = archive.read_bytes()
    if len(archive_bytes) != artifact['size_in_bytes'] or 'sha256:' + sha(archive_bytes) != artifact['digest']:
        raise ValueError('full JR129 archive size/digest mismatch')
    source = ROOT / 'boards' / BOARD / (BOARD + '.kicad_pcb')
    if sha(source.read_bytes()) != endpoints['settled_board_sha256']:
        raise ValueError('published JR129 input changed; request a new epoch')
    with zipfile.ZipFile(archive) as z:
        raw_dump = z.read(PREFIX + 'dump.json')
        if sha(raw_dump) != endpoints['dump_sha256']:
            raise ValueError('retained fresh dump hash mismatch')
        if sha(z.read(PREFIX + BOARD + '.kicad_pcb')) != endpoints['settled_board_sha256']:
            raise ValueError('retained fresh PCB hash mismatch')
        for name, digest in endpoints['context_files'].items():
            if sha(z.read(PREFIX + name)) != digest or sha((source.parent / name).read_bytes()) != digest:
                raise ValueError('native project/library/schematic context mismatch: ' + name)
    dump = json.loads(raw_dump)
    pads = validate_dump(dump, endpoints)
    cuts, anchors = boundary_contract(dump)
    if pads[SOURCE_PAD]['net'] != 'AGND' or not any(g == [SOURCE_PAD] for g in dump['islands']['AGND']):
        raise ValueError('RB4614.2 is no longer the isolated source group')
    cases = []
    for net, groups in sorted(endpoints['disconnected_nets'].items()):
        main = max(range(len(groups)), key=lambda i: len(groups[i]['pads']))
        stranded = [g for i, g in enumerate(groups) if i != main]
        names = sorted({p['ref'] + '.' + p['pad'] for g in stranded for p in g['pads']})
        role = ('fill/AGND fragmentation' if net == 'AGND' else
                'fixed header/package escape review' if any(n.startswith('J') for n in names) else
                'local package escape review')
        cases.append({'net': net, 'open_edges': len(groups)-1, 'classification': role,
                      'classification_scope': 'source endpoint role only; legal start/via/path NOT RUN',
                      'stranded_groups': stranded, 'retained_main_group': {
                          k: v for k, v in groups[main].items() if k != 'pads'}})
    old = ROOT / 'circuit/routing/issue189/jr134-rb4614-2-ground-cut'
    rejection = read(old / 'rejection.json')
    endpoint_trial = read(old.parent / 'jr-rb4614-endpoints/result.json')
    joint_trial = read(old.parent / 'jr-rb4614-joint/result.json')
    evidence_paths = [old / 'rejection.json', old / 'artifact.json', old / 'plan.json',
                      old.parent / 'jr-rb4614-endpoints/result.json',
                      old.parent / 'jr-rb4614-joint/result.json',
                      old.parent / 'jr130-rb4615-via-branch/native-pilot-evidence.json']
    evidence = {'status': 'RETAINED NEGATIVE EVIDENCE; NOT RERUN',
                'files_sha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in evidence_paths},
                'original_artifact': read(old / 'artifact.json'),
                'ground_only': {k: rejection[k] for k in ('input_board_sha256', 'candidate_sha256',
                                'open_edges_before', 'open_edges_after', 'gate', 'adopted')},
                'endpoint_replays': [{k: t[k] for k in ('resolution', 'complete', 'diagnostics')}
                                     for t in endpoint_trial['transactions']],
                'joint_replays': [{k: t[k] for k in ('signal_order', 'complete_raster_transaction', 'diagnostics')}
                                  for t in joint_trial['transactions']],
                'prior_plan_replay_on_JR129': 'REJECTED: exact prior input hash differs; never rewritten',
                'cause': 'ground gain is insufficient: victim reconnect and retained boundary obligations remain unresolved'}
    plan = {'status': 'PROPOSED CUT-ONLY NEGATIVE DIAGNOSTIC; NATIVE NOT RUN; NEVER ADOPT',
            'issue': 251, 'parent_sha': PARENT, 'epoch': 'epic242-e0', 'board': BOARD,
            'input_board_sha256': sha(source.read_bytes()), 'input_dump_sha256': sha(raw_dump),
            'archive': artifact, 'source_ground_pad_uuid': SOURCE_PAD,
            'diagnosed_change': 'measure current native cut topology before choosing a victim reconnect strategy; no A* budget increase',
            'removed_objects': cuts, 'boundary_endpoints': anchors,
            'repair_bounds_mm': [405.7, 129.65, 419.3, 154.85],
            'restoration_obligations': ['every original group on both victim nets', 'all four retained boundaries',
                                        'AGND source and original groups', 'all +12V/-12V/+5V groups'],
            'native_acceptance': 'NOT RUN', 'complete_warning_audit': 'NOT RUN', 'adopted': False}
    output.mkdir(parents=True, exist_ok=True)
    write(output / 'cases.json', {'input_sha': PARENT, 'dump_sha256': sha(raw_dump),
                                 'native_open_edges': 129, 'signal_open_edges': 107,
                                 'agnd_open_edges': 22, 'rail_open_edges': 0, 'cases': cases})
    write(output / 'prior-rejections.json', evidence)
    write(output / 'diagnostic-plan.json', plan)
    write(output / 'cut-proposal.json', {'board_sha256': sha(source.read_bytes()),
                                       'removed_uuids': CUTS, 'copper': []})
    return plan


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, default=HERE)
    args = parser.parse_args()
    prepare(args.archive, args.output)
    print('SOURCE-BOUND NEGATIVE DIAGNOSTIC READY; native NOT RUN; no canonical writes')
