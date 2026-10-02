"""Project the captured lag island into a bounded ideal RC fixture."""
from decimal import Decimal
import re
import math
from design.spec.modules.io_partition import AMP_MAPS

LIBRARY = 'zudo-osc-hole-field:'
POT_FACT_ID = 'fact-b504-resistance'
BOUNDARY = ('The captured lag resistors/capacitors and follower connections are projected. '
            'The held input and pre/post buffers are ideal voltage sources with unlimited rails; '
            'the three 100 kohm output loads are fixture loads isolated by ideal post buffers. '
            'LF398 acquisition/hold, trigger logic, the physical precision-output cell, '
            'actual output/indicator loading, pot tolerance/taper/contact, capacitor tolerance/leakage and amplifier limits '
            'are excluded. The fast endpoint uses a 1 milliohm numerical rheostat, '
            'compared with the nominal zero-ohm endpoint. Positions are nominal resistance '
            'fractions, not measured knob angles.')


def positive_value(value, unit):
    pattern = r'([+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*([kMmunpµ]?)\s*' + re.escape(unit)
    m = re.fullmatch(pattern, value)
    if not m:
        raise ValueError(f'unsupported model {unit} value: {value!r}')
    factor = {'': 1, 'k': 1000, 'M': 1000000, 'm': Decimal('.001'),
              'u': Decimal('.000001'), 'µ': Decimal('.000001'),
              'n': Decimal('1e-9'), 'p': Decimal('1e-12')}[m[2]]
    result = Decimal(m[1]) * factor
    if not result.is_finite() or result <= 0 or not math.isfinite(float(result)) or float(result) <= 0:
        raise ValueError('model value must be positive and finite')
    return result


def pot_nominal(facts):
    selected = [f for f in facts['facts'] if f['fact_id'] == POT_FACT_ID]
    if len(selected) != 1:
        raise ValueError('expected one B504 nominal resistance fact')
    f = selected[0]
    expected = {'record_id': 'rec-b504', 'source_id': 'src-b504-resistance', 'unit': 'ohm',
                'provenance': 'PRIMARY-SPEC', 'verdict': 'PASS - primary-source confirmed'}
    if any(f.get(k) != v for k, v in expected.items()) or type(f['value']) not in (int, float):
        raise ValueError('B504 nominal resistance evidence changed')
    value = Decimal(str(f['value']))
    if not value.is_finite() or value <= 0 or not f.get('conditions'):
        raise ValueError('invalid B504 nominal resistance')
    return value, {k: f[k] for k in ('fact_id', 'record_id', 'source_id', 'value', 'unit', 'conditions')}


def model_contract(parts, facts):
    if len({p.key for p in parts}) != len(parts):
        raise ValueError('lag model duplicate part identities')
    checked = {}

    def one(role, amplifier=False):
        found = [p for p in parts if p.attributes.get('Role') == role]
        if amplifier:
            power = [p for p in found if p.unit == 5]
            for p in power:
                if (p.dnp or p.prefix != 'U' or p.symbol != LIBRARY + 'OPA4197IPWR' or
                        p.pins != {'4': '+12V', '11': '-12V'}):
                    raise ValueError('lag amplifier power identity changed')
            found = [p for p in found if p.unit != 5]
        if len(found) != 1 or found[0].dnp:
            raise ValueError(f'lag model requires one fitted {role}')
        checked[role] = found[0]
        return found[0]

    def amp(role):
        p = one(role, True)
        if p.prefix != 'U' or p.symbol != LIBRARY + 'OPA4197IPWR' or p.unit not in (1, 2, 3, 4):
            raise ValueError('lag model amplifier identity changed')
        out, minus, plus = AMP_MAPS[p.unit - 1]
        if set(p.pins) != {out, minus, plus} or p.pins[out] != p.pins[minus]:
            raise ValueError('lag model requires unity follower feedback')
        return p.pins[plus], p.pins[out]

    held, pre = amp('slew_island:PRE')
    storage, output = amp('slew_island:POST')
    pot = one('slew_island:RV')
    if (pot.prefix != 'RV' or pot.unit != 0 or pot.symbol != LIBRARY + 'PTV09A-4020F-B504' or
            pot.value != 'PTV09A-4020F-B504' or set(pot.pins) != {'1', '2', '3', '4', '5'} or
            pot.pins['2'] != storage or pot.pins['3'] != storage or
            pot.pins['4'] is not None or pot.pins['5'] is not None):
        raise ValueError('lag model B504 rheostat identity/strap changed')
    pot_in = pot.pins['1']
    nodes = (held, pre, pot_in, storage, output, 'AGND')
    if (held != 'RAW_HELD' or output != 'SLEW_BUFFERED' or
            any(not isinstance(n, str) or not n for n in nodes) or len(set(nodes)) != len(nodes) or
            any(n in ('+12V', '-12V', '+5V') for n in nodes)):
        raise ValueError('lag model boundary or private nodes alias')

    def passive(role, kind, symbol, terminals, unit):
        p = one(role)
        if (p.prefix != kind or p.unit != 0 or p.symbol != LIBRARY + symbol or
                set(p.pins) != {'1', '2'} or set(p.pins.values()) != set(terminals)):
            raise ValueError(f'lag model passive identity/connectivity changed: {role}')
        return positive_value(p.value, unit)

    minimum = passive('slew_island:R_MIN', 'R', 'RC0603FR-07100KL', (pre, pot_in), 'Ω')
    caps = [passive(f'slew_island:C{i}', 'C', '1206CG104J500NT', (storage, 'AGND'), 'F') for i in range(1, 6)]
    nominal, evidence = pot_nominal(facts)
    # RAW_HELD and SLEW_BUFFERED are explicit ideal-input/output boundaries.
    # Additional fitted branches on internal lag nodes cannot be omitted.
    internal = {pre, pot_in, storage}
    allowed = {p.key for p in checked.values()}
    for p in parts:
        if not p.dnp and p.key not in allowed and internal.intersection(p.pins.values()):
            raise ValueError(f'unprojected internal lag connection: {p.key}')
    values = [float(minimum), float(nominal), float(sum(caps))]
    if any(not math.isfinite(x) or x <= 0 for x in values):
        raise ValueError('lag model values exceed finite numerical range')
    return {'r_min_ohm': values[0], 'r_pot_nominal_ohm': values[1],
            'c_lag_F': values[2], 'pot_nominal_evidence': evidence,
            'included_roles': list(checked), 'source_parts': [
                {'role': role, 'key': p.key, 'symbol': p.symbol, 'unit': p.unit,
                 'value': p.value, 'pins': dict(p.pins)} for role, p in checked.items()],
            'scope': BOUNDARY}
