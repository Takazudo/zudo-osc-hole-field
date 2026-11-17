"""Exact selected cable interval comparison, never hardware qualification."""
import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).with_name('evidence.json')
SELECTED = {'C26618': 18, 'C29534': 28, 'C32128': 3, 'C68390': 9, 'C81339': 3}
LINK_FILE = 'design/stack/geometry/links/link-gate.json'
LINK_SHA = '1c091c1d6d4b9c000f770a0e604cb986d5c55e44cb77ea22083249afbf5cdb0d'
SOURCE_PINS = {
    'FH12': '9f056f58ff000739633cc3cb7697ba185967083dcf1429b7ab10783b3f55bac5',
    'C26618': '1866c1e6ca5591efe2aa1d1ccfcf58a3384c620ee7db50b9019a2974d30d62a8',
    'C29534': '23fff3c7a1fc0cb63ccea9ee542d442c1c2da9edbb6d591f80211f10173b699e',
    'C32128': '1866c1e6ca5591efe2aa1d1ccfcf58a3384c620ee7db50b9019a2974d30d62a8',
    'C68390': '93f731b7083d21c2bc5279adfd0037184c91c1ea07296ca71f767901ca9bfb4e',
    'C81339': '2549f2f79ecbb7fdad0fc25c8e4480adb2bcfcd4bafe32b6925275c3a22fac9b',
}
EXPECTED_SCOPE = {code: ('generic' if code in ('C26618', 'C32128') else 'exact') for code in SELECTED}
FIELDS = ('tail_thickness', 'total_width', 'exposed_length', 'support_length', 'stiffener_thickness', 'finish')


def interval(record):
    if record['unit'] != 'mm':
        raise ValueError('expected explicit mm units')
    values = []
    for key in ('lower', 'upper'):
        value = record[key]
        if value is None:
            values.append(None)
            continue
        if not isinstance(value, str):
            raise ValueError('decimal endpoints must be strings')
        try:
            value = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError('invalid decimal endpoint') from exc
        if not value.is_finite() or value < 0:
            raise ValueError('nonfinite/negative endpoint')
        values.append(value)
    lower, upper = values
    if lower is None or (upper is not None and upper < lower):
        raise ValueError('invalid interval bounds')
    return lower, upper


def compare_interval(declared, target):
    lo, hi = interval(declared)
    minimum, maximum = interval(target)
    if hi is None:
        return {'verdict': 'UNSOURCED', 'reason': 'declared upper tolerance is absent'}
    low_shortfall = max(Decimal(0), minimum-lo)
    high_excess = max(Decimal(0), hi-maximum) if maximum is not None else Decimal(0)
    return {'verdict': 'DECLARED_INTERVAL_NOT_CONTAINED' if low_shortfall or high_excess
            else 'WITHIN_DECLARED_INTERVAL',
            'lower_shortfall_mm': str(low_shortfall), 'upper_excess_mm': str(high_excess)}


def compare(code, cable, connector):
    exact = cable['source']['scope'] == 'exact' and cable['source'].get('order_code') == code
    rows = []
    for field in FIELDS:
        requirement = connector['criteria'][field]
        datum = cable['dimensions'].get(field)
        row = {'field': field, 'comparator_class': requirement['class'],
               'connector_source_sha256': connector['source']['sha256'],
               'connector_locator': requirement['locator'],
               'cable_source_sha256': cable['source']['sha256'],
               'cable_locator': cable['source']['locator'], 'declared': datum}
        target = requirement.get('by_contacts', {}).get(str(cable['selected_contacts']), requirement.get('value'))
        row['comparator'] = target
        if not exact or datum is None:
            row.update(verdict='UNSOURCED', reason='exact selected-code datum unavailable' if not exact
                       else 'exact drawing does not state this datum')
        elif field == 'stiffener_thickness' and datum.get('lower') is None:
            if datum.get('unit') != 'mm':
                raise ValueError('expected explicit mm units')
            row.update(verdict='UNSOURCED', reason='nominal thickness is stated but no guaranteed lower bound is given')
        elif field == 'finish':
            row['verdict'] = 'MATCHING_STATED_FINISH' if datum == target else 'DIFFERENT_STATED_FINISH'
        else:
            row.update(compare_interval(datum, target))
        if field == 'support_length':
            row['scope_condition'] = 'Numeric comparison conditional on the drawn end-support datum mapping; not mating qualification'
        rows.append(row)
    return rows


def audit(evidence, root=ROOT):
    raw = (root / LINK_FILE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != LINK_SHA:
        raise ValueError('selected-link source pin changed')
    links = [r for r in json.loads(raw)['links'] if r.get('placed')]
    counts = Counter(r['cable'] for r in links)
    if counts != SELECTED or set(evidence['cables']) != set(SELECTED):
        raise ValueError('exact selected cable set/count changed')
    for code, source in [('FH12', evidence['connector']['source'])] + [
            (code, cable['source']) for code, cable in evidence['cables'].items()]:
        if source['sha256'] != SOURCE_PINS[code]:
            raise ValueError('reviewed source pin changed: '+code)
        if code != 'FH12':
            expected = EXPECTED_SCOPE[code]
            if source['scope'] != expected or source.get('order_code') != (code if expected == 'exact' else None):
                raise ValueError('reviewed source applicability changed: '+code)
    results = []
    for code, cable in sorted(evidence['cables'].items()):
        chosen = [r for r in links if r['cable'] == code]
        if any(r['circuits'] != cable['selected_contacts'] for r in chosen):
            raise ValueError('selected conductor count mismatch: '+code)
        results.append({'code': code, 'link_count': len(chosen), 'link_ids': [r['id'] for r in chosen],
                        'source_scope': cable['source']['scope'],
                        'source_description': cable['source']['description'],
                        'comparisons': compare(code, cable, evidence['connector'])})
    return {'engineering_commit': '2c53715d49a4a7639723595590d1fd4eeb3a3c1f',
            'selected_link_sha256': LINK_SHA, 'links': len(links), 'cables': results,
            'scope': 'Reviewed document interval arithmetic only; raw PDFs not re-fetched by this audit. No all-cable compatibility, hardware adoption, mounted fit, access, contact-1 or manufacturing acceptance.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(audit(json.loads(EVIDENCE.read_text())), indent=2))


if __name__ == '__main__':
    main()
