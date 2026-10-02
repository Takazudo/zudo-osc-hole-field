"""Check the captured AO subgraph before projecting its ideal DC model."""
from design.spec.modules.io_partition import AMP_MAPS

SOURCE_LIBRARY = 'zudo-osc-hole-field:'


def model_contract(parts):
    if len({p.key for p in parts}) != len(parts):
        raise ValueError('AO capture has duplicate part identities')
    checked = {}

    def one(role):
        matches = [p for p in parts if p.attributes.get('Role') == role]
        if len(matches) != 1 or matches[0].dnp:
            raise ValueError(f'AO model requires one fitted {role}')
        checked[role] = matches[0]
        return matches[0]

    def passive(role, value, a, b):
        p = one(role)
        kind = 'C' if role == 'bipolar_attenuverter:C_FB' else 'R'
        symbol = ('C0603C101J5GACTU' if kind == 'C' else
                  'RC0603FR-07100KL' if role in ('bipolar_attenuverter:R_W',
                                               'bipolar_attenuverter:R_FAIL') else
                  'RT0603BRD07100KL')
        if p.prefix != kind or p.unit != 0 or p.symbol != SOURCE_LIBRARY + symbol:
            raise ValueError(f'AO model passive identity changed: {role}')
        if p.value != value or p.pins != {'1': a, '2': b}:
            raise ValueError(f'AO model value/connectivity changed: {role}')

    def amp(role, plus, minus, out):
        p = one(role)
        if (p.prefix != 'U' or p.symbol != SOURCE_LIBRARY + 'OPA4197IPWR' or
                p.unit not in (1, 2, 3, 4)):
            raise ValueError(f'AO model amplifier identity changed: {role}')
        output, negative, positive = AMP_MAPS[p.unit - 1]
        if p.pins != {output: out, negative: minus, positive: plus}:
            raise ValueError(f'AO model amplifier connectivity changed: {role}')

    pot = one('bipolar_attenuverter:RV')
    if (pot.prefix != 'RV' or pot.unit != 0 or
            pot.symbol != SOURCE_LIBRARY + 'PTV09A-4020F-B103'):
        raise ValueError('AO model attenuator pot identity changed')
    if (pot.value != 'PTV09A-4020F-B103' or
            set(pot.pins) != {'1', '2', '3', '4', '5'} or
            pot.pins['4'] is not None or pot.pins['5'] is not None or
            pot.pins.get('1') != 'AGND' or
            pot.pins.get('3') != 'IN_REMOTE' or not pot.pins.get('2')):
        raise ValueError('AO model attenuator pot source changed')
    wiper = pot.pins['2']
    series = one('bipolar_attenuverter:R_W')
    sense = series.pins.get('2')
    named = {'IN_BUFFER', 'IN_REMOTE', 'MANUAL_OFFSET', 'OFFSET_BUFFER', 'AGND',
             'ATTEN_SUM', 'ATTEN_OUT', 'SUM_NODE', 'SUM_NEG', 'RESTORE_NODE',
             'OUT_INTERNAL'}
    if (not isinstance(wiper, str) or not isinstance(sense, str) or not sense or
            sense == wiper or wiper in named or sense in named):
        raise ValueError('AO model private wiper/sense nodes alias a circuit boundary')
    passive('bipolar_attenuverter:R_W', '1000 Ω', wiper, sense)
    passive('bipolar_attenuverter:R_FAIL', '1e+07 Ω', sense, 'AGND')
    passive('bipolar_attenuverter:R_IN', '100000 Ω', 'IN_BUFFER', 'ATTEN_SUM')
    passive('bipolar_attenuverter:R_FB', '100000 Ω', 'ATTEN_OUT', 'ATTEN_SUM')
    passive('bipolar_attenuverter:C_FB', '1e-11 F', 'ATTEN_OUT', 'ATTEN_SUM')
    amp('bipolar_attenuverter:A', sense, 'ATTEN_SUM', 'ATTEN_OUT')
    for name, start in (('ATTEN', 'ATTEN_OUT'), ('MANUAL', 'MANUAL_OFFSET'),
                        ('CV', 'OFFSET_BUFFER'), ('FB', 'SUM_NEG')):
        passive(f'offset:R_SUM_{name}', '100 kΩ', start, 'SUM_NODE')
    amp('offset:SUM', 'AGND', 'SUM_NODE', 'SUM_NEG')
    passive('offset:R_RESTORE_IN', '100 kΩ', 'SUM_NEG', 'RESTORE_NODE')
    passive('offset:R_RESTORE_FB', '100 kΩ', 'OUT_INTERNAL', 'RESTORE_NODE')
    amp('offset:RESTORE', 'AGND', 'RESTORE_NODE', 'OUT_INTERNAL')

    # Additional fitted connections at a modeled feedback node cannot silently
    # remain outside the fixed ideal deck. Output loads are explicitly excluded.
    internal = {wiper, sense, 'ATTEN_SUM', 'ATTEN_OUT', 'SUM_NODE',
                'SUM_NEG', 'RESTORE_NODE'}
    allowed = {p.key for p in checked.values()}
    for p in parts:
        if not p.dnp and internal.intersection(p.pins.values()) and p.key not in allowed:
            raise ValueError(f'AO model has an unprojected internal connection: {p.key}')
    return {
        'included': 'Attenuverter, three-input summer and sign-restoring amplifier DC algebra only',
        'ideal_boundaries': ['IN_BUFFER and IN_REMOTE are the same ideal input source',
                             'MANUAL_OFFSET and OFFSET_BUFFER are ideal voltage sources',
                             'Pot and wiper network are replaced by an ideal alpha divider',
                             'OUT_INTERNAL is the model output, not the jack'],
        'excluded': ['Source-facing protection and input/remote-buffer behavior',
                     'Finite pot/wiper loading, tolerance, contact failure and taper',
                     'Feedback-capacitor dynamics, finite amplifier rails and macromodel behavior',
                     'Reference, jack-output isolation, indicators and physical qualification'],
        'checked_parts': {role: {'symbol': p.symbol, 'unit': p.unit, 'value': p.value,
                                 'pins': p.pins}
                          for role, p in sorted(checked.items())},
    }
