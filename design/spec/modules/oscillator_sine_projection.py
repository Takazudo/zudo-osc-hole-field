"""Select the captured sine shaper, excluding local-reference fanout fixtures."""
from design.spec.modules.io_partition import AMP_MAPS

SINE_RESISTORS = tuple('oscillator:R_SINE_' + name for name in (
    'ATTEN', 'BASE_GND', 'OFFSET', 'TAIL', 'COLLECTOR1', 'COLLECTOR2',
    'DIFF_PLUS', 'DIFF_GROUND', 'DIFF_MINUS', 'DIFF_FB', 'GAIN_IN', 'GAIN_FIXED'))
SINE_AMPLIFIERS = ('oscillator:SINE_DIFF', 'oscillator:SINE_GAIN')
SINE_ROLES = SINE_RESISTORS + SINE_AMPLIFIERS
LIBRARY = 'zudo-osc-hole-field:'
BOUNDARY = ('Only the selected sine-shaper resistors/amplifier connections are projected; '
            'the matched pair uses a generic NPN model, the symmetry wiper is an ideal 1.5 V '
            'source and the level rheostat is a fixed 5.5 kohm fixture. '
            'Local SINE_REF5/REFN5 fanout, actual symmetry-pot loading and output loading '
            'are excluded. This does not simulate the full reference or oscillator circuit.')


def sine_parts(parts):
    """Preserve source order while requiring the complete declared membership."""
    if len({p.key for p in parts}) != len(parts):
        raise ValueError('Sine projection has duplicate part identities')
    selected = [p for p in parts if p.attributes.get('Role') in SINE_ROLES]
    for role in SINE_ROLES:
        found = [p for p in selected if p.attributes.get('Role') == role]
        if len(found) != 1 or found[0].dnp:
            raise ValueError(f'Sine projection requires one fitted {role}')
        p = found[0]
        if role in SINE_RESISTORS:
            if (p.prefix not in ('R', 'RB') or p.unit != 0 or
                    p.symbol != LIBRARY + 'RT0603BRD07100KL' or set(p.pins) != {'1', '2'}):
                raise ValueError(f'Unsupported sine resistor primitive: {role}')
        else:
            if (p.prefix != 'U' or p.symbol not in (LIBRARY + 'OPA4196IDR', LIBRARY + 'OPA4197IPWR') or
                    p.unit not in (1, 2, 3, 4) or set(p.pins) != set(AMP_MAPS[p.unit - 1])):
                raise ValueError(f'Unsupported sine amplifier primitive: {role}')
    return selected
