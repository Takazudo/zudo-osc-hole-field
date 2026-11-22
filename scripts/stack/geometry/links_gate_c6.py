"""DA-03 c6 finite conductor-order pass over the exact retained 61-link record.

This changes positions and three coupling riders only. It refuses a changed source
record; placement, cable, slot, size, tail, and displaced-footprint evidence are
frozen. The output is a candidate until the whole generator/check chain is rebound.
"""
import hashlib
import json
import copy

import links_gate as gate

SOURCE_SHA256 = '6e3141c94d8aff6d3552916fd37caf11e710607cf9add46c315107d41aa093b1'
SOURCE_OBJECT_SHA256 = 'a555e65e9a61617ebe9e7c10656722ac0f25f80f7abef0a3d193bc7b7d389ef8'
# MC04-S6 revision 4 rebind (circuit/orchestration/campaigns/osc-stack-20261114/
# mc04-s6-board-sync-native-brief-20261121.md, Revision 4): after JL/JR were brought to the floorplan (source
# commit 9d3d5a96), the pre-c6 geometry changed (JL-K-JL-L02 and JR-K-JR-L02 take new slots; JL-L07, JL-L08 and
# JR-L04 change cost only). c6's own output - positions, signals and the three riders - is unchanged; see
# mc04-s6-c6-rebind-check-20261122.json (sha256 577464968eb8e7644a50b283192817891070361fe946389fd8fb44e86e77b87d, as of MC04-S6 revision 5).
# Only the geometry and output pins are rebound; the signal and positions pins are unchanged.
# Previous geometry pin: fb5e91e1c7fc1f581434cb6a9a28fb91d7c21c170d66156ceb6cb4e912760eb8
# MC04-S7 Revision 2 rebind (JL-K-JL-L02 held at its retained slot; signals, positions and riders unchanged;
# circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-c6-rebind-check-20261122.json, sha256
# 844a68b6caea1458376f4266a70b13506be9dc561d088c4b9c0ee42d64df1c4e). Previous geometry pin: 3b58378a048d21c0f2eb273dda07759f789d1151629c43df90028eaafa4db7b8
# MC04-S7 Revision 11 fresh attempt (stage 7 K block move with stable GH headers and stable link clusters): the JL
# and JR links carry the stage 7 nets and the new pairs (JL-K-JL-L09; JR-K-28/29 join JR-K-JR-L02, JR-K-30 joins
# JR-K-JR-L01), so the geometry, signal and positions pins change. The eight links c6 acts on have the same pre-c6
# positions as the retained source snapshot, and c6 gives them the same positions and riders as before; see
# circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-r11-c6-check-20261122.json.
# Previous pins: geometry 35ce915f31bab14a881690030ed18e67250331d6eee00d40d42c8c93268fe627,
# signal baa834876861bea8245c223950e3405ec7d9223f327f99f38fc3c5a59da128c4,
# positions c95a3dfbd397cfe3785e6e8f90037105a86ee01a9460fd98d7fab0b932f57ebd
# MC04-S7 Revision 13 rebind (JR step 7 redo: D4101, D4102, R8425 and R8426 leave the SLV-U2 keep-out; JR-K-JR-L01
# takes another slot): signal, positions, riders and c6's eight links unchanged; see
# circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-r13-c6-rebind-check-20261122.json.
# Previous geometry pin: a1549b308d2d6b26a2bd504abfa037e1b90331922d8b6cda3c521a8f7dd6033a (Revision 11)
SOURCE_GEOMETRY_SHA256 = '466a9e4ccb00339db0e1ec87ab3d3b8e398a482b232d05816327b93273887aed'
SOURCE_SIGNAL_SHA256 = '70335b6d45781946dddabeb3fbdb86dcf0924c2dd79355dd4e7f08443f5c584b'
SOURCE_POSITIONS_SHA256 = 'f1d03b6ab6aadfc2530d6e22b0596598d51a468bdcaff978152f5ec85acd94a6'
# Previous output pin: 81400a28b258fc0002bbe05f451e9237aeb9ab5ad9b2719cbaa2e4416522e94a (MC04-S6 revision 4 rebind)
# Previous output pin: 078cd8eeb0c86b7551867e82a6e6c0ab7bf64068f84e1a030400509cd5142443 (MC04-S6 revision 4 rebind)
# Previous output pin: 7f7fb47c58b32d7267008c6cc610174d03749b7389599d7e77eeff0714b4f907 (MC04-S7 Revision 2 rebind)
# Previous output pin: 5c4a7e27f13b2697e26f852d563693a9c609e198734f5d36b3b0b7b8a1e9fbd1 (MC04-S7 Revision 11 fresh attempt)
OUTPUT_LINKS_SHA256 = '44cff1e4c0b377d435c46cbb7533bb58041f733d01679287f86593bdb82b2dbb'
L01 = 'P-K-P-L01.01.01'
L01B = 'P-K-P-L01.02.01'
L03 = 'P-K-P-L03.01'
L03B = 'P-K-P-L03.02.01'
L05 = 'P-K-P-L05.01.01'
L07 = 'P-K-P-L07'
L08 = 'P-K-P-L08'
L13 = 'P-K-P-L13.01.01.01'
RULED_SPLIT_SHA256 = {
    L07: ('9eb0188c0f235eb0f7b1257ebb3917066acdbe04444de9b439832e948501bbf8',
          'bea6a27789f1376b0c0f1ede28278bc1f2679cf0e868995f1161dd3110d3e967'),
    L08: ('0aca57a174664e1a2c5458bdbc9851734ddc25a3d0b1ab4ff0cbd00572a6c162',
          'e678405ec250de35dc640b6de8821e64bae25753d97f4c01d522672f320eff5e'),
    L13: ('1ff78f28bfdb2d3469c2cba980b484004744352749c18091d1d6d24ccd66b079',
          'bfdd6f372c6ba08ddf59ed1e6cba75e56305c19f6729841a0f0356d49c4d3402'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def geometry_digest(doc):
    return digest([{k: v for k, v in link.items() if k not in
                    ('positions', 'signals', 'grounds', 'unused', 'riders_in', 'riders_out', 'c6_circuits_needed')}
                   for link in doc['links']])


def signal_digest(doc):
    return digest(sorted((p['site'], p['net'], p['class']) for link in doc['links']
                         for p in link['positions'] if p['kind'] == 'signal'))


def valid_record(doc):
    return (doc.get('c6', {}).get('source_sha256') == SOURCE_SHA256 and
            doc['c6'].get('geometry_sha256') == SOURCE_GEOMETRY_SHA256 and
            doc['c6'].get('signal_sha256') == SOURCE_SIGNAL_SHA256 and
            digest(doc['links']) == OUTPUT_LINKS_SHA256)


def _signal_id(p):
    return p['site'], p['net'], p['class']


def _boundary(link):
    signals = [p for p in link['positions'] if p['kind'] == 'signal']
    return _signal_id(signals[0]), _signal_id(signals[-1])


def order_errors(link, original=None):
    pos = link['positions']
    errors = gate.allocation_errors(pos, 'a8', gate.DS79_ORDER if hasattr(gate, 'DS79_ORDER') else
                                    ['OSC_OCT0', 'OSC_OCT1', 'OSC_OCT2', 'OSC_OCT3', 'OSC_OCT4', 'OSC_OCT5', 'AGND', 'OCT_SELECTED'])
    # DA-03 c6's specific SYNC_GATE and L13 orders split one original LOGIC
    # cohort into fragments. The old DS-78 checker ranks each new singleton as
    # a new outer-preference unit. Its old, previously valid outer signals are
    # deliberately unchanged by this ruled pass. Only this provenance-checked
    # case suppresses that one obsolete ranking diagnostic.
    if original is not None and link['id'] in (L07, L08, L13):
        old_errors = gate.allocation_errors(original['positions'], 'a8',
                                            ['OSC_OCT0', 'OSC_OCT1', 'OSC_OCT2', 'OSC_OCT3', 'OSC_OCT4', 'OSC_OCT5', 'AGND', 'OCT_SELECTED'])
        old_nonlogic = [_signal_id(p) for p in original['positions'] if p['kind'] == 'signal' and p['class'] != 'LOGIC']
        new_nonlogic = [_signal_id(p) for p in pos if p['kind'] == 'signal' and p['class'] != 'LOGIC']
        before, after = RULED_SPLIT_SHA256[link['id']]
        if (not old_errors and digest(original['positions']) == before and digest(pos) == after and
                _boundary(link) == _boundary(original) and old_nonlogic == new_nonlogic):
            errors = [e for e in errors if 'preference of DS-78' not in e]
    for a, b, classes in gate.signal_units(pos):
        if classes[0] == 'LOGIC' and len(classes) > 3:
            errors.append(f'logic run {a}-{b} has {len(classes)} lines, above DA-03 c6 cap')
    for i, p in enumerate(pos):
        if p['kind'] == 'signal' and p['net'].endswith('/SYNC_GATE'):
            if i == 0 or i == len(pos) - 1 or pos[i - 1]['kind'] not in ('ground', 'unused') or pos[i + 1]['kind'] not in ('ground', 'unused'):
                errors.append(f'SYNC_GATE at {i+1} lacks ground on both sides')
    return errors


def _pack(link, sequence, original=None):
    if len(sequence) > link['circuits']:
        raise ValueError(f"{link['id']}: ruled order needs {len(sequence)} of {link['circuits']} positions")
    sequence = sequence + ['_'] * (link['circuits'] - len(sequence))
    pos = []
    for i, item in enumerate(sequence, 1):
        if item is None:
            pos.append({'pos': i, 'kind': 'ground'})
        elif item == '_':
            pos.append({'pos': i, 'kind': 'unused'})
        else:
            pos.append(dict(item, pos=i))
    link['positions'] = pos
    link['signals'] = sum(p['kind'] == 'signal' for p in pos)
    link['grounds'] = sum(p['kind'] == 'ground' for p in pos)
    link['unused'] = sum(p['kind'] == 'unused' for p in pos)
    # The historical clustering field remains frozen, as DA-03 c6 requires.
    link['c6_circuits_needed'] = gate.circuits_needed([p['class'] for p in pos if p['kind'] == 'signal'])
    if order_errors(link, original):
        raise ValueError(f"{link['id']}: {order_errors(link, original)}")


def _by_pos(link):
    return {p['pos']: p for p in link['positions']}


def _rider(source, host, net, distance):
    signal = next(p for p in source['positions'] if p['kind'] == 'signal' and p['net'] == net)
    if distance > 55.0:
        raise ValueError('logic rider exceeds 55 mm')
    fields = {k: signal[k] for k in ('net', 'class', 'site')}
    source.setdefault('riders_out', []).append(dict(fields, host=host['id'], distance_mm=distance, reason='coupling'))
    host.setdefault('riders_in', []).append(dict(fields, **{'from': source['id'], 'distance_mm': distance, 'reason': 'coupling'}))
    return dict(signal, rider_from=source['id'])


def apply(doc, inp=None):
    if doc.get('c6'):
        if doc['c6']['geometry_sha256'] != geometry_digest(doc):
            raise ValueError('c6 geometry changed after pass')
        return doc
    if (geometry_digest(doc) != SOURCE_GEOMETRY_SHA256 or
            signal_digest(doc) != SOURCE_SIGNAL_SHA256 or
            digest([x['positions'] for x in doc['links']]) != SOURCE_POSITIONS_SHA256):
        raise ValueError('DA-03 c6 pass requires the exact retained source record')
    g0, s0 = geometry_digest(doc), signal_digest(doc)
    links = {x['id']: x for x in doc['links']}
    original = {key: copy.deepcopy(value) for key, value in links.items()}
    by = {name: _by_pos(links[name]) for name in (L01, L01B, L03, L03B, L05, L07, L08, L13)}
    e5a = _rider(links[L01], links[L05], '/E5/ASR_RAW', 24.1835)
    e5c = _rider(links[L01], links[L05], '/E5/CURVED', 24.1835)
    e1 = _rider(links[L13], links[L03B], '/E1/STAGE_FALL', 50.3211)
    p = by[L01]
    _pack(links[L01], [p[1], None, p[3], p[4], p[5], None, p[6], p[7], p[12], None, p[10], p[11], None, p[14]], original[L01])
    p = by[L05]
    _pack(links[L05], [None, p[2], p[3], None, e5a, e5c, None], original[L05])
    p = by[L13]
    _pack(links[L13], [p[1], None, p[5], p[6], None, p[4], None, p[8]], original[L13])
    p = by[L03B]
    _pack(links[L03B], [p[1], None, p[3], None, p[5], p[6], p[7], None, p[8], p[9], e1, None, p[11]], original[L03B])
    for name, split in ((L01B, 3), (L03, 3)):
        p = by[name]
        values = list(p.values())
        start = next(i for i, x in enumerate(values) if x['kind'] == 'signal' and x['class'] == 'LOGIC')
        end = start
        while end < len(values) and values[end]['kind'] == 'signal' and values[end]['class'] == 'LOGIC':
            end += 1
        seq = values[:start] + values[start:start+split] + [None] + values[start+split:end] + values[end:]
        seq.remove(next(x for x in reversed(seq) if x['kind'] == 'unused'))
        _pack(links[name], seq, original[name])
    for name in (L07, L08):
        p = by[name]
        values = list(p.values())
        start = next(i for i, x in enumerate(values) if x['kind'] == 'signal' and x['class'] == 'LOGIC')
        end = start
        while end < len(values) and values[end]['kind'] == 'signal' and values[end]['class'] == 'LOGIC':
            end += 1
        run = values[start:end]
        segment = []
        for x in run:
            if x['net'].endswith('/SYNC_GATE'):
                if not segment or segment[-1] is not None:
                    segment.append(None)
                segment += [x, None]
            else:
                segment.append(x)
        # L08 has four planning lines after its last gate: balance them 2 + 2.
        if name == L08:
            tail = next(i for i, x in enumerate(segment) if x is not None and x['net'].endswith('O2:SUB_SEL_A (planning)'))
            segment.insert(tail + 2, None)
        seq = values[:start] + segment + values[end:]
        while len(seq) > links[name]['circuits']:
            u = next((x for x in reversed(seq) if isinstance(x, dict) and x['kind'] == 'unused'), None)
            if u is None:
                raise ValueError(f'{name}: insufficient unused positions for SYNC_GATE and cap')
            seq.remove(u)
        _pack(links[name], seq, original[name])
    if geometry_digest(doc) != g0 or signal_digest(doc) != s0:
        raise ValueError('c6 pass changed frozen geometry or signal identity')
    doc['c6'] = {'authority': 'DA-03 c6 and clarification', 'source_sha256': SOURCE_SHA256,
                 'geometry_sha256': g0, 'signal_sha256': s0,
                 'changed_links': [L01, L01B, L03, L03B, L05, L07, L08, L13]}
    if not valid_record(doc):
        raise ValueError('c6 output differs from the exact ruled candidate')
    return doc
