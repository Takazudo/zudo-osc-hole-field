#!/usr/bin/env python3
"""Three predeclared additive P-to-KA land access pilots; never a source bridge.

Uses construct_access.Obstacles and its cumulative sheet severance guard. No
routing, site search, copper replacement, native calls or ideal star is added.
Every original object survives byte-for-byte as a JSON value. A legal local
proposal is not credited until the complete graph/census and finite path checks.
"""
import argparse
import copy
import hashlib
import json
import resource
import uuid
from pathlib import Path
from collections import defaultdict
import shapely
from shapely.geometry import Point, Polygon, LineString
import construct_access as ca

NS = uuid.UUID('e16feedb-0000-5000-8000-000000000242')
VARIANTS = ('parallel-vias', 'wider-face', 'combined')

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def digest(objects):
    h = hashlib.sha256()
    for chunk in json.JSONEncoder(sort_keys=True, separators=(',', ':'), allow_nan=False).iterencode(objects):
        h.update(chunk.encode())
    return h.hexdigest()

def write_json(path, value, compact=False):
    """Stream large source and report documents without a second full string."""
    with Path(path).open('w') as stream:
        json.dump(value, stream, sort_keys=True, separators=(',', ':') if compact else None,
                  indent=None if compact else 2, allow_nan=False)
        stream.write('\n')

def check_seals(paths, seals):
    need(all(sha(path) == seals[key] for key, path in paths.items()),
         'input, predeclaration or method changed during pilot')

def sheet_witness(row, polygon, window, seal_cache):
    """Exact full-sheet identity plus bounded geometry; sealed planes own the rest."""
    identity = (row['net'], row['id'])
    if identity not in seal_cache:
        seal_cache[identity] = digest(row)
    local = polygon.intersection(window)
    return {'sheet_id': row['id'], 'net': row['net'], 'layer': row['layer'],
            'canonical_record_sha256': seal_cache[identity],
            'full_record_locator': 'planes.clipped_sheets.' + row['net'] + '[id=' + row['id'] + ']',
            'geometry_scope': 'Complete original sheet record remains in sealed input planes; WKB is its exact intersection with this declared local window.',
            'window_wkb': shapely.to_wkb(window, hex=True),
            'local_sheet_wkb': shapely.to_wkb(local, hex=True),
            'local_area_mm2': local.area}

def source_dependency(contract, source):
    """Retain exact absent raw/load interface and branch direction evidence."""
    boundary = contract['external_boundary']
    abstract = boundary['abstract_parts']
    need({o['ref'] for o in abstract} == {'CN301', 'XB301'}, 'changed source interface: review required')
    actual = [o for o in source['objects'] if o.get('ref') in ('CN301', 'XB301')]
    absent = boundary['no_physical_bridge'] and not actual and all(not o['footprint'] and not o['in_bom'] for o in abstract)
    wires = contract['existing_main_wires']
    need(len({w['id'] for w in wires}) == len(wires), 'duplicate physical wire charge identity')
    lands = {o['reference']: o for o in contract['existing_main_lands']}
    p_wires = [w for w in wires if w['id'].startswith('POWER-P-')]
    need(len(p_wires) == 6, 'changed P-to-KA wire set: review required')
    return {'status': 'SOURCE_DEPENDENCY_NEGATIVE' if absent else 'SOURCE_INTERFACE_CHANGED_REVIEW_REQUIRED',
            'external_boundary': copy.deepcopy(boundary), 'matching_source_objects': actual,
            'p_receiving_lands': [lands[r] for w in p_wires for r in w['terminal_refs'] if lands[r]['candidate_owner'] == 'KA'],
            'physical_wires': copy.deepcopy(wires),
            'finite_charge_policy': 'Each exact wire ID and each physical end termination must occur once. Existing wire metadata supplies only a maximum length, not an actual routed source/star section. No wire, termination, raw/load bridge or P-side copper is inferred by this pilot.',
            'complete_source_to_load_result': 'NOT ESTABLISHED: CN301/XB301 have empty footprints, no BOM population and no physical raw/load bridge. Local land-access copper cannot close this dependency.'}

