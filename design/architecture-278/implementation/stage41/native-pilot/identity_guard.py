"""Fail closed on retained copper, pad and zone net-identity changes.

No pcbnew dependency. Duplicate UUIDs are retained as occurrences; copper
identity includes its complete raw geometry with only the net value removed.
This check supplements, never replaces, native DRC and connectivity gates.
"""
from collections import Counter
from pathlib import Path
from decimal import Decimal
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


LOCAL_SUPPLY_RETIREMENTS = {
    'ad4076c4-6993-563e-b756-f16bade968a8': '-12V',
    'd2685cd1-1b40-5f7b-812a-95ff8f967dee': '-12V',
    'b6a3e08a-344c-56dd-8210-3445bca58110': '-12V',
    'a7cc00f2-c575-500f-a42b-35d1ad78df1b': '+12V',
    'f442ae45-59e3-5ef8-a34a-b31090e70cfe': '+12V',
}


def retirement_rows(receipt):
    local = receipt.get('retired_local_supply_copper', [])
    if local and (len(local) != 5 or {r['uuid']: r['net'] for r in local} != LOCAL_SUPPLY_RETIREMENTS):
        raise ValueError('local supply retirement outside reviewed five objects')
    return receipt['retired_private_copper'] + local


def bound_retirements(receipt, baseline_raw):
    rows = retirement_rows(receipt)
    by_hash = {}
    for index, (a, b) in enumerate(top_level_spans(baseline_raw)):
        raw = baseline_raw[a:b]
        if kind(raw) in ('segment', 'via'):
            by_hash.setdefault(digest(raw), []).append((index, kind(raw), value(raw, 'uuid'), value(raw, 'net')))
    if len({r['sha256'] for r in rows}) != len(rows):
        raise ValueError('duplicate retirement hash')
    for row in rows:
        if by_hash.get(row['sha256']) != [(row['index'], row['kind'], row['uuid'], row['net'])]:
            raise ValueError('retirement hash does not bind exact baseline occurrence metadata')
    return rows


def kind(raw):
    match = re.match(r'\((\w+)(?:\s|\))', raw)
    if not match:
        raise ValueError('invalid object')
    return match[1]


def direct(raw):
    return [raw[a:b] for a, b in top_level_spans(raw)]


def value(raw, name, required=True):
    rows = [p for p in direct(raw) if kind(p) == name]
    if len(rows) > 1 or (required and len(rows) != 1):
        raise ValueError('missing/duplicate ' + name)
    if not rows:
        return ''
    match = re.fullmatch(r'\(' + name + r'\s+"([^"\\]*)"\s*\)', rows[0])
    if not match:
        raise ValueError('unsupported ' + name + ' syntax')
    return match[1]


def copper_contract(raw):
    """Integer-nanometre geometry for comparison to the native in-memory API."""
    fields = {kind(p): p for p in direct(raw)}
    def nums(name):
        tokens = fields[name][1:-1].split()[1:]
        return tuple(int(Decimal(t) * 1000000) for t in tokens)
    k = kind(raw)
    if k == 'segment':
        shape = (nums('start'), nums('end'), nums('width'), value(raw, 'layer'))
    elif k == 'via':
        layers = tuple(re.findall(r'"([^"\\]*)"', fields['layers']))
        shape = (nums('at'), nums('size'), nums('drill'), layers)
    else:
        raise ValueError('native pilot contract supports segments/vias only')
    return (k, value(raw, 'uuid'), shape, value(raw, 'net'))


