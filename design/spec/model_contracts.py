"""Fail-closed projections of captured circuits into bounded SPICE fixtures.

These contracts describe the evaluated subgraphs, not complete circuit models.
Values absent from an exact passive identity remain unresolved sourcing gates.
"""
import hashlib
import json
import math
from design.spec.cells import _builder as source
from design.spec.modules.io_partition import AMP_MAPS
from design.spec.modules.sample_hold_model_contract import positive_value

PRECISION_SCOPE = ('One OPA4197 model core and the complete five-part precision-output cell; '
                   'ideal +/-12 V supplies and +/-5 V input. Load and cable capacitance are fixture '
                   'elements. Package coupling, tolerance, temperature, PCB/cable parasitics, '
                   'fault protection and physical stability are not modeled.')
MIX4_SCOPE = ('Four coherent ideal inputs replace the complete input/attenuverter chains at '
              '1_GAIN through 4_GAIN. Ideal +/-5 V sources replace the reference generator. '
              'The commanded bias current replaces the complete clamp/current servo at CURRENT_SOURCE; '
              'the captured current-sense resistance defines only its nominal requested slope. '
              'Captured summer and TIA connections use unbounded ideal E sources, not OPA4196 models. '
              'The OTA divider, offset pot, IABC series resistor, OTA1 and TIA feedback are included. '
              'A fixture 100k load at SUM_POSTVCA replaces the general-output cell and indicator; '
              'the clip monitor at SUM_PRELEVEL, unused OTA section and package supply current are excluded. '
              'No complete servo, opamp headroom, protection, tolerance, temperature or hardware claim.')