class Witnesses:
    """IDs and complete original records for every conservative obstacle hit."""
    def __init__(self, objects):
        self.objects = objects
        self.obs = ca.Obstacles(objects)
        self.index = defaultdict(list)
        self.drills = []
        self.forbid = defaultdict(list)
        for o in objects:
            if o['kind'] == 'rule_area':
                if o['rules'].get('vias') == 'not_allowed' or o['rules'].get('tracks') == 'not_allowed':
                    for layer in o['layers']:
                        self.forbid[layer].append(o)
                continue
            if ca.copper(o) is not None:
                for layer in o['layers']:
                    self.index[layer].append(o)
            if o.get('drill_mm', 0) > 0:
                self.drills.append(o)

    def hits(self, shape, layers, net, drill_shape=None):
        result = []
        for layer in layers:
            tree = self.obs.trees.get(layer)
            if tree is not None:
                for i in tree.query(shape, predicate='intersects'):
                    obj = self.index[layer][int(i)]
                    if obj.get('net', '') != net:
                        result.append({'reason': 'copper', 'layer': layer, 'object': obj})
            tree = self.obs.forbid_trees.get(layer)
            if tree is not None:
                for i in tree.query(shape, predicate='intersects'):
                    result.append({'reason': 'rule_area', 'layer': layer, 'object': self.forbid[layer][int(i)]})
        if drill_shape is not None and self.obs.drill_tree is not None:
            for i in self.obs.drill_tree.query(drill_shape, predicate='intersects'):
                result.append({'reason': 'drill', 'object': self.drills[int(i)]})
        need(bool(result) == bool(self.obs.blocked(shape, layers, net, drill_shape)), 'obstacle witness parity failed')
        return sorted(result, key=lambda r: (r['reason'], r.get('layer', ''), r['object']['id']))

def sheets_from(planes):
    rows = planes['clipped_sheets']
    result = {}
    for net, records in rows.items():
        polygons = [Polygon(r['polygon_mm'], r['holes_mm']) for r in records]
        result[net] = (shapely.STRtree(polygons), polygons)
    return result

def pilot_objects(source, plan, variant):
    need(variant in VARIANTS, 'undeclared variant')
    byid = {o['id']: o for o in source['objects']}
    out = []
    for row in plan['targets']:
        pad = byid[row['pad_id']]
        need(all(pad.get(k) == row[k] for k in ('ref', 'net', 'center_mm')), 'fixed land identity changed: ' + row['ref'])
        need(pad['kind'] == 'pad' and pad['layers'] == ['F.Cu'] and pad['pad'] == '1', 'fixed land face/pad changed')
        for k, center in enumerate(row['parallel_via_centers_mm'] if variant in ('parallel-vias', 'combined') else []):
            out.append({'id': str(uuid.uuid5(NS, row['pad_id'] + ':parallel:' + str(k))), 'kind': 'via',
                        'net': pad['net'], 'layers': list(ca.LAYERS), 'center_mm': center,
                        'diameter_mm': .6, 'drill_mm': .3, 'access_for_pad': pad['id'],
                        'epoch': 'E16-continuation-20261013b', 'via_in_pad': True,
                        'process': 'conditional filled/capped through via; no process qualification inferred'})
        target = row.get('face_target')
        if target and variant in ('wider-face', 'combined'):
            via = byid[target['object_id']]
            need(via['kind'] == 'via' and via['net'] == pad['net'] and via['center_mm'] == target['center_mm'], 'fixed face endpoint changed')
            out.append({'id': str(uuid.uuid5(NS, row['pad_id'] + ':face')), 'kind': 'segment', 'net': pad['net'],
                        'layers': ['F.Cu'], 'path_mm': [pad['center_mm'], via['center_mm']], 'width_mm': 1.,
                        'access_for_pad': pad['id'], 'face_target_id': via['id'], 'epoch': 'E16-continuation-20261013b'})
    return out

