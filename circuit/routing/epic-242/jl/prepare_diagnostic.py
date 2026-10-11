"""Authenticate JL117 and measure first-via availability without running a search."""
import argparse
import copy
import hashlib
import inspect
import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'baseline'
BOARD = 'osc-jack-left'
ORIGINAL_PARENT = '1da1909846dc3255888ecd36c88cee9737c85834'
PARENT = '40aa1cec58190487dc70aa5048a366e29a6b32a1'
TARGET = ('U8202.14', 'U8202.15', 'U8202.16')
TOOLS = ('scripts/pcbgen/grid_router.py', 'scripts/pcbgen/grid_astar.c',
         'scripts/pcbgen/route_jack_grid.py', 'scripts/pcbgen/route_shards.py',
         'scripts/pcbgen/local_repair_pilot.py', 'scripts/pcbgen/grid_apply.py',
         'scripts/pcbgen/grid_dump.py', 'scripts/pcbgen/copper_identity.py',
         'scripts/kicad/run.sh', 'design/boards/osc-jack-left.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def validate_dump(dump, endpoints):
    if dump['board_sha256'] != endpoints['settled_board_sha256']:
        raise ValueError('dump board binding changed')
    if dump['open_edges'] != 117 or sum(len(g)-1 for g in dump['islands'].values()) != 117:
        raise ValueError('complete native open-edge count changed')
    pads = {p['uuid']: p for p in dump['pads']}
    if len(pads) != len(dump['pads']):
        raise ValueError('duplicate pad identity')
    # The authenticated accepted dump contains eleven repeated track UUIDs.
    # Preserve every track row; never deduplicate copper or manufacture new IDs.
    actual = {net: sorted((len(g), sha(json.dumps(sorted(g), separators=(',', ':')).encode()),
                          tuple(sorted(u for u in g if u in pads))) for g in groups)
              for net, groups in dump['islands'].items()}
    expected = {net: sorted((g['all_member_count'], g['all_sorted_members_sha256'],
                            tuple(sorted(p['uuid'] for p in g['pads']))) for g in groups)
                for net, groups in endpoints['disconnected_nets'].items()}
    if actual != expected:
        raise ValueError('full native group membership changed, even if edge totals match')
    for groups in endpoints['disconnected_nets'].values():
        for group in groups:
            for p in group['pads']:
                if any(p[k] != pads[p['uuid']][k] for k in ('ref', 'pad', 'net', 'xy', 'layers')):
                    raise ValueError('endpoint identity or pose changed')
    return pads


def authenticate(archive):
    endpoints = read(BASELINE / 'jl-endpoints.json')
    artifact = read(BASELINE / 'accepted-artifacts.json')['JL']
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if archive.stat().st_size != artifact['size_in_bytes'] or 'sha256:' + digest != artifact['digest']:
        raise ValueError('full JL117 archive size/digest mismatch')
    source = ROOT / 'boards' / BOARD / (BOARD + '.kicad_pcb')
    if sha(source.read_bytes()) != endpoints['settled_board_sha256']:
        raise ValueError('published JL input changed; request coordinator epoch')
    prefix = endpoints['member'].removesuffix('dump.json')
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate archive member')
        raw_dump = z.read(endpoints['member'])
        if sha(raw_dump) != endpoints['dump_sha256']:
            raise ValueError('retained dump hash mismatch')
        if sha(z.read(prefix + source.name)) != endpoints['settled_board_sha256']:
            raise ValueError('retained settled PCB hash mismatch')
        for name, digest in endpoints['context_files'].items():
            if sha(z.read(prefix + name)) != digest or sha((source.parent / name).read_bytes()) != digest:
                raise ValueError('native context changed: ' + name)
    dump = json.loads(raw_dump)
    validate_dump(dump, endpoints)
    return dump, endpoints, artifact


def target_members(dump):
    pads = {p['uuid']: p for p in dump['pads']}
    found = [g for g in dump['islands']['AGND']
             if tuple(sorted(pads[u]['ref'] + '.' + pads[u]['pad'] for u in g if u in pads)) == TARGET]
    if len(found) != 1 or len(found[0]) != 3:
        raise ValueError('target must remain the exact three-pad group with no track/via source')
    if any(pads[u]['layers'] != ['F.Cu'] for u in found[0]):
        raise ValueError('target has unexpected through or non-F.Cu source')
    return found[0]


def first_via_mask(free, via_ok, src, goal, *unused):
    """Observe the existing router masks; return no path and never call A*.

    Eight-neighbour flood connectivity is an optimistic same-layer upper bound.
    No reachable first via means no via fanout on this exact bounded raster. A
    positive result would not prove a route or native electrical legality.
    """
    import numpy as np
    from scipy import ndimage
    rows = []
    for li in range(len(free)):
        labels, _ = ndimage.label(free[li] | src[li], np.ones((3, 3), int))
        identities = np.unique(labels[src[li]])
        identities = identities[identities != 0]
        reachable = np.isin(labels, identities) if len(identities) else np.zeros_like(via_ok)
        sites = reachable & via_ok & ~src[li] & free[li]
        rows.append({'layer_index': li, 'source_cells': int(src[li].sum()),
                     'optimistic_reachable_cells': int(reachable.sum()),
                     'reachable_first_via_cells': int(sites.sum())})
    return {'window_shape': list(free.shape), 'source_cells': int(src.sum()),
            'legal_via_cells': int(via_ok.sum()), 'layers': rows,
            'negative': not any(r['reachable_first_via_cells'] for r in rows),
            'search_executed': False, 'native_executed': False}


def probe_masks(dump):
    sys.path.insert(0, str(ROOT))
    import numpy
    import scipy
    import shapely
    from scripts.pcbgen import grid_router as router
    probe = copy.deepcopy(dump)
    probe['islands'] = {'AGND': [target_members(dump)]}
    from attribution import explain, existing_anchors
    observed = []
    anchor_observation = None
    # Hold allocation, lattice, obstacles, rules and budget fixed. Only the
    # computational first-via search window changes from 3 to 6 mm.
    bounds = [232.7, 147.25, 248.1, 161.3]
    for window in (3, 6, 100):
        masks = []

        def observe(*args):
            context = inspect.currentframe().f_back.f_locals
            result = first_via_mask(*args)
            if window == 100:
                result['existing_anchor_hypothesis'] = existing_anchors(context, args[0], args[2], dump, target_members(dump))
            else:
                result['attribution'] = explain(context, args[0], args[1], args[2])
            masks.append(result)
            return None, 0

        with patch.object(router, 'astar', observe), patch.object(
                router, 'native_astar', side_effect=AssertionError('native search forbidden')):
            results, cuts = router.route(
                probe, nets=['AGND'], planes={'AGND': 'In1.Cu'}, res=0.025,
                clearance=0.25, rail_nets=['+12V', '-12V', '+5V', 'AGND'],
                rail_width=0.3, via_diameter=0.6, via_drill=0.3,
                allowed_layers=['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu'],
                grow={n: 0.05 for n in ('+12V', '-12V', '+5V', 'AGND')},
                bounds_mm=bounds, plane_window_mm=window,
                plane_max_expansions=300000, max_expansions=300000, log=lambda *args: None)
        if cuts or any(r['path'] is not None for r in results) or len(masks) != 1:
            raise ValueError('mask-only diagnostic unexpectedly routed or removed copper')
        # Mock-generated router failure reasons are not measured search evidence.
        if window == 100:
            anchor_observation = masks[0]['existing_anchor_hypothesis']
        else:
            observed.append({'plane_window_mm': window, **masks[0]})
    return {'status': 'SOURCE MASK DIAGNOSTIC; NO SEARCH / NO COPPER / NATIVE NOT RUN',
            'target': list(TARGET), 'target_uuids': sorted(target_members(dump)),
            'bounds_mm': bounds, 'res_mm': 0.025, 'track_width_mm': 0.3,
            'via_diameter_mm': 0.6, 'via_drill_mm': 0.3, 'clearance_mm': 0.25,
            'changed_cause': 'first-via window only: 3 mm versus 6 mm; no expansion-budget increase',
            'classification': 'no reachable first via on tested raster' if all(r['negative'] for r in observed)
                              else 'first-via availability; path and native legality unresolved',
            'scope': 'bounded conservative router geometry only; not physical impossibility or native acceptance',
            'observations': observed,
            'existing_anchor_hypothesis': anchor_observation,
            'zone_pour_scope': 'Poured zones ignored by router mask: no poured-zone blocker/connectivity attribution',
            'dependencies': {'numpy': numpy.__version__, 'scipy': scipy.__version__, 'shapely': shapely.__version__}}


def case_projection(endpoints):
    cases = []
    for net, groups in sorted(endpoints['disconnected_nets'].items()):
        kind = ('fill/AGND fragmentation' if net == 'AGND' else 'rail restoration' if net in ('+12V', '-12V', '+5V')
                else 'fixed header/package escape review' if any(p['ref'].startswith('J') for g in groups for p in g['pads'])
                else 'local package escape review')
        cases.append({'net': net, 'open_edges': len(groups)-1, 'classification': kind,
                      'classification_scope': 'endpoint role only; legal starts/vias/search limits unresolved except measured U8202 diagnostic',
                      'groups': groups})
    return {'parent_sha': PARENT, 'original_parent_sha': ORIGINAL_PARENT, 'epoch': 'epic242-e0',
            'native_open_edges': 117, 'signal_open_edges': 103, 'agnd_open_edges': 14,
            'rail_open_edges': 0, 'dump_sha256': endpoints['dump_sha256'], 'cases': cases}


def products(archive):
    dump, endpoints, artifact = authenticate(archive)
    diagnostic = probe_masks(dump)
    pads = {p['ref'] + '.' + p['pad']: p for p in dump['pads']}
    vulnerable = ('C8122.1', 'C2322.1', 'U8106.4', 'C8124.1', 'U2304.4', 'U8105.4')
    if '-12V' in dump['islands'] or any(pads[n]['net'] != '-12V' for n in vulnerable):
        raise ValueError('the original six-pad rail preservation contract changed')
    inputs = {p: sha((ROOT / p).read_bytes()) for p in TOOLS}
    inputs.update({str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in (
        BASELINE / 'jl-endpoints.json', BASELINE / 'accepted-artifacts.json',
        BASELINE / 'harness-contract.json', HERE / 'prior-rejections.json', HERE / 'attribution.py')})
    plan = {'status': 'BOUNDED NEGATIVE SOURCE DIAGNOSTIC READY; NATIVE NOT RUN',
            'issue': 250, 'parent_sha': PARENT, 'original_parent_sha': ORIGINAL_PARENT,
            'epoch': 'epic242-e0', 'board': BOARD, 'adopted': False,
            'published_board_sha256': endpoints['settled_board_sha256'],
            'retained_settled_board_sha256': endpoints['settled_board_sha256'],
            'retained_dump_sha256': endpoints['dump_sha256'], 'archive': artifact,
            'context_files': endpoints['context_files'], 'source_tool_sha256': inputs,
            'diagnostic': diagnostic,
            'six_pad_minus12_preservation_obligation': [pads[n] for n in vulnerable],
            'next_method_review': 'Do not enlarge A* budget or replay PR233. Review a legal first-via escape and full signal/AGND/minus12 restoration together before proposing copper.',
            'native_proposal_scope': 'Optional baseline settle/fresh and mask reproduction only; no search, cuts, added copper, merge or promotion',
            'native_acceptance': 'NOT RUN', 'complete_warning_audit': 'NOT RUN',
            'new_native_slot': None}
    return {'cases.json': case_projection(endpoints), 'diagnostic-plan.json': plan,
            'no-copper-proposal.json': {'board_sha256': endpoints['settled_board_sha256'],
                                       'removed_uuids': [], 'copper': []}}


def prepare(archive, output, check=False):
    output = output.resolve()
    if output.is_relative_to(ROOT) and not (output.is_relative_to(HERE) or output.is_relative_to(ROOT / '.circuit-cache')):
        raise ValueError('output must stay in JL lane or disposable cache')
    values = products(archive)
    if check:
        for name, value in values.items():
            if (output / name).read_bytes() != encoded(value):
                raise ValueError('source diagnostic drift: ' + name)
    else:
        output.mkdir(parents=True, exist_ok=True)
        for name, value in values.items():
            (output / name).write_bytes(encoded(value))
    return values


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, default=HERE)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    values = prepare(args.archive, args.output, args.check)
    print(values['diagnostic-plan.json']['diagnostic']['classification'])
    print('SOURCE CHECK PASS; native NOT RUN; no route search or canonical writes')
