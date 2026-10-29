"""Pinned source distinction, not hardware equivalence or packing adoption.

Run: python3 scripts/checks/h_packing_contract.py --variants <after-directory>
The optional CSV check does not generate CAD or alter either configuration.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name('fixtures') / 'h-packing-contract.json'
AMP_MAPS = (('1', '2', '3'), ('7', '6', '5'), ('8', '9', '10'), ('14', '13', '12'))
DEVICES = {'OPA4196IDR', 'OPA4197IPWR', 'TL074HIDR'}


def channel(instance, ref, unit, device, pins):
    nets = [pins[k] for k in AMP_MAPS[unit - 1]]
    spare = nets[0] == nets[1] and nets[0] is not None and nets[2] == 'AGND'
    return {'instance': instance, 'ref': ref, 'unit': unit, 'device': device,
            'spare': spare, 'nets': ['GROUNDED_FOLLOWER'] if spare else nets}


def ordered(rows):
    return sorted(rows, key=lambda r: (r['instance'], r['ref'], r['unit']))


def repository_snapshot():
    sys.path.insert(0, str(ROOT))
    from design.spec.modules.sample_hold import specification
    from scripts.schgen.core import designator
    families, instances = specification()
    family = families[0]
    rows, packages, supplies = [], set(), []
    for instance in instances:
        for part in family.parts:
            if part.prefix != 'U':
                continue
            ref = designator(part, instance)
            packages.add((instance.name, ref))
            if part.value in DEVICES:
                if part.unit in range(1, 5):
                    row = channel(instance.name, ref, part.unit, part.value, part.pins)
                    row['region'] = part.attributes.get('BoardRegion')
                    rows.append(row)
                elif part.unit == 5:
                    supplies.append({'instance': instance.name, 'ref': ref, 'unit': 5,
                                     'pins': dict(part.pins)})
    return {'ic_packages': len(packages), 'channels': ordered(rows), 'supplies': ordered(supplies)}


def candidate_snapshot(directory):
    with (directory / 'candidate-bom.csv').open() as f:
        selected = [r for r in csv.DictReader(f) if r['instance'] in ('H1', 'H2') and r['ref'].startswith('U')]
    bom = {(r['instance'], r['ref']): r for r in selected}
    if len(bom) != len(selected):
        raise ValueError('duplicate candidate IC package')
    units, scopes = {}, {}
    with (directory / 'candidate-pin-map.csv').open() as f:
        for r in csv.DictReader(f):
            key = (r['instance'], r['ref'])
            if key not in bom:
                continue
            ukey = (*key, int(r['unit']))
            pins = units.setdefault(ukey, {})
            if r['pin'] in pins:
                raise ValueError('duplicate candidate pin')
            pins[r['pin']] = r['resolved_label'] if r['state'] == 'NET' else None
            scopes.setdefault(ukey, {})[r['pin']] = (r['state'], r['net_scope'])
    rows, supplies = [], []
    for (instance, ref, unit), pins in units.items():
        device = bom[instance, ref]['mpn'] or bom[instance, ref]['value']
        if device not in DEVICES:
            continue
        if unit in range(1, 5):
            row = channel(instance, ref, unit, device, pins)
            row['pin_scopes'] = {k: list(scopes[instance, ref, unit][k]) for k in AMP_MAPS[unit - 1]}
            rows.append(row)
        elif unit == 5:
            supplies.append({'instance': instance, 'ref': ref, 'unit': 5, 'pins': pins})
    return {'ic_packages': len(bom), 'channels': ordered(rows), 'supplies': ordered(supplies)}


def validate(actual, expected, label):
    for field in ('ic_packages', 'channels', 'supplies'):
        if actual[field] != expected[field]:
            raise ValueError(f'{label}: {field} drift; review source lineage, do not auto-update fixture')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variants', type=Path)
    args = parser.parse_args()
    fixture = json.loads(FIXTURE.read_text())
    validate(repository_snapshot(), fixture['repository'], 'repository')
    if args.variants:
        for variant, expected in fixture['variants'].items():
            validate(candidate_snapshot(args.variants / variant / 'candidate/source-records'), expected, variant)
    print('PASS: pinned H1/H2 source distinction; analog/physical equivalence NOT CHECKED; candidate CSVs ' + ('checked' if args.variants else 'not supplied'))


if __name__ == '__main__':
    main()
