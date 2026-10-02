"""Permute complete K/P header pairs among existing identical physical sites.

This preserves occupied geometry and pin maps, not routing or electrical receipts.
"""
import copy
import hashlib
import json
from collections import Counter

GEOMETRY = ('center_mm', 'footprint_origin_mm', 'rotation_deg',
            'kicad_orientation_deg', 'side', 'land_courtyard_mm',
            'native_cached_courtyard_envelope_mm')
IDENTITY = ('board', 'header_mpn', 'housing_mpn', 'contact_mpn', 'contacts')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def baseline_digest(headers):
    return digest(sorted((h for h in headers if h['id'].startswith('K-P-')),
                         key=lambda h: h['id']))


def reassign(headers, apertures, proposal):
    if type(proposal.get('schema_version')) is not int or proposal['schema_version'] != 1:
        raise ValueError('Unsupported connector locality proposal')
    if baseline_digest(headers) != proposal['baseline_headers_sha256']:
        raise ValueError('Connector locality baseline changed')
    old = {h['id']: h for h in headers}
    if len(old) != len(headers):
        raise ValueError('Duplicate header identity')
    pairs = {h['id'][:-2] for h in headers
             if h['board'] == 'P' and h['id'].startswith('K-P-')}
    mapping = proposal['destination_pair_site']
    if (len(pairs) != proposal['expected_pair_count'] or set(mapping) != pairs or
            set(mapping.values()) != pairs or len(set(mapping.values())) != len(mapping)):
        raise ValueError('Complete bijective K/P pair assignment required')
    expected = {p+'-'+b for p in pairs for b in ('K', 'P')}
    if {h['id'] for h in headers if h['id'].startswith('K-P-')} != expected:
        raise ValueError('Each source pair must contain exactly K and P')
    old_apertures = {a['header_id']: a for a in apertures}
    if len(old_apertures) != len(apertures) or not {p+'-K' for p in pairs} <= old_apertures.keys():
        raise ValueError('Each K header needs its original service aperture')
    result = copy.deepcopy(headers)
    result_apertures = copy.deepcopy(apertures)
    for row in result:
        if row['id'] not in expected:
            continue
        pair, board = row['id'][:-2], row['board']
        source = old[mapping[pair]+'-'+board]
        if (any(row[k] != source[k] for k in IDENTITY) or row['contacts'] != 3 or
                row['header_mpn'] != 'BM03B-GHS-TBT(LF)(SN)' or
                row['housing_mpn'] != 'GHR-03V-S' or row['contact_mpn'] != 'SSHL-002T-P0.2' or
                row['pin_map'].get('2') != 'AGND'):
            raise ValueError('Only identical exact GH3 sites with central ground may be permuted')
        if old[pair+'-P']['center_mm'] != old[pair+'-K']['center_mm']:
            raise ValueError('Paired source endpoints must share their XY site')
        for key in GEOMETRY:
            row[key] = copy.deepcopy(source[key])
    for index, row in enumerate(result_apertures):
        if row['header_id'] in expected:
            hid = row['header_id']
            result_apertures[index] = copy.deepcopy(old_apertures[mapping[hid[:-2]]+'-K'])
            result_apertures[index]['header_id'] = hid
    for board in ('K', 'P'):
        signature = lambda rows: Counter(digest({k:h[k] for k in (*GEOMETRY,*IDENTITY)})
                                         for h in rows if h['board'] == board)
        if signature(headers) != signature(result):
            raise ValueError('Occupied header geometry changed')
    aperture_geometry = lambda rows: Counter(digest({k:v for k,v in a.items() if k!='header_id'}) for a in rows)
    if aperture_geometry(apertures) != aperture_geometry(result_apertures):
        raise ValueError('Occupied service aperture geometry changed')
    for row in result:
        if {k:v for k,v in row.items() if k not in GEOMETRY} != {k:v for k,v in old[row['id']].items() if k not in GEOMETRY}:
            raise ValueError('Header pin map or non-geometric identity changed')
    return result, result_apertures, {
        'status': 'SOURCE SITE PERMUTATION ONLY; native routing/current/physical acceptance required',
        'proposal_sha256': digest(proposal), 'pair_count': len(pairs),
        'moved_pairs': sum(a != b for a,b in mapping.items()),
        'occupied_header_geometry': 'UNCHANGED', 'occupied_service_aperture_geometry': 'UNCHANGED',
        'pin_maps_and_exact_identities': 'UNCHANGED',
        'scope': 'Both K/P endpoints move together; other headers remain fixed. Previous routed boards and electrical receipts are not rebound.'}


def prove_partition_transition(old, new, proposal):
    """Compare the entire partition after only the declared pair permutation."""
    raw_fields = {'id', 'board', 'header_mpn', 'housing_mpn', 'contact_mpn',
                  'contacts', 'pin_map', 'status', *GEOMETRY}
    raw_headers = [{k:v for k,v in h.items() if k in raw_fields}
                   for h in old['connectors']]
    if baseline_digest(raw_headers) != proposal['baseline_headers_sha256']:
        raise ValueError('Partition does not match the declared raw header baseline')
    bound = {**proposal, 'baseline_headers_sha256':baseline_digest(old['connectors'])}
    headers, apertures, _ = reassign(old['connectors'], old['K_service_apertures'], bound)
    expected = copy.deepcopy(old)
    expected['connectors'], expected['K_service_apertures'] = headers, apertures
    if expected != new:
        raise ValueError('Partition changed beyond the declared K/P connector permutation')