def inventory(text):
    copper = Counter()
    native_contract = Counter()
    raw_copper = {}
    pads = Counter()
    zones = Counter()
    rules = Counter()
    refs = set()
    footprints = {}
    other_objects = Counter()
    net_names = set()
    for a, b in top_level_spans(text):
        raw = text[a:b]
        k = kind(raw)
        if k in ('segment', 'via', 'arc'):
            uid, net = value(raw, 'uuid'), value(raw, 'net')
            fields = direct(raw)
            geometry = '\n'.join(p for p in fields if kind(p) != 'net')
            key = (k, uid, digest(geometry), net)
            copper[key] += 1
            native_contract[copper_contract(raw)] += 1
            raw_copper.setdefault(digest(raw), []).append(key)
            net_names.add(net)
        elif k == 'footprint':
            uid = value(raw, 'uuid')
            reference = re.findall(r'\(property\s+"Reference"\s+"([^"\\]*)"', raw)
            if len(reference) != 1 or reference[0] in refs:
                raise ValueError('missing/duplicate reference')
            refs.add(reference[0])
            footprints[reference[0]] = digest(raw)
            for p in direct(raw):
                if kind(p) != 'pad':
                    continue
                pin = re.match(r'\(pad\s+"([^"\\]*)"', p)
                if not pin:
                    raise ValueError('unsupported pad number')
                net = value(p, 'net', False)
                pads[(uid, reference[0], value(p, 'uuid'), pin[1], net)] += 1
                if net:
                    net_names.add(net)
        elif k == 'zone':
            fields = direct(raw)
            net = value(raw, 'net', False)
            definition = '\n'.join(p for p in fields if kind(p) not in ('filled_polygon', 'filled_areas_thickness'))
            zones[(value(raw, 'uuid'), net, digest(definition))] += 1
            if any(kind(p) == 'keepout' for p in fields):
                rules[digest(raw)] += 1
            if net:
                net_names.add(net)
        else:
            other_objects[digest(raw)] += 1
    return dict(footprints=footprints, other_objects=other_objects, copper=copper, native_contract=native_contract, raw_copper=raw_copper, pads=pads, zones=zones,
                rules=rules, refs=refs, net_names=net_names)


def compare(before, after, retired_hashes=(), allowed_new=()):
    """Only exact baseline raw-hash retirements and explicit new copper accepted.

    allowed_new consists of complete copper identity tuples from the reviewed
    proposal. No mere net/UUID allowlist can conceal a changed existing object.
    """
    expected = before['copper'].copy()
    for h, count in Counter(retired_hashes).items():
        keys = before['raw_copper'].get(h, [])
        if len(keys) != count:
            raise ValueError('retirement must identify exact baseline occurrences')
        for key in keys:
            expected[key] -= 1
    expected = +expected
    additions = Counter(tuple(row) for row in allowed_new)
    old_uuids = {key[1] for key in before['copper']}
    if any(key[1] in old_uuids for key in additions):
        raise ValueError('new copper reuses baseline UUID')
    if len({key[1] for key in additions}) != sum(additions.values()):
        raise ValueError('new copper UUID collision')
    if any(key[3] not in before['net_names'] for key in additions):
        raise ValueError('new net name')
    expected.update(additions)
    checks = {
        'complete_copper_object_net_multiset': expected == after['copper'],
        'complete_pad_identity_net_multiset': before['pads'] == after['pads'],
        'zone_definitions_and_nets': before['zones'] == after['zones'],
        'rule_area_bytes': before['rules'] == after['rules'],
        'reference_set': before['refs'] == after['refs'],
        'other_board_objects': before['other_objects'] == after['other_objects'],
        'no_new_net_names': not (after['net_names'] - before['net_names']),
    }
    return {'accepted': all(checks.values()), 'checks': checks,
            'missing_copper': [list(k) + [n] for k, n in sorted((expected - after['copper']).items())],
            'unexpected_copper': [list(k) + [n] for k, n in sorted((after['copper'] - expected).items())]}


def structure_matches(before, after, prepared_footprints):
    """Routing must preserve every footprint, including explicitly prepared poses."""
    if not set(prepared_footprints) <= before['footprints'].keys():
        raise ValueError('prepared footprint absent from baseline')
    expected = dict(before['footprints'])
    expected.update(prepared_footprints)
    return expected == after['footprints'] and before['other_objects'] == after['other_objects']