def fingerprint(projection):
    return hashlib.sha256(json.dumps(projection, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require_current_builder():
    """Do not evaluate old imported JSON while the on-disk source has changed."""
    standard = json.loads((source.ROOT / 'design/standard/electrical-standard.json').read_text())
    shortlist = {p['id']: p for p in json.loads((source.ROOT / 'design/standard/parts-shortlist.json').read_text())['parts']}
    if standard != source.STANDARD or shortlist != source.SHORTLIST:
        raise ValueError('model source changed after import; start a fresh process')


def precision_contract(cell, roles, shortlist, aliases):
    expected = {
        'A': {'IN+': 'SIGNAL', 'IN-': 'FB', 'OUT': 'DRIVE', 'V+': '+12V', 'V-': '-12V'},
        'R_ISO_A': {'1': 'DRIVE', '2': 'ISO_MID'},
        'R_ISO_B': {'1': 'ISO_MID', '2': 'JACK'},
        'R_FB': {'1': 'JACK', '2': 'FB'}, 'C_FAST': {'1': 'DRIVE', '2': 'FB'},
    }
    rows = cell['parts']
    if len(rows) != len(expected) or {p['ref'] for p in rows} != set(expected):
        raise ValueError('precision model requires the complete five-part cell with unique references')
    by_ref = {p['ref']: p for p in rows}
    for ref, pins in expected.items():
        if by_ref[ref]['terminals'] != pins or by_ref[ref].get('dnp', False):
            raise ValueError('precision model connectivity/population changed: ' + ref)
    amp = by_ref['A']
    if amp.get('opamp_role') != 'precision' or 'part_id' in amp:
        raise ValueError('precision model amplifier role changed')
    selected = shortlist[roles['precision']['part_id']]
    if selected['mpn'] != 'OPA4197IPWR' or selected['manufacturer'] != 'Texas Instruments':
        raise ValueError('TI OPAx197 model requires the captured OPA4197IPWR selection')
    if aliases != {'IN+': '3', 'IN-': '2', 'OUT': '1', 'V+': '4', 'V-': '11'}:
        raise ValueError('precision amplifier physical pin mapping changed')
    values = {}
    for ref, part_id, unit in [('R_ISO_A', 'r_power', 'ohm'), ('R_ISO_B', 'r_power', 'ohm'),
                               ('R_FB', 'r_feedback', 'ohm'), ('C_FAST', 'c_feedback', 'F')]:
        p = by_ref[ref]
        value = p.get('value')
        if (p.get('part_id') != part_id or p.get('unit') != unit or 'opamp_role' in p or
                type(value) not in (int, float) or not math.isfinite(value) or value <= 0):
            raise ValueError('precision passive type/unit/value changed: ' + ref)
        values[ref] = value
    if values['R_ISO_A'] != 499 or values['R_ISO_B'] != 499:
        raise ValueError('precision deck requires two captured 499 ohm isolation resistors')
    return {'amplifier_mpn': selected['mpn'], 'amplifier_pin_aliases': dict(aliases),
            'values': values, 'source_parts': rows, 'scope': PRECISION_SCOPE}


def compiled_precision_contract(parts, projection):
    if (len(parts) != 9 or len({p.key for p in parts}) != 9 or
            len({(p.prefix,p.ordinal,p.unit) for p in parts}) != 9 or
            any(p.panel_ref or p.panel_refs for p in parts)):
        raise ValueError('precision compiled cell must have nine unique units')
    expected = {p['ref']: p for p in projection['source_parts']}
    groups = {}
    for p in parts:
        full_role = p.attributes.get('Role', '')
        if not full_role.startswith('precision_output:'):
            raise ValueError('precision compiled role namespace changed')
        role = full_role.removeprefix('precision_output:')
        if role not in expected or p.dnp:
            raise ValueError('precision compiled role/population changed')
        groups.setdefault(role, []).append(p)
    amp = groups['A']
    if len(amp) != 5 or {p.unit for p in amp} != set(range(1, 6)):
        raise ValueError('precision compiled amplifier units changed')
    if len({p.key.rsplit('.', 1)[0] for p in amp}) != 1 or len({p.ordinal for p in amp}) != 1:
        raise ValueError('precision amplifier units must share one physical package')
    unused_nodes = set()
    for p in amp:
        if p.prefix != 'U' or p.symbol != 'zudo-osc-hole-field:OPA4197IPWR' or p.attributes.get('MPN') != 'OPA4197IPWR':
            raise ValueError('precision compiled amplifier identity changed')
        if p.unit == 1:
            pins = {'1': 'DRIVE', '2': 'FB', '3': 'SIGNAL'}
        elif p.unit == 5:
            pins = {'4': '+12V', '11': '-12V'}
        else:
            out, minus, plus = AMP_MAPS[p.unit-1]
            if (set(p.pins) != {out, minus, plus} or p.pins[out] != p.pins[minus] or
                    p.pins[plus] != 'AGND' or not p.pins[out] or
                    p.pins[out] in {'DRIVE','FB','SIGNAL','ISO_MID','JACK','AGND','+12V','-12V'}):
                raise ValueError('precision compiled unused amplifier termination changed')
            if p.pins[out] in unused_nodes:
                raise ValueError('precision unused amplifier outputs must not be tied together')
            unused_nodes.add(p.pins[out])
            continue
        if p.pins != pins:
            raise ValueError('precision compiled amplifier pins changed')
    for ref, symbol, prefix, unit in [
        ('R_ISO_A', 'RC1210FR-07499RL', 'R', 'Ω'), ('R_ISO_B', 'RC1210FR-07499RL', 'R', 'Ω'),
        ('R_FB', 'RC0603FR-07100RL', 'R', 'Ω'), ('C_FAST', 'C0603C102J5GACTU', 'C', 'F')]:
        rows = groups[ref]
        if len(rows) != 1:
            raise ValueError('precision compiled passive multiplicity changed')
        p = rows[0]
        representative = {'R_ISO_A':499, 'R_ISO_B':499, 'R_FB':100, 'C_FAST':1e-9}[ref]
        expected_mpn = symbol if projection['values'][ref] == representative else ''
        if p.attributes.get('MPN') != expected_mpn:
            raise ValueError('precision exact-value identity handling changed: ' + ref)
        if (p.prefix != prefix or p.unit != 0 or p.symbol != 'zudo-osc-hole-field:' + symbol or
                p.pins != expected[ref]['terminals'] or
                float(positive_value(p.value, unit)) != projection['values'][ref]):
            raise ValueError('precision compiled passive primitive/connectivity/value changed: ' + ref)
    return [{'role': p.attributes['Role'], 'symbol': p.symbol, 'unit': p.unit, 'prefix': p.prefix,
             'value': p.value, 'pins': p.pins, 'mpn': p.attributes.get('MPN')} for p in parts]


def current_precision_contract():
    require_current_builder()
    projection = precision_contract(source.CELLS['precision_output'], source.STANDARD['roles'], source.SHORTLIST, source.AMP)
    nets = {n: n for n in ('SIGNAL','FB','DRIVE','ISO_MID','JACK')}
    parts = source.cell_parts('precision_output', 'J:H1.OUT', nets)
    projection['compiled_parts'] = compiled_precision_contract(parts, projection)
    return json.loads(json.dumps(projection, allow_nan=False))


def mix4_contract(parts):
    if len({p.key for p in parts}) != len(parts):
        raise ValueError('MIX4 duplicate part identity')
    checked = {}
    def one(role):
        matches = [p for p in parts if p.attributes.get('Role') == 'mix4_vca:' + role]
        if len(matches) != 1 or matches[0].dnp:
            raise ValueError('MIX4 requires one fitted ' + role)
        checked[matches[0].key] = matches[0]
        return matches[0]
    def resistor(role, value, pins):
        p = one('R_' + role)
        if (p.prefix != 'R' or p.unit != 0 or p.symbol != 'zudo-osc-hole-field:RT0603BRD07100KL' or
                p.pins != pins or positive_value(p.value, 'Ω') != value):
            raise ValueError('MIX4 resistor differs from modeled source: ' + role)
    def amplifier(role, plus, minus, out):
        p = one(role)
        if (p.prefix != 'U' or p.symbol != 'zudo-osc-hole-field:OPA4196IDR' or
                p.attributes.get('MPN') != 'OPA4196IDR' or p.unit not in range(1, 5)):
            raise ValueError('MIX4 idealized amplifier identity changed: ' + role)
        op, mn, pl = AMP_MAPS[p.unit - 1]
        if p.pins != {op: out, mn: minus, pl: plus}:
            raise ValueError('MIX4 amplifier connectivity changed: ' + role)
        supply = [q for q in parts if q.key == p.key.rsplit('.', 1)[0] + '.5']
        if (len(supply) != 1 or supply[0].dnp or supply[0].symbol != p.symbol or
                supply[0].prefix != p.prefix or supply[0].ordinal != p.ordinal or
                supply[0].pins != {'4': '+12V', '11': '-12V'}):
            raise ValueError('MIX4 amplifier supplies changed: ' + role)
        checked[supply[0].key] = supply[0]
    amplifier('SUMMER', 'AGND', 'SUM_NODE', 'SUM_PRELEVEL')
    amplifier('CURRENT_TO_VOLTAGE', 'AGND', 'OTA_CURRENT', 'SUM_POSTVCA')
    for n in range(1, 5):
        resistor('SUM_IN_' + str(n), 100000, {'1': str(n) + '_GAIN', '2': 'SUM_NODE'})
    for role, value, a, b in [
        ('SUM_FEEDBACK', 50000, 'SUM_PRELEVEL', 'SUM_NODE'),
        ('CURRENT_SENSE', 10000, 'REF5', 'EMITTER'),
        ('IABC_LIMIT', 10000, 'CURRENT_SOURCE', 'IABC1'),
        ('OTA_ATTEN_TOP', 100000, 'SUM_PRELEVEL', 'OTA_SIGNAL'),
        ('OTA_ATTEN_BOTTOM', 100, 'OTA_SIGNAL', 'AGND'),
        ('OFFSET_FEED', 1000000, 'OFFSET_W', 'OTA_OFFSET'),
        ('OFFSET_RETURN', 1000, 'OTA_OFFSET', 'AGND'),
        ('TIA_FIXED', 100000, 'SUM_POSTVCA', 'TIA_TRIM')]:
        resistor(role, value, {'1': a, '2': b})
    for role, pins in [('FEEDTHROUGH', {'1': 'REFN5', '2': 'OFFSET_W', '3': 'REF5'}),
                       ('TIA_CAL', {'1': 'TIA_TRIM', '2': 'OTA_CURRENT', '3': 'OTA_CURRENT'})]:
        p = one(role)
        if (p.prefix != 'RV' or p.unit != 0 or p.symbol != 'zudo-osc-hole-field:TC33X-2-103E' or
                p.attributes.get('MPN') != 'TC33X-2-103E' or p.pins != pins or positive_value(p.value, 'Ω') != 10000):
            raise ValueError('MIX4 trim range/wiring changed: ' + role)
    ota = [p for p in parts if p.attributes.get('Role') == 'mix4_vca:VCA_OTA']
    pins = {}
    if len(ota) != 5 or {p.unit for p in ota} != set(range(1, 6)):
        raise ValueError('MIX4 requires all five units of one OTA package')
    if len({p.key.rsplit('.', 1)[0] for p in ota}) != 1 or len({p.ordinal for p in ota}) != 1:
        raise ValueError('MIX4 OTA units are not one package')
    for p in ota:
        if (p.dnp or p.prefix != 'U' or p.symbol != 'zudo-osc-hole-field:LM13700M_NOPB' or
                p.attributes.get('MPN') != 'LM13700M/NOPB' or set(pins).intersection(p.pins)):
            raise ValueError('MIX4 OTA identity/pin uniqueness changed')
        pins.update(p.pins)
        checked[p.key] = p
    expected = {'1': 'IABC1', '2': None, '3': 'OTA_SIGNAL', '4': 'OTA_OFFSET', '5': 'OTA_CURRENT',
                '6': '-12V', '7': 'AGND', '8': None, '9': None, '10': 'AGND', '11': '+12V',
                '12': None, '13': 'AGND', '14': 'AGND', '15': None, '16': 'IABC2'}
    if pins != expected:
        raise ValueError('MIX4 OTA pin map differs from single-OTA fixture')
    physical_units = {(p.prefix,p.ordinal,p.unit) for p in checked.values()}
    if (len(physical_units) != len(checked) or any(p.panel_ref or p.panel_refs for p in checked.values())):
        raise ValueError('MIX4 modeled physical reference/unit collision or override')
    internal = {'SUM_NODE', 'OTA_SIGNAL', 'OFFSET_W', 'OTA_OFFSET', 'OTA_CURRENT', 'TIA_TRIM', 'IABC1'}
    for p in parts:
        if not p.dnp and p.key not in checked and internal.intersection(p.pins.values()):
            raise ValueError('MIX4 unmodeled internal branch: ' + p.key)
    return {'scope': MIX4_SCOPE, 'source_parts': [
        {'key': p.key, 'role': p.attributes.get('Role'), 'symbol': p.symbol, 'unit': p.unit,
         'value': p.value, 'mpn': p.attributes.get('MPN'), 'pins': p.pins}
        for p in checked.values()]}


def current_mix4_contract():
    from design.spec.modules import mix4_vca
    require_current_builder()
    return mix4_contract(mix4_vca.family().parts)


def snapshot_sources():
    """Freeze local loaded producers and their JSON/symbol operands for this run.

The report binds the evaluated projection/decks. These bytes are a lifecycle
check only: unrelated project code is not mislabeled as modeled circuit scope.
"""
    import sys
    paths = {source.ROOT / 'design/standard/electrical-standard.json',
             source.ROOT / 'design/standard/parts-shortlist.json'}
    paths.update((source.ROOT / 'symbols/src').glob('*.kicad_sym'))
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            from pathlib import Path
            p = Path(filename).resolve()
            if p.suffix == '.py' and p.is_relative_to(source.ROOT) and p.is_file():
                paths.add(p)
    return {p: p.read_bytes() for p in paths}


def verify_snapshot(snapshot):
    for path, content in snapshot.items():
        if not path.is_file() or path.read_bytes() != content:
            raise ValueError('model source changed during run: ' + str(path))