def assess(source, planes, plan, variant):
    original = source['objects']
    need(len({o['id'] for o in original}) == len(original), 'duplicate source identities')
    proposals = pilot_objects(source, plan, variant)
    need(len(proposals) <= 14, 'bounded proposal count exceeded')
    need(not ({o['id'] for o in original} & {o['id'] for o in proposals}), 'proposal UUID collides with old copper')
    obs = Witnesses(original)
    sheets = sheets_from(planes)
    byid = {o['id']: o for o in original}
    accepted, rows, prior = [], [], []
    sheet_seals = {}
    for obj in proposals:
        pad = byid[obj['access_for_pad']]
        geometry = ca.copper(obj)
        if obj['kind'] == 'via':
            point = Point(obj['center_mm'])
            hole_keep = point.buffer(obj['drill_mm']/2 + ca.HOLE_CLEARANCE, quad_segs=16)
        else:
            hole_keep = LineString(obj['path_mm']).buffer(obj['width_mm']/2 + ca.HOLE_CLEARANCE, quad_segs=8)
        keep = geometry.buffer(ca.CLEARANCE, quad_segs=16)
        hits = obs.hits(keep, obj['layers'], obj['net'], hole_keep)
        if accepted:
            hits += Witnesses(accepted).hits(keep, obj['layers'], obj['net'], hole_keep)
        contacts = []
        for target in [pad] + ([byid[obj['face_target_id']]] if obj['kind'] == 'segment' else []):
            target_copper = ca.copper(target)
            if target.get('drill_mm', 0) > 0:
                target_copper = target_copper.difference(Point(target['center_mm']).buffer(target['drill_mm']/2, quad_segs=16))
            area = geometry.intersection(target_copper).area
            contacts.append({'object_id': target['id'], 'layer': 'F.Cu', 'positive_area_mm2': area, 'object': target})
        intentional_drills = []
        if obj['kind'] == 'segment':
            row_plan = next(r for r in plan['targets'] if r['pad_id'] == pad['id'])
            allowed = set(row_plan.get('intentional_face_drill_ids', []))
            for hit in hits:
                target = hit['object']
                if hit['reason'] != 'drill' or target['id'] not in allowed:
                    continue
                need(target['kind'] == 'via' and target['net'] == obj['net'], 'invalid declared same-net face drill exception')
                ring = ca.copper(target).difference(Point(target['center_mm']).buffer(target['drill_mm']/2, quad_segs=16))
                area = geometry.intersection(ring).area
                if area > 1e-10:
                    intentional_drills.append(dict(hit, positive_annulus_contact_mm2=area, reason='intentional_same_net_annulus_contact'))
            exempt = {r['object']['id'] for r in intentional_drills}
            hits = [h for h in hits if not (h['reason'] == 'drill' and h['object']['id'] in exempt)]
        support, guard = [], []
        if obj['kind'] == 'via':
            ring = Point(obj['center_mm']).buffer(.3 + ca.SHEET_MARGIN, quad_segs=16)
            tree, polygons = sheets[obj['net']]
            box = shapely.box(point.x-ca.GUARD_HALF, point.y-ca.GUARD_HALF, point.x+ca.GUARD_HALF, point.y+ca.GUARD_HALF)
            support = [sheet_witness(planes['clipped_sheets'][obj['net']][int(i)], polygons[int(i)], box, sheet_seals)
                       for i in tree.query(ring, predicate='intersects') if polygons[int(i)].contains(ring)]
            for net, (tree, polygons) in sheets.items():
                if net == obj['net']:
                    continue
                for i in tree.query(ca.antipad(point), predicate='intersects'):
                    guard.append({'net': net, 'sheet': sheet_witness(planes['clipped_sheets'][net][int(i)], polygons[int(i)], box, sheet_seals)})
            severed = ca.severs(point, obj['net'], sheets, prior)
        else:
            severed = False
        reasons = []
        if hits: reasons.append('OBSTRUCTED')
        if not all(c['positive_area_mm2'] > 1e-10 for c in contacts): reasons.append('NO_POSITIVE_FACE_CONTACT')
        if obj['kind'] == 'via' and not support: reasons.append('NO_FULL_RING_IN_SAME_NET_SHEET')
        if severed: reasons.append('CUMULATIVE_SHEET_SEVERANCE')
        if obj['kind'] == 'via' and not Polygon(pad['polygon_mm']).contains(geometry): reasons.append('VIA_OUTSIDE_FIXED_LAND')
        row = {'proposal': obj, 'status': 'REJECTED' if reasons else 'LOCAL_GEOMETRY_LEGAL', 'reasons': reasons,
               'obstruction_witnesses': hits, 'intentional_drill_contact_witnesses': intentional_drills, 'contact_witnesses': contacts, 'ring_support_sheets': support,
               'severance_guard_witnesses': guard, 'prior_antipads_wkb': [{'net': n, 'wkb': shapely.to_wkb(g, hex=True)} for n, g in prior],
               'complete_path_credit': False}
        rows.append(row)
        if not reasons:
            accepted.append(obj)
            if obj['kind'] == 'via': prior.append((obj['net'], ca.antipad(Point(obj['center_mm']))))
    out = dict(source)
    out['objects'] = original + accepted
    need(out['objects'][:len(original)] == original, 'old copper changed')
    report = {'variant': variant, 'results': rows, 'proposed_count': len(proposals), 'added_count': len(accepted),
              'preservation': {'old_count': len(original), 'old_objects_sha256': digest(original), 'removed': [], 'changed': [], 'all_old_objects_identical': True},
              'limits': 'Source projection only. Full sheets must be re-clipped after additions, then complete fragment graph/census and finite paths rerun. Ring containment does not assert feed connection. No source bridge, P copper, process, native DRC or admission proof.',
              'native_calls': 0, 'complete_source_to_load_result': 'SOURCE_DEPENDENCY_NEGATIVE', 'accepted': False}
    return out, report

