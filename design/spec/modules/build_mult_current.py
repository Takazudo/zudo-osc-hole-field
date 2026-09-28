"""Per-instance MULT rail-current planning from the captured IC packages and loads."""
from collections import Counter
import json

from design.spec.modules.mult import ROOT, INSTANCES, family

RAILS = ('+12V', '-12V', '+5V')
LOADS = {row['id']: row for row in json.loads(
    (ROOT / 'design/standard/rail-budget-preliminary.json').read_text())['loads']}


def build():
    spec = family()
    packages = {part.key.rsplit('.', 1)[0]: part.symbol.split(':')[-1]
                for part in spec.parts if part.prefix == 'U'}
    counts = Counter(packages.values())
    typical = dict.fromkeys(RAILS, 0.0)
    planning_max = typical.copy()
    breakdown = []

    def add(name, count, typical_unit, max_unit, basis):
        for rail in RAILS:
            typical[rail] += count * typical_unit[rail]
            planning_max[rail] += count * max_unit[rail]
        breakdown.append({'load': name, 'count': count,
                          'typical_unit_mA': typical_unit,
                          'planning_maximum_unit_mA': max_unit, 'basis': basis})

    for symbol, load_id in (('OPA4197IPWR', 'opamp_precision'),
                            ('OPA4196IDR', 'opamp_indicator'),
                            ('ADG5412FBRUZ', 'fault_switches')):
        count = counts[symbol]
        if count:
            row = LOADS[load_id]
            add(symbol, count, row['typical_unit_mA'], row['planning_unit_mA'], row['basis'])

    indicators = sum(1 for part in spec.parts if part.attributes.get('PanelUid', '').startswith('L:'))
    add('Magnitude indicator envelope', indicators,
        {'+12V': .25, '-12V': .25, '+5V': 0},
        {'+12V': 1.25, '-12V': 1.25, '+5V': 0},
        'OSC-ES-1 magnitude LED envelope per indicator; rail peaks need not coincide.')
    output_count = 3
    add('External output loads', output_count,
        {'+12V': .05, '-12V': .05, '+5V': 0},
        {'+12V': .5, '-12V': .5, '+5V': 0},
        'OSC-ES-1 planning envelope: 5 V into 100 kΩ typical / 10 kΩ planning per output; shorts excluded.')
    add('Input-isolator enable feed', 1,
        {'+12V': 0, '-12V': 0, '+5V': .05},
        {'+12V': 0, '-12V': 0, '+5V': .075},
        'One 5 V / 101 kΩ feed plus a small logic allowance; estimate, not guaranteed.')

    return {
        'schema_version': 1,
        'module': 'mult',
        'authority': 'PROPOSAL (planning, owner-delegated)',
        'status': 'Unvalidated per-instance rail estimate; not measured and not a guaranteed maximum',
        'units': 'mA',
        'IC_packages_per_instance': dict(sorted(counts.items())),
        'breakdown': breakdown,
        'instances': [
            {'instance': name,
             'typical_mA_per_rail': {rail: round(typical[rail], 6) for rail in RAILS},
             'planning_maximum_mA_per_rail': {rail: round(planning_max[rail], 6) for rail in RAILS},
             'guaranteed_maximum_mA_per_rail': {rail: None for rail in RAILS}}
            for name in INSTANCES],
        'guaranteed_maximum_status': 'NOT ESTABLISHED - load-current overlap, clamp/fault behavior, temperature and output short conditions are unqualified',
        'omitted_transients': ['input fault/clamp current', 'simultaneous output short', 'capacitive load and startup', 'external source back-drive'],
        'note': 'Planning maximum is an allowance, not a device or module limit. Full instrument closure remains owned by the system-level power task.'
    }


def main(check=False):
    path = ROOT / 'design/reports/current/mult.json'
    body = json.dumps(build(), indent=2) + '\n'
    if check:
        assert path.read_text() == body, 'MULT current report drift'
    else:
        path.write_text(body)
    print('MULT per-instance planning maximum:', build()['instances'][0]['planning_maximum_mA_per_rail'])


if __name__ == '__main__':
    import sys
    main('--check' in sys.argv)
