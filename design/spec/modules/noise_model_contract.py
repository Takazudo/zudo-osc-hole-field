"""Bind the fixed ideal noise-filter decks to their captured circuit subgraph."""
from design.spec.modules.io_partition import AMP_MAPS


def model_contract(parts):
    if len({p.key for p in parts}) != len(parts):
        raise ValueError('Noise capture has duplicate part identities')
    checked = {}

    def one(role):
        role = 'noise:' + role
        matches = [p for p in parts if p.attributes.get('Role') == role]
        if len(matches) != 1 or matches[0].dnp:
            raise ValueError(f'Noise model requires one fitted {role}')
        checked[role] = matches[0]
        return matches[0]

    def passive(role, value, a, b):
        p = one(role)
        kind = role[0]
        symbol = ('RT0603BRD07100KL' if kind == 'R' else
                  'GRM188R71H104KA93D' if value == '100 nF' else 'C0603C101J5GACTU')
        if p.prefix != kind or p.unit != 0 or p.symbol != 'zudo-osc-hole-field:' + symbol:
            raise ValueError(f'Noise model passive identity changed: {role}')
        if p.value != value or p.pins != {'1': a, '2': b}:
            raise ValueError(f'Noise model value/connectivity changed: {role}')

    def amp(role, plus, minus, out):
        p = one(role)
        if p.symbol != 'zudo-osc-hole-field:OPA4196IDR' or p.prefix != 'U' or p.unit not in (1, 2, 3, 4):
            raise ValueError(f'Noise model amplifier identity changed: {role}')
        output, negative, positive = AMP_MAPS[p.unit - 1]
        if p.pins != {output: out, negative: minus, positive: plus}:
            raise ValueError(f'Noise model amplifier connectivity changed: {role}')

    internal = set()
    for colour in ('WHITE', 'PINK'):
        start = 'WHITE_RAW' if colour == 'WHITE' else 'PINK_SOURCE'
        passive(f'R_{colour}_RECON', '1 kΩ', start, f'{colour}_LP')
        passive(f'C_{colour}_RECON', '10 nF', f'{colour}_LP', 'AGND')
        passive(f'C_{colour}_AC', '100 nF', f'{colour}_LP', f'{colour}_AC')
        passive(f'R_{colour}_BLEED', '100 kΩ', f'{colour}_AC', 'AGND')
        amp(f'{colour}_INPUT', f'{colour}_AC', f'{colour}_SIGNAL', f'{colour}_SIGNAL')
        internal.update((f'{colour}_LP', f'{colour}_AC'))
    amp('PINK_SOURCE', 'PINK_RAW', 'PINK_SOURCE', 'PINK_SOURCE')
    amp('BROWN_LEAK', 'AGND', 'BROWN_SUM', 'BROWN_SHAPE')
    passive('R_BROWN_IN', '100 kΩ', 'WHITE_SIGNAL', 'BROWN_SUM')
    passive('R_BROWN_LEAK', '1 MΩ', 'BROWN_SHAPE', 'BROWN_SUM')
    passive('C_BROWN_LEAK', '10 nF', 'BROWN_SHAPE', 'BROWN_SUM')
    passive('C_BLUE_INPUT', '100 pF', 'PINK_SIGNAL', 'BLUE_SERIES')
    passive('R_BLUE_INPUT', '100 kΩ', 'BLUE_SERIES', 'BLUE_SUM')
    amp('BLUE_DIFF', 'AGND', 'BLUE_SUM', 'BLUE_SHAPE')
    passive('R_BLUE_FEEDBACK', '100 kΩ', 'BLUE_SHAPE', 'BLUE_SUM')
    passive('C_BLUE_FEEDBACK', '33 pF', 'BLUE_SHAPE', 'BLUE_SUM')
    internal.update(('PINK_SOURCE', 'BROWN_SUM', 'BLUE_SERIES', 'BLUE_SUM'))
    allowed = {p.key for p in checked.values()}
    for p in parts:
        if not p.dnp and internal.intersection(p.pins.values()) and p.key not in allowed:
            raise ValueError(f'Noise model has an unprojected internal connection: {p.key}')
    return {
        'included': 'Fixed nominal reconstruction, AC coupling, buffer and colour-shaping subgraph',
        'ideal_boundaries': ['WHITE_RAW and PINK_RAW are separate flat ideal AC sources',
                             'WHITE_SIGNAL, PINK_SIGNAL, BROWN_SHAPE and BLUE_SHAPE are model outputs',
                             'Amplifiers have ideal input/output impedance and finite open-loop gain 1e6',
                             'WHITE/PINK include an extra synthetic closed-loop 1e6 readout follower; it is not a captured stage'],
        'excluded': ['NOISE2 spectra, output impedance, clock feedthrough and supply behavior',
                     'Level stages, trims, output cells, jack loads and cross-channel coupling',
                     'Offset, bias, leakage, tolerance, temperature, rails, headroom and hardware stability'],
        'checked_parts': {role: {'symbol': p.symbol, 'unit': p.unit, 'value': p.value,
                                 'pins': p.pins}
                          for role, p in sorted(checked.items())},
    }
