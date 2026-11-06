#!/usr/bin/env python3
"""Exact-identity candidates for value-only passives and BOM part-cost evidence.

Inputs are the instrument specification plus retained read-only catalog bytes in
.circuit-cache/sources/readiness-20261031/ (git-ignored):

- jlc/<keyword>.json: public JLC parts-search responses, 2026-10-31;
- spec/<MPN>.pdf: manufacturer spec sheets from yageogroup.com (Yageo/KEMET).

Candidates are UNADOPTED. Nothing here enters the inventory, the schematic or an
order file. Distributor rows establish order identity, price tier and stock only.
"""
import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification  # noqa: E402
from scripts.checks.bom_readiness import build as bom_build  # noqa: E402

CACHE = ROOT / '.circuit-cache/sources/readiness-20261031'
OUTPUT = ROOT / 'design/readiness/bom-cost-evidence.json'
RETRIEVED = '2026-10-31'
JLC_URL = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
SPEC_URL = 'https://www.yageogroup.com/component-documentation/download/specsheet/'
LOT = 5
# JLC returns generic "JLCPCB Assembly" C99... rows for consigned/unlisted parts;
# their fixed price is a service placeholder, not a part offer.
PLACEHOLDER_BRAND = 'JLCPCB Assembly'


def ohms(value):
    m = re.fullmatch(r'([0-9.e+]+)\s*(k|M)?\s*Ω', value.strip())
    return float(m[1]) * {None: 1, 'k': 1e3, 'M': 1e6}[m[2]] if m else None


def farads(value):
    m = re.fullmatch(r'([0-9.e+-]+)\s*(pF|nF|µF|F)', value.replace(' C0G', '').strip())
    return float(m[1]) * {'pF': 1e-12, 'nF': 1e-9, 'µF': 1e-6, 'F': 1}[m[2]] if m else None


def yageo_code(x):
    for unit, div in (('M', 1e6), ('K', 1e3), ('R', 1)):
        if x >= div or unit == 'R':
            s = f'{x / div:.4g}'
            return s.replace('.', unit) if '.' in s else s + unit


def kemet_code(f):
    pf = round(f * 1e12, 6)
    exp = 0
    while pf >= 100:
        pf /= 10
        exp += 1
    return f'{int(round(pf)):02d}{exp}'


def groups():
    families, instances = specification()
    copies = collections.Counter(i.family for i in instances)
    out = collections.defaultdict(lambda: {'qty': 0, 'roles': collections.Counter()})
    for family in families:
        packages = {}
        for part in family.parts:
            packages.setdefault(part.key.rsplit('.', 1)[0] if part.prefix == 'U' else part.key, part)
        for part in packages.values():
            if (part.abstract or not part.in_bom or part.dnp or part.attributes.get('MPN')
                    or part.prefix.startswith('#')):
                continue
            symbol = part.symbol.split(':')[-1]
            if symbol.startswith('RC0603FR'):
                key = ('RC0603FR-07', 'Yageo RC0603 1% thick film (r_general symbol)', ohms(part.value))
            elif symbol.startswith('RT0603BRD'):
                key = ('RT0603BRD07', 'Yageo RT0603 0.1% thin film (r_precision symbol)', ohms(part.value))
            elif symbol.startswith('C0603C101'):
                key = ('C0603C-J5GACTU', 'KEMET C0603 C0G 50 V 5% (c_small symbol)', farads(part.value))
            elif symbol.startswith('GRM188R71H104'):
                key = ('GRM188R7', 'Murata GRM188 X7R (c_bypass symbol)', farads(part.value))
            elif symbol.startswith('TC33X'):
                key = ('TC33X-2', 'Bourns TC33X trimmer (trim symbol)', ohms(part.value))
            else:
                key = (symbol, symbol, part.value)
            out[key]['qty'] += copies[family.name]
            out[key]['roles'][part.attributes.get('Role', '')] += copies[family.name]
    return out


def candidate(series, value):
    if series in ('RC0603FR-07', 'RT0603BRD07'):
        return f'{series}{yageo_code(value)}L'
    if series == 'C0603C-J5GACTU':
        return f'C0603C{kemet_code(value)}J5GACTU' if value <= 10e-9 else None
    if series == 'TC33X-2':
        return {2e4: 'TC33X-2-203E', 5e4: 'TC33X-2-503E', 5e5: 'TC33X-2-504E'}.get(value)
    if series == 'GRM188R7' and value == 1e-6:
        return 'GRM188R71E105KA12D'
    return None


def jlc_row(keyword):
    path = CACHE / 'jlc' / (keyword.replace('/', '_').replace(',', '_') + '.json')
    if not path.exists():
        return None, None
    raw = path.read_bytes()
    rows = ((json.loads(raw).get('data') or {}).get('componentPageInfo') or {}).get('list') or []
    norm = lambda s: (s or '').replace('/', '_').replace(',', '_').upper()
    hits = [r for r in rows if norm(r.get('componentModelEn')) == norm(keyword) or r.get('componentCode') == keyword]
    receipt = {'url': JLC_URL, 'keyword': keyword, 'retrieved': RETRIEVED,
               'response_sha256': hashlib.sha256(raw).hexdigest()}
    if not hits:
        return None, receipt
    r = hits[0]
    return {'lcsc': r['componentCode'], 'model': r['componentModelEn'], 'brand': r['componentBrandEn'],
            'library_type': r.get('componentLibraryType'), 'stock': r.get('stockCount'),
            'tiers': [[p['startNumber'], p['endNumber'], p['productPrice']] for p in r.get('componentPrices') or []],
            'describe': r.get('describe')}, receipt