def main():
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    p = argparse.ArgumentParser()
    for key in ('source', 'planes', 'plan', 'contract', 'output'): p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    need(a.output.is_absolute() and not a.output.exists(), 'fresh absolute output directory required')
    paths = {'source': a.source, 'planes': a.planes, 'contract': a.contract,
             'plan': a.plan, 'method': Path(__file__), 'obstacles_method': Path(ca.__file__)}
    seals = {k: sha(path) for k, path in paths.items()}
    with a.plan.open() as stream:
        plan = json.load(stream)
    need(all(seals[k] == plan['input_sha256'][k] for k in ('source', 'planes', 'contract')), 'predeclared input seal changed; stop without search')
    values = []
    for key in ('source', 'planes', 'contract'):
        with paths[key].open() as stream:
            values.append(json.load(stream))
    source, planes, contract = values
    check_seals(paths, seals)
    need(source['board'] == planes['board'] == 'KA', 'KA-only pilot')
    dependency = source_dependency(contract, source)
    need(dependency['status'] == 'SOURCE_DEPENDENCY_NEGATIVE', 'source boundary changed; stop for exact review')
    a.output.mkdir(parents=True)
    dependency['input_sha256'] = seals
    write_json(a.output/'source-dependency.json', dependency)
    baseline = {'variant': 'baseline', 'preservation': {'old_count': len(source['objects']), 'old_objects_sha256': digest(source['objects']), 'removed': [], 'changed': [], 'all_old_objects_identical': True}, 'added_count': 0, 'native_calls': 0, 'accepted': False, 'complete_source_to_load_result': dependency['status']}
    baseline['input_sha256'] = seals
    write_json(a.output/'baseline-report.json', baseline)
    summaries = []
    for variant in VARIANTS:
        check_seals(paths, seals)
        out, report = assess(source, planes, plan, variant)
        check_seals(paths, seals)
        report['input_sha256'] = seals
        output = a.output/(variant+'-source.json')
        write_json(output, out, compact=True)
        report['output_sha256'] = sha(output)
        write_json(a.output/(variant+'-report.json'), report)
        summaries.append({'variant': variant, 'added_count': report['added_count'], 'proposed_count': report['proposed_count'], 'complete_path_credit': False})
    check_seals(paths, seals)
    write_json(a.output/'execution-seals.json', {'input_sha256': seals, 'inputs_before_after_equal': True, 'variants': summaries, 'native_calls': 0})
    print(json.dumps({'status': dependency['status'], 'variants': summaries, 'native_calls': 0, 'accepted': False}))

if __name__ == '__main__':
    main()
