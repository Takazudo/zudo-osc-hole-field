"""Fail-closed current-epoch gap inventory for fitted convex SMD AGND sources.

This reports nominal source geometry and missing physical inputs. It does not
compute a flux coefficient, admit a manufactured foil slab, or approve #38.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.convex_source_flux import domain_bounds


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.circuit-cache/issue38-recovery/current-own-source-boundary-v6.json'
SOURCE_SHA256 = 'a5bbda74de40c39dc21427aece3dc0a12857eb8c4f8257280dd8c9ab525b5d81'
CONVEX_HELPER = ROOT / 'scripts/pcbgen/convex_source_flux.py'
EXPECTED = {
    'osc-jack-left': 886,
    'osc-jack-right': 691,
    'osc-core': 1889,
    'osc-control': 94,
    'osc-stage-optical': 60,
}
MISSING = (
    'Actual continuous convex drill-free foil slab under the complete possible source support, including etch and registration envelope',
    'Selected contained reference-profile patch with proved positive minimum area and geometric containment',
    'Positive physical foil-height interval, with minimum and maximum values',
    'Maximum resistivity for the declared hot operating condition and material/process envelope',
    'Current and redistribution class qualification, with face-correct normal trace and joined primal/dual construction',
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_source(path=SOURCE):
    path = Path(path)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('reviewed v6 aggregate bytes changed; select and review a new source epoch')
    source = json.loads(raw)
    if source.get('own_source_contact_count') != 4143 or source.get('family_counts') != {
        'PTH': 305, 'SMD_drill_overlap_unresolved': 218, 'convex_SMD': 3620,
    }:
        raise ValueError('reviewed complete source family split changed')
    dependencies = source['source_sha256']
    if not dependencies or not isinstance(dependencies, dict):
        raise ValueError('missing current-source dependency closure')
    for name, wanted in dependencies.items():
        file = Path(name)
        if not file.is_absolute() or not file.is_relative_to(ROOT):
            raise ValueError('source dependency outside project: ' + name)
        if digest(file) != wanted:
            raise ValueError('current-source dependency changed: ' + name)
    if digest(path) != SOURCE_SHA256:
        raise ValueError('aggregate changed during dependency admission')
    return source


def classify(row):
    if row.get('family') != 'convex_SMD' or row.get('net') != 'AGND':
        raise ValueError('not a convex AGND own source')
    if row.get('physical_support_qualified') is not False:
        raise ValueError('unexpected physical support claim')
    if row.get('face') not in ('F.Cu', 'B.Cu') or row.get('native_layers') != [row['face']]:
        raise ValueError('source needs one exact external foil face')
    if set(row.get('nearby_drill_uuids', [])) != set(row.get('drill_separation', {})):
        raise ValueError('nearby drill proof is incomplete')
    if row.get('actual_or_unproved_drill_uuids') or any(
        item.get('status') != 'proved disjoint' for item in row.get('drill_separation', {}).values()
    ):
        raise ValueError('unresolved drill enters convex source class')
    lower, upper, diameter2 = domain_bounds(row['primitive'])
    rational = lambda value: [value.numerator, value.denominator]
    if row.get('area_mm2_rational_bounds') != [rational(lower), rational(upper)]:
        raise ValueError('source area bound differs from current convex primitive')
    if row.get('diameter_squared_mm2_rational_upper') != rational(diameter2):
        raise ValueError('source diameter bound differs from current convex primitive')
    if not all(isinstance(row.get(key), str) and row[key] for key in ('ref', 'pad', 'uuid')):
        raise ValueError('source identity incomplete')
    return {
        'ref': row['ref'], 'pad': row['pad'], 'uuid': row['uuid'],
        'face': row['face'], 'primitive': row['primitive'],
        'area_mm2_rational_bounds': row['area_mm2_rational_bounds'],
        'diameter_squared_mm2_rational_upper': row['diameter_squared_mm2_rational_upper'],
        'coefficient_status': 'BLOCKED_PHYSICAL_SOURCE_INPUTS',
        'net_to_uniform_profile_energy_ohm_upper': None,
        'unit_normalized_redistribution_energy_ohm_upper': None,
        'missing_admissions': list(MISSING),
    }


def inventory(path=SOURCE):
    helper_sha=digest(__file__)
    convex_sha=digest(CONVEX_HELPER)
    source = checked_source(path)
    boards = []
    seen = set()
    for board in source['boards']:
        bid = board['board_id']
        if bid not in EXPECTED or any(item['board_id'] == bid for item in boards):
            raise ValueError('duplicate or unexpected current board')
        selected = [row for row in board['own_source_contacts'] if row['family'] == 'convex_SMD']
        if len(selected) != EXPECTED[bid] or board['family_counts'].get('convex_SMD') != len(selected):
            raise ValueError('board convex source population differs: ' + bid)
        rows = []
        for row in selected:
            key = (row['ref'], row['pad'])
            if key in seen:
                raise ValueError('duplicate source contact: ' + str(key))
            seen.add(key)
            rows.append(classify(row))
        boards.append({'board_id': bid, 'count': len(rows), 'contacts': rows})
    if set(item['board_id'] for item in boards) != set(EXPECTED) or len(seen) != 3620:
        raise ValueError('incomplete current convex population')
    counts = Counter(row['face'] for board in boards for row in board['contacts'])
    if digest(path) != SOURCE_SHA256:
        raise ValueError('aggregate changed during classification')
    for name, wanted in source['source_sha256'].items():
        if digest(name) != wanted:
            raise ValueError('current-source dependency changed during classification: ' + name)
    if digest(__file__) != helper_sha or digest(CONVEX_HELPER) != convex_sha:
        raise ValueError('convex source classifier changed during inventory')
    return {
        'status': 'BLOCKED nominal convex source geometry only; physical/electrical acceptance NOT ACCEPTED',
        'reviewed_source': str(Path(path).resolve()),
        'reviewed_source_sha256': SOURCE_SHA256,
        'helper_sha256': helper_sha,
        'convex_source_flux_sha256': convex_sha,
        'source_dependency_sha256': source['source_sha256'],
        'contact_count': len(seen), 'face_counts': dict(counts),
        'boards': boards,
        'scope': 'All 3620 current v6 fitted drill-free convex own AGND pad sections. No actual foil, support, material, flux-class, joined or physical qualification.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('fresh output required')
    report = inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(report['status'], report['contact_count'], report['face_counts'])