def tier_price(tiers, qty):
    for start, end, price in tiers:
        if qty >= start and (end == -1 or qty <= end):
            return price
    return None


def priced(row, qty):
    if not row or row['brand'] == PLACEHOLDER_BRAND or not row['tiers']:
        return None
    unit, lot = tier_price(row['tiers'], qty), tier_price(row['tiers'], qty * LOT)
    if unit is None or lot is None:
        return None
    return {'unit_price_usd': unit, 'lot_unit_price_usd': lot,
            'per_unit_usd': round(qty * unit, 4), 'per_lot_usd': round(qty * LOT * lot, 4),
            'stock': row['stock'], 'stock_covers_lot': row['stock'] >= qty * LOT}


def spec_receipt(mpn):
    path = CACHE / 'spec' / f'{mpn}.pdf'
    if not path.exists():
        return None
    raw = path.read_bytes()
    return {'url': SPEC_URL + mpn, 'retrieved': RETRIEVED, 'sha256': hashlib.sha256(raw).hexdigest(),
            'authority_class': 'MANUFACTURER_PRIMARY', 'extract': 'Exact MPN printed in the spec sheet; values and ratings not yet promoted to an owner bundle'}


def build():
    bom = bom_build()
    exact = []
    for line in bom['lines']:
        if line['mpn'] == 'TEST_PAD_D1.5MM':
            continue
        row, receipt = jlc_row(line['lcsc'] or line['mpn'])
        cost = priced(row, line['qty_per_unit'])
        exact.append({'mpn': line['mpn'], 'qty_per_unit': line['qty_per_unit'], 'jlc': row, 'receipt': receipt,
                      'cost': cost, 'status': ('PRICED' if cost and cost['stock'] else 'PRICED, STOCK 0' if cost
                                               else 'UNKNOWN: no exact distributor row' if not row
                                               else 'UNKNOWN: JLC placeholder row only')})
    cands = []
    for (series, family, value), g in sorted(groups().items(), key=lambda x: (-x[1]['qty'], x[0][0], x[0][2] or 0)):
        mpn = candidate(series, value)
        row, receipt = jlc_row(mpn) if mpn else (None, None)
        spec = spec_receipt(mpn) if mpn else None
        cost = priced(row, g['qty'])
        if not mpn:
            status = 'UNKNOWN: no candidate in this family; dielectric or value is a design decision'
        elif not row or row['brand'] == PLACEHOLDER_BRAND:
            status = ('UNKNOWN: exact MPN not found at JLC or as a Yageo spec sheet; nearest-value substitution is a design decision'
                      if not spec else 'UNKNOWN: manufacturer spec exists, no JLC offer')
        elif not spec and series != 'TC33X-2':
            status = 'CANDIDATE: distributor identity only (manufacturer sheet not retained)'
        else:
            status = 'CANDIDATE: distributor identity and manufacturer spec' if row['stock'] else 'CANDIDATE: identity confirmed, JLC stock 0'
        if series == 'TC33X-2' and row:
            spec = {'source': 'component-passives-family src-trim-103-datasheet (Bourns TC33 series, retained)'}
        cands.append({'series': series, 'family': family, 'value': value, 'qty_per_unit': g['qty'],
                      'qty_per_lot': g['qty'] * LOT, 'roles': dict(g['roles'].most_common(4)),
                      'candidate_mpn': mpn, 'status': status, 'jlc': row, 'jlc_receipt': receipt,
                      'manufacturer_spec': spec, 'cost': cost})
    def total(rows):
        known = [r for r in rows if r['cost']]
        return {'per_unit_usd': round(sum(r['cost']['per_unit_usd'] for r in known), 2),
                'per_lot_usd': round(sum(r['cost']['per_lot_usd'] for r in known), 2),
                'priced_placements_per_unit': sum(r['qty_per_unit'] for r in known),
                'unpriced_placements_per_unit': sum(r['qty_per_unit'] for r in rows if not r['cost']),
                'unpriced_lines': [r.get('mpn') or r.get('candidate_mpn') or f"{r['series']} {r['value']}" for r in rows if not r['cost']]}
    return {
        'schema_version': 1,
        'status': 'UNADOPTED candidates and dated catalog observations; not a quote, order or fabrication BOM',
        'retrieved': RETRIEVED, 'lot_units': LOT, 'currency': 'USD (JLC catalog tier price, tax/shipping/assembly excluded)',
        'tier_rule': 'Unit cost uses the tier containing the per-unit quantity; lot cost uses the tier containing 5x that quantity',
        'exact_lines': exact, 'exact_total': total(exact),
        'value_only_candidates': cands, 'candidate_total': total(cands),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not (CACHE / 'jlc').exists():
        print(f'NOT RUN: retained catalog cache {CACHE.relative_to(ROOT)} is absent')
        raise SystemExit(4)
    text = json.dumps(build(), indent=1, ensure_ascii=False) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            raise SystemExit('bom-cost-evidence.json is stale')
        print('PASS: bom-cost-evidence.json current')
        return
    OUTPUT.write_text(text)
    d = json.loads(text)
    for k in ('exact_total', 'candidate_total'):
        t = d[k]
        print(k, t['per_unit_usd'], t['per_lot_usd'], t['priced_placements_per_unit'], t['unpriced_placements_per_unit'])


if __name__ == '__main__':
    main()
