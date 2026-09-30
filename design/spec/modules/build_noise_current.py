"""N1 preliminary rail worksheet; NOISE2 operating current is unqualified."""
from collections import Counter
import json
from design.spec.modules.noise import family
from design.spec.cells._builder import ROOT

RAILS = ('+12V', '-12V', '+5V')
LOADS = {x['id']: x for x in json.loads((ROOT / 'design/standard/rail-budget-preliminary.json').read_text())['loads']}


def build():
    f = family()
    packages = {p.key.rsplit('.', 1)[0]: p.symbol.rsplit(':', 1)[-1]
                for p in f.parts if p.prefix == 'U'}
    counts = Counter(packages.values())
    typical = dict.fromkeys(RAILS, 0.0)
    planning = typical.copy()
    rows = []

    def add(load, count, a, b, basis):
        a = dict(zip(RAILS, a)); b = dict(zip(RAILS, b))
        for rail in RAILS:
            typical[rail] += count * a[rail]
            planning[rail] += count * b[rail]
        rows.append({'load': load, 'count': count, 'typical_unit_mA': a,
                     'planning_unit_mA': b, 'basis': basis})

    op = LOADS['opamp_audio']
    add('OPA4196IDR whole quad package', counts['OPA4196IDR'],
        [op['typical_unit_mA'][r] for r in RAILS],
        [op['planning_unit_mA'][r] for r in RAILS], op['basis'])
    add('Four external output loads', 4, (.05, .05, 0), (.5, .5, 0),
        'Standard general output: nominal 5V/100k and planning 5V/10k per direction; shorts excluded.')
    add('NOISE2 filtered digital supply', 1, (0, 0, 5), (0, 0, 10),
        'Explicit planning allowance, NOT manufacturer typical or maximum. The retained NOISE2 PDF does not establish supply current; measure it before rail closure.')
    return {'schema_version': 1, 'module': 'noise',
            'authority': 'PROPOSAL (planning, owner-delegated)',
            'status': 'Incomplete planning worksheet; NOISE2 current and guaranteed maxima unestablished',
            'IC_packages_per_instance': dict(sorted(counts.items())),
            'breakdown': rows,
            'instances': [{'instance': 'N1',
                           'planning_typical_mA': {r: round(typical[r], 6) for r in RAILS},
                           'planning_upper_mA': {r: round(planning[r], 6) for r in RAILS},
                           'guaranteed_maximum_mA': {r: None for r in RAILS}}],
            'planning_upper_total_mA': {r: round(planning[r], 6) for r in RAILS},
            'guaranteed_maximum_status': 'NOT ESTABLISHED - NOISE2 supply current, signal drive, temperature, startup and fault loads unqualified',
            'note': 'NOISE2 filtered supply R=22Ω would drop 0.22V at the assumed 10mA; measured current and minimum VDD are mandatory gates. No switch/LED load in this module.'}


def main(check=False):
    path = ROOT / 'design/reports/current/noise.json'
    value = json.dumps(build(), indent=2) + '\n'
    if check:
        assert path.read_text() == value, 'noise current report drift'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
    print('Noise planning upper:', build()['planning_upper_total_mA'])


if __name__ == '__main__':
    import sys
    main('--check' in sys.argv)
