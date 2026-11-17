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
    'SN74HC00DR': {'maximum_pF': 10, 'typical_pF': 3, 'typical_temperature_C': 25,
                  'VCC_V': [2, 6], 'temperature_C': [-40, 85],
                  'pdf': 'circuit/sources/ic-library/SN74HC00.pdf',
                  'locator': 'SCLS181H, printed p5, physical index4, section6.5 Ci Commercial (74xx)',
                  'scope': 'DEVICE_INPUT_ONLY; project applicability NOT_ESTABLISHED'},
    'CD74HC221M96': {'maximum_pF': 10, 'typical_pF': None,
                  'VCC_V': None, 'VCC_source_cell': '-', 'test_conditions_source_cell': '-',
                  'temperature_C': [-40, 85], 'family_block': 'HC TYPES (continued from printed p6)',
                  'table_header': 'Switching Specifications Input tr, tf = 6ns (Continued)',
                  'pdf': 'circuit/sources/ic-library/CD74HC221.pdf',
                  'locator': 'SCHS166F, printed p7, physical index6, upper HC CIN row; -40..85C MAX column',
                  'scope': 'DEVICE_INPUT_ONLY; no numeric VCC inferred; project applicability NOT_ESTABLISHED'},
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


def receiver_sums(contacts, observations):
    """Sum catalog maxima only, without claiming a shared actual operating corner."""
    if observations != CI:
        raise ValueError('Ci conditions/provenance drift')
    expected = {'CLOCK': {'CLOCK_INPUT': ('SN74HC74DR', 17)},
                'READY': {'CLEAR_INPUT': ('SN74HC74DR', 15),
                          'NAND_INPUT': ('SN74HC00DR', 3),
                          'ONE_SHOT_RESET_INPUT': ('CD74HC221M96', 1)}}
    result = {}
    for net, classes in expected.items():
        seen = set(); groups = []; excluded = []
        for row in contacts[net]:
            key = (row['ref'], row['pin'])
            if key in seen: raise ValueError('duplicate physical contact in sum')
            seen.add(key)
            if row['classification'] != classify(row['mpn'], row['pin'], row['ref']):
                raise ValueError('receiver classification changed')
            if row['classification'] not in classes:
                excluded.append(row)
        for classification, (mpn, count) in classes.items():
            rows = [r for r in contacts[net] if r['classification'] == classification]
            if len(rows) != count or any(r['mpn'] != mpn for r in rows):
                raise ValueError('receiver membership changed')
            groups.append({'classification': classification, 'mpn': mpn, 'receiver_count': len(rows),
                'named_receivers': rows, 'source_observation': observations[mpn],
                'conditional_catalog_max_sum_pF': len(rows) * observations[mpn]['maximum_pF']})
        result[net] = {'status': 'CONDITIONAL_CATALOG_ARITHMETIC_ONLY', 'groups': groups,
            'conditional_catalog_max_sum_pF': sum(g['conditional_catalog_max_sum_pF'] for g in groups),
            'excluded_contacts': excluded, 'shared_project_conditions': 'NOT_ESTABLISHED',
            'actual_receiver_load_pF': None, 'actual_total_load_pF': None,
            'actual_load_lower_bound_pF': None, 'timing_verdict': 'NOT_ESTABLISHED',
            'other_unknowns': ['driver/network behavior', 'routing and coupling parasitics',
                              'actual supply/temperature/edge conditions', 'RC feedback loading']}
    return result


def canonical_ci(root, evidence):
    links = evidence['canonical_ci']
    if set(links) != set(CI): raise ValueError('canonical Ci identity set changed')
    for mpn, link in links.items():
        owner = root / link['owner']; expected = link['fact']
        facts = json.loads((owner / 'facts.json').read_text())['facts']
        matches = [f for f in facts if f['fact_id'] == expected['fact_id']]
        if matches != [expected]: raise ValueError('canonical Ci fact drift')
        if expected['value'] != CI[mpn]['maximum_pF'] or expected['unit'] != 'pF':
            raise ValueError('canonical Ci numeric mismatch')
        coverage = [c for c in json.loads((owner / 'coverage.json').read_text())['coverage']
                    if c['domain'] == 'electrical limits']
        if coverage != [link['electrical_coverage']] or coverage[0]['status'] != 'OPEN' or not coverage[0]['blocking_fact_ids']:
            raise ValueError('canonical Ci coverage unknowns changed')
        if expected['fact_id'] not in coverage[0]['fact_ids']:
            raise ValueError('canonical Ci coverage linkage absent')
    return links


def audit(root=ROOT):
    evidence = json.loads((HERE / 'evidence.json').read_text())
    for path, sha in evidence['sha256'].items():
        if digest(root / path) != sha: raise ValueError('source pin changed: ' + path)
    contacts = validate(json.loads((root / REPORT).read_text()), pin_maps(root), evidence)
    canonical = canonical_ci(root, evidence)
    return {'status': 'SOURCE_CONTRACT_MATCH; PHYSICAL_APPLICABILITY_NOT_ESTABLISHED',
        'source_commit': evidence['source_commit'], 'engineering_commit': evidence['engineering_commit'],
        'source_history': evidence['source_history'], 'canonical_ci': canonical, 'sha256': evidence['sha256'],
        'contacts': contacts, 'counts': {n: dict(Counter(r['classification'] for r in rows)) for n, rows in contacts.items()},
        'ci_observations': CI, 'nominal_RC': evidence['nominal_RC'],
        'receiver_only_sums': receiver_sums(contacts, CI),
        'actual_total_load_pF': None, 'guaranteed_clock_frequency_Hz': None,
        'clock_edge_bound_ns': None, 'ready_recovery_slack_ns': None,
        'physical_timing_acceptance': 'NOT_ESTABLISHED', 'native': 'NOT_RUN',
        'hardware_adoption': 'HOLD'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
