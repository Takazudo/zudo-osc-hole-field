#!/usr/bin/env python3
"""Offline matching of blank-MPN requirements to existing UNADOPTED options."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_sources(root):
    pins = json.loads((HERE / 'source-pins.json').read_text())
    for path, expected in pins['sha256'].items():
        require(hashlib.sha256((root / path).read_bytes()).hexdigest() == expected,
                f'source drift: {path}')
    return pins


def options_for(requirement, candidates):
    """Value/family match only. No performance, tolerance or adoption verdict."""
    options = []
    for c in candidates:
        if (c['series'], c['family'], c['value']) != (requirement['series'], requirement['family'], requirement['value_si']):
            continue
        options.append({'candidate_mpn': c['candidate_mpn'], 'status': c['status'],
                        'candidate_distributor_identity': ({k: c['jlc'].get(k) for k in ('lcsc', 'model', 'brand')} if c['jlc'] else None),
                        'distributor_receipt': c['jlc_receipt'],
                        'manufacturer_spec_receipt': c['manufacturer_spec'],
                        'match_basis': 'SOURCE FAMILY AND VALUE ONLY',
                        'tolerance_compliance': 'NOT ESTABLISHED',
                        'adoption': 'UNADOPTED'})
    return options


def build(io, threading, families, instances, candidate_report, source_classifier):
    from scripts.schgen.core import designator
    instances_by_name = {i.name: i for i in instances}
    require(candidate_report['status'].startswith('UNADOPTED'), 'candidate source is not UNADOPTED')
    refs = {ref for r in threading['latch']['not_shown'] for ref in r['neighbours']}
    physical = {p['ref']: p for p in io['physical_packages']}
    units = {}
    for u in io['package_units']:
        units.setdefault(u['ref'], []).append(u)
    family_parts = {f.name: {p.key: p for p in f.parts} for f in families}
    classifier = {}
    for series, family, value in source_classifier.groups():
        require(series not in classifier or classifier[series] == family, 'ambiguous classifier family')
        classifier[series] = family
    rows = []
    for ref in sorted(refs):
        pkg = physical[ref]
        if pkg['mpn']:
            continue
        require(len(units[ref]) == 1, f'ambiguous units: {ref}')
        u = units[ref][0]
        key = u['logical_key']
        part = family_parts[pkg['family']][key]
        instance = instances_by_name[pkg['instance']]
        require(instance.family == pkg['family'] and designator(part, instance) == ref,
                f'instance/ref mapping mismatch: {ref}')
        require(not part.attributes.get('MPN'), f'identity changed: {ref}')
        require(part.attributes.get('Role') == u['role'], f'role mismatch: {ref}')
        require(part.symbol.split(':')[-1] == pkg['symbol'] and part.footprint == pkg['footprint'],
                f'symbol/footprint mismatch: {ref}')
        symbol = pkg['symbol']
        series = None
        if symbol.startswith('RC0603FR'):
            series, value = 'RC0603FR-07', source_classifier.ohms(part.value)
        elif symbol.startswith('RT0603BRD'):
            series, value = 'RT0603BRD07', source_classifier.ohms(part.value)
        elif symbol.startswith('C0603C101'):
            series, value = 'C0603C-J5GACTU', source_classifier.farads(part.value)
        else:
            value = None
        family = classifier.get(series)
        # Do not infer an electrical tolerance requirement from Role or symbol.
        tolerance_attrs = {k: v for k, v in part.attributes.items() if 'tolerance' in k.lower()}
        require(not tolerance_attrs, f'explicit tolerance needs reviewed parser: {ref}')
        req = {'ref': ref, 'instance': pkg['instance'], 'source_family': pkg['family'],
               'logical_key': key, 'role': u['role'], 'symbol': symbol,
               'footprint': pkg['footprint'], 'value_text': part.value, 'value_si': value,
               'value_unit': 'F' if ref.startswith('C') else 'ohm',
               'series': series, 'family': family, 'required_tolerance_percent': None,
               'required_tolerance_status': 'NOT DECLARED IN MATCHED PART ATTRIBUTES'}
        opts = options_for(req, candidate_report['value_only_candidates']) if family and value is not None else []
        if family and value is not None:
            # Candidate MPN construction here checks existing records; never adds options.
            expected = source_classifier.candidate(series, value)
            require(all(o['candidate_mpn'] == expected for o in opts), f'candidate MPN/value conflict: {ref}')
        rows.append({'requirement': req, 'options': opts, 'selected_mpn': None,
                     'status': 'UNADOPTED OPTIONS' if opts else 'NO EXACT FAMILY/VALUE OPTION IN RETAINED REPORT',
                     'physical_access_verdict': 'NOT SHOWN'})
    require(len(rows) == 27, 'blank-MPN coverage changed')
    return {'schema_version': 1, 'scope': 'SOURCE-ONLY OPTIONS; NO SELECTION OR COMPLIANCE CLAIM',
            'candidate_observation_date': candidate_report['retrieved'],
            'rows': rows, 'counts': {'references': len(rows),
                'with_existing_options': sum(bool(r['options']) for r in rows),
                'without_existing_options': sum(not r['options'] for r in rows)},
            'warning': 'Dated catalog identities are not current stock/price evidence. Required tolerance and all other circuit ratings need independent review.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.parse_args()
    try:
        pins = verify_sources(ROOT)
        from design.spec.instrument import specification
        from scripts.checks import passive_candidates
        families, instances = specification()
        report = build(json.loads((ROOT / 'design/reports/io-partition.json').read_text()),
                       json.loads((ROOT / 'design/stack/fixings/threading-procedure.json').read_text()),
                       families, instances,
                       json.loads((ROOT / 'design/readiness/bom-cost-evidence.json').read_text()),
                       passive_candidates)
        report['source_commit'] = pins['source_commit']
        report['engineering_commit'] = pins['engineering_commit']
        report['procedure_amendment'] = pins['procedure_amendment']
        report['source_sha256'] = pins['sha256']
        print(json.dumps(report, indent=2))
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        p.exit(1, f'MC02 passive options refused: {exc}\n')


if __name__ == '__main__':
    main()
