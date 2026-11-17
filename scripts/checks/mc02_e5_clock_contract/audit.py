"""Source contacts and conditioned Ci observations; no physical timing acceptance."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPORT = 'design/reports/io-partition.json'
NETS = ('CLOCK_RC', 'CLOCK', 'READY')
OWNERS = ('sn74hc74dr', 'sn74hc14dr', 'sn74hc00dr', 'cd74hc221m96')
CI = {
    'SN74HC74DR': {'maximum_pF': 10, 'typical_pF': 3, 'typical_temperature_C': 25,
                  'VCC_V': [2, 6], 'temperature_C': [-40, 85],
                  'pdf': 'circuit/sources/ic-library/SN74HC74.pdf',
                  'locator': 'SCLS094F, printed p5, physical index4, section6.5 Ci (-74)',
                  'scope': 'DEVICE_INPUT_ONLY; project applicability NOT_ESTABLISHED'},
    'SN74HC14DR': {'maximum_pF': 10, 'typical_pF': 3, 'typical_temperature_C': 25,
                  'VCC_V': [5, 5], 'temperature_C': [-40, 85],
                  'pdf': 'circuit/sources/ic-library/SN74HC14.pdf',
                  'locator': 'SCLS085L, printed p5, physical index4, section5.5 Ci (-74)',
                  'scope': 'DEVICE_INPUT_ONLY; project applicability NOT_ESTABLISHED'},
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin_maps(root):
    maps = {}
    for owner in OWNERS:
        path = f'.claude/skills/component-ti-{owner}/pin-map.json'
        row = json.loads((root / path).read_text())['pin_maps'][0]
        maps[row['symbol']] = {p['symbol_pin']: p['function'] for p in row['pins']}
    return maps


def classify(mpn, pin, ref):
    if ref == 'R4533': return 'FEEDBACK_RESISTOR_TERMINAL'
    if ref == 'C4509': return 'RC_CAPACITOR_TERMINAL'
    if mpn == 'SN74HC74DR':
        if pin in ('3', '11'): return 'CLOCK_INPUT'
        if pin in ('1', '13'): return 'CLEAR_INPUT'
        if pin == '9': return 'Q_DRIVER'
    if mpn == 'SN74HC14DR':
        if pin == '9': return 'SCHMITT_INPUT'
        if pin == '8': return 'SCHMITT_DRIVER'
    if mpn == 'SN74HC00DR' and pin in ('9', '4', '12'): return 'NAND_INPUT'
    if mpn == 'CD74HC221M96' and pin == '3': return 'ONE_SHOT_RESET_INPUT'
    raise ValueError('unexpected contact identity/role')


def extract(report, maps):
    packages = {}
    for p in report['physical_packages']:
        if p['ref'] in packages: raise ValueError('duplicate package')
        packages[p['ref']] = p
    result = {n: [] for n in NETS}
    seen = set()
    for unit in report['package_units']:
        for pin, net in unit['pins'].items():
            if net not in ['/E5/' + n for n in NETS]: continue
            key = (unit['ref'], unit['unit'], pin)
            if key in seen: raise ValueError('duplicate contact')
            seen.add(key)
            p = packages[unit['ref']]
            if p['instance'] != 'E5': raise ValueError('wrong instance')
            mpn = p['mpn']
            if p['ref'] in ('R4533', 'C4509') and mpn != '':
                raise ValueError('blank MPN promoted')
            function = maps[mpn][pin] if mpn else 'PASSIVE_TERMINAL; EXACT_MPN_UNBOUND'
            result[net[4:]].append({'ref': p['ref'], 'unit': unit['unit'], 'pin': pin,
                'role': unit['role'], 'mpn': mpn, 'symbol_template': p['symbol'],
                'pin_function': function, 'classification': classify(mpn, pin, p['ref'])})
    return {n: sorted(rows, key=lambda r: (r['ref'], r['unit'], r['pin'])) for n, rows in result.items()}


def validate(report, maps, evidence):
    contacts = extract(report, maps)
    if contacts != evidence['contacts']: raise ValueError('semantic contacts drift')
    if evidence['ci_observations'] != CI: raise ValueError('Ci conditions/provenance drift')
    expected_rc = {'resistor': ('R4533', 'ohm', 47000), 'capacitor': ('C4509', 'farad', 1e-9)}
    for kind, (ref, unit, value) in expected_rc.items():
        row = evidence['nominal_RC'][kind]
        if row['ref'] != ref or row[unit] != value or row['mpn'] != '' or row['tolerance'] is not None:
            raise ValueError('nominal RC proposal promoted or changed')
    return contacts


def audit(root=ROOT):
    evidence = json.loads((HERE / 'evidence.json').read_text())
    for path, sha in evidence['sha256'].items():
        if digest(root / path) != sha: raise ValueError('source pin changed: ' + path)
    contacts = validate(json.loads((root / REPORT).read_text()), pin_maps(root), evidence)
    return {'status': 'SOURCE_CONTRACT_MATCH; PHYSICAL_APPLICABILITY_NOT_ESTABLISHED',
        'source_commit': evidence['source_commit'], 'sha256': evidence['sha256'],
        'contacts': contacts, 'counts': {n: dict(Counter(r['classification'] for r in rows)) for n, rows in contacts.items()},
        'ci_observations': CI, 'nominal_RC': evidence['nominal_RC'],
        'actual_total_load_pF': None, 'guaranteed_clock_frequency_Hz': None,
        'clock_edge_bound_ns': None, 'ready_recovery_slack_ns': None,
        'physical_timing_acceptance': 'NOT_ESTABLISHED', 'native': 'NOT_RUN',
        'hardware_adoption': 'HOLD'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
