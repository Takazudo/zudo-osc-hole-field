"""Dated procurement candidates and geometry gaps, without CAD or native execution."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = 'e2e580aed4620e86357341d660bbf04f356d33f2'
REL = 'design/architecture-278/implementation/'
OUT = ROOT / REL / 'stage21'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_text(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n'


def parse_jlc(html, mpn, code):
    """Read exact product componentInfo, never related-product stock or page URL."""
    blocks = re.findall(r'self\.__next_f\.push\((\[1,.*?\])\)</script>', html)
    decoded = ''.join(json.loads(block)[1] for block in blocks)
    decoder = json.JSONDecoder()
    records = [decoder.raw_decode(decoded[m.end():])[0]
               for m in re.finditer(r'"componentInfo":', decoded)]
    for i, row in enumerate(records):
        if isinstance(row, str):
            need(re.fullmatch(r'\$[0-9a-f]+', row), 'unsupported product reference')
            definitions = [m.end()-1 for m in re.finditer(re.escape(row[1:])+r':\{', decoded)]
            need(len(definitions) == 1, 'missing or duplicate product reference')
            records[i] = decoder.raw_decode(decoded[definitions[0]:])[0]
    need(records, 'no server product observation; search zero is inconclusive')
    for row in records:
        need(isinstance(row, dict), 'product observation must be object')
        need(row.get('componentModelEn') == mpn and row.get('componentCode') == code,
             'supplier exact identity mismatch')
    merged = {}
    keys = ('componentModelEn', 'componentCode', 'componentBrandEn',
            'componentSpecificationEn', 'componentLibraryType',
            'assemblyComponentFlag', 'overseasStockCount')
    for row in records:
        for key in keys:
            if key in row:
                need(key not in merged or merged[key] == row[key], 'conflicting supplier observations')
                merged[key] = row[key]
    need(merged.get('componentBrandEn') in ('YAGEO', 'KEMET'), 'supplier manufacturer missing')
    stock = merged.get('overseasStockCount')
    need(stock is None or (type(stock) is int and stock >= 0), 'invalid supplier stock')
    return merged


def geometry(text):
    """Measure captured, unrotated two-pad source footprints; reject other shapes."""
    pattern = r'\(pad ([12]) smd rect \(at (-?[\d.]+) ([\d.]+) ([\d.]+)\) \(size ([\d.]+) ([\d.]+)\)'
    matches = re.findall(pattern, text)
    need(len(re.findall(r'\(pad\s', text)) == len(matches) == 2
         and {m[0] for m in matches} == {'1', '2'}, 'two distinct rectangular pads required')
    pads = {m[0]: list(map(float, m[1:])) for m in matches}
    a, b = pads['1'], pads['2']
    need(a[1:3] == b[1:3] == [0, 0] and a[0] == -b[0] and b[0] > 0,
         'unexpected pad orientation')
    need(a[3:] == b[3:] and all(math.isfinite(v) for p in pads.values() for v in p), 'pad geometry')
    need(all(v > 0 for v in a[3:]), 'positive pads')
    return {'pad_center_abs_x': b[0], 'pad_length_x': a[3], 'pad_width_y': a[4],
            'pad_gap_mm': round(2*b[0]-a[3], 9), 'overall_pad_length_mm': round(2*b[0]+a[3], 9)}


def protected():
    changed = subprocess.check_output(['git', 'diff', BASE, '--name-only', '--diff-filter=DMRTUXB'], cwd=ROOT, text=True).splitlines()
    need(set(changed) <= {REL+'WORK.md'}, 'preexisting protected bytes changed: '+repr(changed))
    added = subprocess.check_output(['git', 'diff', BASE, '--name-only', '--diff-filter=A'], cwd=ROOT, text=True).splitlines()
    added += subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    allowed = {'scripts/architecture278/implementation/'+n for n in ('stage21_inventory.py', 'test_stage21_inventory.py')}
    need(all(p.startswith(REL+'stage21/') or p in allowed for p in added), 'out-of-scope addition')
    # Unlike historical stage20_replay.protected(), this allows only Stage21 additions
    # over the exact completed Stage20 commit, preserving its entire report and raw FAIL.
    return {'baseline_commit': BASE, 'all_preexisting_tracked_bytes_preserved_except': [REL+'WORK.md']}


def analyze(spec, land, previous, packages, transport, footprints):
    need(spec['status'] == 'CANDIDATES_ONLY_NOT_ADOPTED' and spec['application_qualified'] is False
         and spec['canonical_BOM_changed'] is False, 'candidate-only boundary')
    refs = {r for r, p in packages.items() if p['selected_mpn'] is None}
    need(len(refs) == 19 and set(spec['selections']) == refs, 'complete19 unselected references')
    mpns = {previous['selections'][r]['candidate_MPN'] for r in refs}
    need(len(mpns) == 9, 'nine exact candidates')
    out = {}
    for ref in sorted(refs):
        choice = spec['selections'][ref]
        need(choice['captured_source'] == packages[ref], 'source identity/pins/units/value drift '+ref)
        need(choice['adopted'] is False and len(choice['missing_decision']) > 40
             and len(choice['common_requirements']) == 3, 'unresolved selection decision '+ref)
        mpn = choice['candidate_mpn']
        need(mpn == previous['selections'][ref]['candidate_MPN'], 'candidate identity substitution '+ref)
        evidence = spec['sources'][mpn]
        need(evidence['ratings'] == previous['parts'][mpn], 'primary rating substitution '+ref)
        need(evidence['authority'] == 'MANUFACTURER_PRIMARY' and evidence['pdf'] is True
             and evidence['url'] == 'https://yageogroup.com/component-documentation/download/specsheet/'+mpn,
             'exact primary source required')
        need(evidence['previous_sha256'] == previous['sources'][mpn]['sha256'], 'historical primary hash drift')
        part = evidence['ratings']
        value = float(packages[ref]['unit_records'][0]['value'].split()[0])
        need(math.isclose(value, part['value_SI'], rel_tol=1e-12), 'nominal value differs from candidate')
        row = {'candidate_mpn': mpn, 'role': packages[ref]['unit_records'][0]['attributes']['Role'],
               'missing_decision': choice['missing_decision'], 'selected_mpn': None,
               'nominal_value_SI': value, 'ratings': part, 'common_requirements': choice['common_requirements']}
        if part['kind'] == 'R':
            row['conditional_70C_working_voltage_bound_V'] = min(part['maximum_continuous_voltage_V'], math.sqrt(part['power_W_at_70C']*value*(1-part['tolerance_fraction'])))
            row['in_circuit_rating_pass'] = None
        out[ref] = row
    unbound = {r: p for r, p in transport.items() if not p['footprint_source']}
    need(len(unbound) == 24 and spec['unbound'] == unbound, 'all24 unbound identities and flags required')
    for name in ('capacitor', 'resistor', 'DIN', 'annotations'):
        need(land[name]['qualified'] is False and len(land[name]['missing_decision']) > 40, 'physical qualification boundary')
    need(land['annotations']['mpn_applicable'] is False, 'annotations cannot become fitted parts')
    need(all(land['DIN'][k] is None for k in ('recommended_finished_hole_mm', 'pad_mm', 'flange_holes')), 'no guessed DIN drill/land')
    need(land['resistor']['recommended_pattern_mm'] is None, 'unverified resistor mounting guide')
    need(land['capacitor']['density_patterns_mm'] == {
        'A': {'pad_center_abs_x': .9, 'pad_length_x': 1.15, 'pad_width_y': 1.1, 'courtyard': [4, 2.1]},
        'B': {'pad_center_abs_x': .8, 'pad_length_x': .95, 'pad_width_y': 1, 'courtyard': [3.1, 1.5]},
        'C': {'pad_center_abs_x': .6, 'pad_length_x': .75, 'pad_width_y': .9, 'courtyard': [2.4, 1.2]}}, 'KEMET Table3 transcription drift')
    comparison = {}
    for name, text in footprints.items():
        measured = geometry(text)
        comparison[name] = {'captured_mm': measured, 'qualified': False}
        if name == 'C0603':
            comparison[name]['delta_captured_minus_recommended_mm'] = {
                level: {key: round(measured[key]-pattern[key], 9) for key in ('pad_center_abs_x', 'pad_length_x', 'pad_width_y')}
                for level, pattern in land['capacitor']['density_patterns_mm'].items()}
    need(set(footprints) == {'R0603', 'C0603'}, 'both captured footprints')
    need(set(spec['supplier_observations']) == mpns, 'all candidate sourcing outcomes required')
    for mpn, observations in spec['supplier_observations'].items():
        need(observations and {o['supplier'] for o in observations} == {'LCSC', 'JLCPCB'}, 'both suppliers researched')
        for obs in observations:
            need(obs['allocation_confirmed'] is False and obs['retrieved_at'].startswith('2026-10-16T'), 'dated observation not allocation')
            if obs['status'] == 'EXACT_LISTING':
                need(obs['observed']['componentModelEn'] == mpn and re.fullmatch(r'C[0-9]+', obs['observed']['componentCode']), 'exact supplier model/code')
                need(obs['source_id'] in spec['sources'], 'supplier raw source missing')
                evidence = spec['sources'][obs['source_id']]
                code = obs['observed']['componentCode']
                need(evidence['authority'] == 'SUPPLIER_CATALOG' and obs['supplier'] == 'JLCPCB'
                     and obs['url'] == evidence['url'] and obs['retrieved_at'] == evidence['retrieved_at']
                     and evidence['url'].startswith('https://jlcpcb.com/partdetail/')
                     and evidence['url'].endswith('/'+code) and obs['source_id'] == 'jlc-'+code,
                     'supplier source/code binding')
                need(obs['observed'].get('componentBrandEn') == ('KEMET' if mpn.startswith('C') else 'YAGEO')
                     and obs['observed'].get('componentSpecificationEn') == '0603', 'supplier manufacturer/package')
            else:
                need(obs['status'] in ('HTTP403', 'SEARCH_INCONCLUSIVE') and obs['observed'] is None, 'lookup failure is not absent or zero stock')
    for sid, evidence in spec['sources'].items():
        need(re.fullmatch('[0-9a-f]{64}', evidence['sha256']) and evidence['sha256'] != '0'*64
             and evidence['bytes'] > 0 and evidence['retrieved_at'].startswith('2026-10-16T'), 'dated source receipt '+sid)
    for sid, sha in {
        'kemet-c0g': '02d179914aeb9585eb2229ba8e18ef9d6b01c77c056de2af295d6950a2a5cc0d',
        'kemet-x7r': 'd8e6ca6631862e31a19b90b6cfe13f1b20153c2efd6c8e30f1a5d5ba147aa908',
        'harting-female-pdf': '978b11ceab4ffa9b0bf7661240a6b32eb54bec8197e8bf1f726761b88db0eed6',
        'harting-male-pdf': '736b7a87209f7e1e59610d3897b9922aab8fe4833276fb43af16165aa26a982e',
    }.items():
        need(sid in spec['sources'] and spec['sources'][sid]['sha256'] == sha, 'reviewed mechanical source '+sid)
    return {'status': 'SOURCE_AUDIT_PASS_SELECTION_AND_PHYSICAL_ACCEPTANCE_OPEN',
            'counts': {'unselected_references': 19, 'distinct_candidates': 9, 'resistors': 17, 'capacitors': 2,
                       'unbound_DIN': 2, 'non_BOM_non_board_annotations': 22},
            'candidates': out, 'footprint_comparison': comparison, 'footprint_decisions': land,
            'supplier_observations': spec['supplier_observations'], 'native_execution': 'NONE',
            'electrical_acceptance': False, 'selected_MPN_count_changed': False,
            'retained_XML_scope': 'Stage20 unchanged118refs/561pins/154UUIDs/196NCs only; no qualification of changed inputs.'}


def build(check_cache=False):
    previous = read(ROOT/REL/'stage11/identity-input.json')
    spec, land = read(OUT/'inventory-input.json'), read(OUT/'footprint-input.json')
    inputs = [ROOT/REL/'stage16/inputs-report.json', ROOT/REL/'stage17/generated/transport-component-rows.json']
    mechanical_path = ROOT/REL/'stage4/mechanical-input.json'
    mechanical = read(mechanical_path)
    need(land['DIN']['retained_evidence'] == {sex: mechanical[sex+'_evidence'] for sex in ('female', 'male')}, 'DIN identity/dimensions drift')
    fps = {n: ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/f'{n}.kicad_mod' for n in ('R0603', 'C0603')}
    result = analyze(spec, land, previous, read(inputs[0])['packages'], read(inputs[1]), {n:p.read_text() for n,p in fps.items()})
    result['preservation'] = protected()
    if check_cache:
        for sid, source in spec['sources'].items():
            path = ROOT/source['raw_cache']
            need(path.is_file() and digest(path) == source['sha256'] and path.stat().st_size == source['bytes'], 'raw source missing or changed '+sid)
        for mpn, observations in spec['supplier_observations'].items():
            for obs in observations:
                if obs['status'] == 'EXACT_LISTING' and obs['supplier'] == 'JLCPCB':
                    raw = ROOT/spec['sources'][obs['source_id']]['raw_cache']
                    need(parse_jlc(raw.read_text(), mpn, obs['observed']['componentCode']) == obs['observed'], 'supplier replay drift')
    files = inputs + [mechanical_path] + list(fps.values()) + [ROOT/REL/'stage11/identity-input.json', OUT/'inventory-input.json', OUT/'footprint-input.json', OUT/'README.md', Path(__file__), Path(__file__).with_name('test_stage21_inventory.py')]
    result['source_sha256'] = {str(p.relative_to(ROOT)): digest(p) for p in files}
    return result


def main():
    p = argparse.ArgumentParser(); p.add_argument('--check', action='store_true'); p.add_argument('--check-cache', action='store_true'); args = p.parse_args()
    body = json_text(build(args.check_cache)); path = OUT/'inventory-report.json'
    if args.check: need(path.read_text() == body, 'Stage21 report drift')
    else: path.write_text(body)
    print('PASS Stage21 source audit:19 passive refs/9 candidates/24 unbound; selection and hardware acceptance OPEN')


if __name__ == '__main__':
    main()
