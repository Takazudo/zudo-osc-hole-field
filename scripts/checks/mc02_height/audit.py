#!/usr/bin/env python3
"""Offline candidate evidence audit. Never computes an assembled access verdict."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verified_bytes(path, expected):
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected, f'source drift: {path}')
    return data


def murata_fields(data):
    fields = {x['id']: x for x in data['productSearchResult'][0]['itemInfoList']}
    # Public API fields contain an array of values; keep raw and display distinct.
    return fields


def audit(manifest, threading, packages, murata):
    links = {r['link']: r['neighbours'] for r in threading['latch']['not_shown']}
    require(len(links) == len(threading['latch']['not_shown']), 'duplicate link')
    require(links == manifest['expected_links'], 'latch reference set changed')
    by_ref = {p['ref']: p for p in packages['physical_packages']}
    refs = sorted({ref for values in links.values() for ref in values})
    require(set(refs) == set(manifest['expected_refs']), 'reference coverage changed')
    # Validate exact known response structure and preserve the inconsistent max field.
    fields = murata_fields(murata)
    require('GRM188R71H104KA93D' in
            [v['value'] for v in fields['partNumWithPackageCode']['valueList']],
            'Murata exact suffix absent')
    values = lambda key: fields[key]['valueList']
    thickness = values('thickness')[0]
    maximum = values('thicknessMax')[0]
    require(thickness['displayName'] == '0.8mm ±0.1mm', 'Murata tolerance changed')
    require(maximum['value'] == '0.8' and maximum['displayName'] == '0.9mm',
            'Murata raw/display conflict changed; review required')
    require((manifest['groups']['GRM188R71H104KA93D']['body_min_mm'],
             manifest['groups']['GRM188R71H104KA93D']['body_max_mm']) == (0.7, 0.9),
            'Murata derived bound changed; raw max cannot be adopted')
    rows = []
    for ref in refs:
        require(sum(p['ref'] == ref for p in packages['physical_packages']) <= 1,
                f'duplicate package: {ref}')
        p = by_ref.get(ref)
        require(p is not None, f'missing package: {ref}')
        expected = manifest['expected_refs'][ref]
        require(all(p[k] == expected[k] for k in ('mpn', 'footprint')), f'identity drift: {ref}')
        mpn = p['mpn']
        row = {'ref': ref, 'mpn': mpn, 'footprint': p['footprint'],
               'classification': 'unresolved_identity', 'body_min_mm': None,
               'body_max_mm': None, 'mounted_height_mm': None}
        if mpn:
            require(mpn in manifest['groups'], f'unsupported MPN: {mpn}')
            e = manifest['groups'][mpn]
            row.update(classification=e['identity_scope'], body_min_mm=e['body_min_mm'],
                       body_max_mm=e['body_max_mm'], source=e['source'], locator=e['locator'])
        rows.append(row)
    counts = {name: sum(r['classification'] == name for r in rows)
              for name in ('exact', 'conditional_suffix', 'unresolved_identity')}
    require(counts == {'exact': 59, 'conditional_suffix': 2, 'unresolved_identity': 27},
            'coverage counts changed')
    return {'schema_version': 1, 'source_commit': manifest['source_commit'],
            'scope': 'BODY DIMENSION EVIDENCE CANDIDATES ONLY; NOT MOUNTED CLEARANCE',
            'access_verdict': 'NOT SHOWN', 'counts': counts, 'references': rows,
            'source_sha256': manifest['pins'], 'murata_sha256': manifest['murata_sha256'],
            'links': [{'link': link, 'neighbours': neighbours, 'access_verdict': 'NOT SHOWN',
                       'coverage': {name: sum(r['ref'] in neighbours and r['classification'] == name
                                             for r in rows) for name in counts}}
                      for link, neighbours in sorted(links.items())],
            'murata_conflict': {'raw_max': maximum['value'], 'display_max': maximum['displayName'],
                               'derivation': '0.8 ±0.1 mm display tolerance; raw max NOT USED'}}


def run(root, murata_path):
    manifest = json.loads((HERE / 'evidence.json').read_text())
    data = {p: verified_bytes(root / p, sha) for p, sha in manifest['pins'].items()}
    murata = json.loads(verified_bytes(murata_path, manifest['murata_sha256']))
    return audit(manifest, json.loads(data['design/stack/fixings/threading-procedure.json']),
                 json.loads(data['design/reports/io-partition.json']), murata)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--murata-source', type=Path, required=True,
                   help='Previously retained official API JSON, verified by SHA256; never downloaded')
    args = p.parse_args()
    try:
        print(json.dumps(run(args.root, args.murata_source), indent=2))
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        p.exit(1, f'MC02 evidence audit refused: {exc}\n')


if __name__ == '__main__':
    main()
