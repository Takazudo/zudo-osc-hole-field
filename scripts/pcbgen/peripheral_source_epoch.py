"""Prove named source-only transitions without rebinding native/model evidence."""
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from scripts.libgen.gen_ic_package_envelopes import owned_model_span
from scripts.pcbgen.generate_peripheral_ground import generate
from scripts.checks.io_partition60 import power_requirements, repacking_metadata

BASE = Path('design/partition/peripheral-ground-feasibility')
PRIOR = Path('design/partition/peripheral-source-epoch-20261001.json')
DISPLAY_EPOCH = Path('design/partition/peripheral-source-epoch-20261002.json')
OUTPUT = Path('design/partition/peripheral-source-epoch-20261002-power-metadata.json')
COMMIT = 'fa11636b860ef80c01cb42bc7450551db556c72e'
METADATA_BASE = '38153f8d51db8852ab87e00aa94039f7981dc937'
IO = 'design/reports/io-partition.json'
FP = 'footprints/kicad/zudo-osc-hole-field.pretty/DIP-8_W7.62mm.kicad_mod'
MODEL = 'IC_DIP-8_W7.62mm.wrl'
CONTRACT = 'design/power/supply-architecture-input.json'
SUPPLY = 'design/power/supply-architecture.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def historical(path, commit=COMMIT):
    return subprocess.check_output(['git', 'show', f'{commit}:{path}'])


def prove_display_only(old_io, new_io, old_fp, new_fp):
    """Require byte-identical 2D footprint and a single report hash substitution."""
    geometries = []
    for raw in (old_fp, new_fp):
        text = raw.decode()
        start, end = owned_model_span(text, MODEL)
        geometries.append(text[:start] + text[end:])
    if geometries[0] != geometries[1]:
        raise ValueError('2D footprint geometry changed')
    old, new = json.loads(old_io), json.loads(new_io)
    expected = copy.deepcopy(old)
    matches = [r for r in expected['physical_packages'] if r['ref'] == 'U6101']
    if len(matches) != 1:
        raise ValueError('expected exactly one U6101 package')
    row = matches[0]
    if row['mpn'] != 'NOISE2' or row['footprint'] != 'zudo-osc-hole-field:DIP-8_W7.62mm':
        raise ValueError('unexpected U6101 identity')
    if row['courtyard']['footprint_sha256'] != sha(old_fp):
        raise ValueError('historical footprint hash mismatch')
    row['courtyard']['footprint_sha256'] = sha(new_fp)
    if expected != new:
        raise ValueError('IO report changed beyond the U6101 display footprint hash')


def prove_power_metadata_only(old_io, new_io, contract, supply):
    """Require the exact source-driven metadata replacement; compare all else."""
    expected = json.loads(old_io)
    expected.pop('added_fitted_quads')
    expected.pop('rail_change')
    expected.update(repacking_metadata(
        {r['ref']: r for r in expected['physical_packages']}, expected['package_units']))
    power = power_requirements(contract, supply)
    for row in expected['allowed_crossings']:
        if row['net'] not in power:
            continue
        fields = power[row['net']]
        if row['capacitance_F']['whole_domain_nominal_ceiling'] != fields['capacitance_F']:
            raise ValueError('capacitance contract changed beyond metadata scope')
        row['current_mA'] = fields['current_mA']
        row['capacitance_F']['status'] = 'board count and fitted/bulk totals are owned by the current partition report'
    if expected != json.loads(new_io):
        raise ValueError('IO report changed beyond the exact power/package metadata replacement')


def derive():
    prior_bytes = PRIOR.read_bytes()
    if prior_bytes != historical(str(PRIOR)):
        raise ValueError('historical epoch was modified')
    display_bytes = DISPLAY_EPOCH.read_bytes()
    if display_bytes != historical(str(DISPLAY_EPOCH), METADATA_BASE):
        raise ValueError('historical display epoch was modified')
    display = json.loads(display_bytes)
    if display['prior_epoch'] != {'path': str(PRIOR), 'sha256': sha(prior_bytes)}:
        raise ValueError('display epoch prior binding changed')
    old_io, display_io, new_io = historical(IO), historical(IO, METADATA_BASE), Path(IO).read_bytes()
    old_fp, display_fp, new_fp = historical(FP), historical(FP, METADATA_BASE), Path(FP).read_bytes()
    prove_display_only(old_io, display_io, old_fp, display_fp)
    if new_fp != display_fp:
        raise ValueError('footprint changed after the display epoch')
    inputs = {p: Path(p).read_bytes() for p in (CONTRACT, SUPPLY)}
    if any(raw != historical(p, METADATA_BASE) for p, raw in inputs.items()):
        raise ValueError('supply source changed beyond this metadata-only transition')
    prove_power_metadata_only(display_io, new_io, json.loads(inputs[CONTRACT]), json.loads(inputs[SUPPLY]))
    result = copy.deepcopy(display)
    result['scope'] = ('Exact source projection equivalence through the retained display epoch '
        'and the named power/package metadata correction. All other IO report values and '
        'the supply contract/report are unchanged. Historical native/model prerequisites remain stale.')
    result['prior_epoch'] = {'path': str(DISPLAY_EPOCH), 'sha256': sha(display_bytes)}
    result['metadata_comparison'] = {'commit': METADATA_BASE, 'report': IO,
        'historical_report_sha256': sha(display_io), 'current_report_sha256': sha(new_io),
        'unchanged_supply_sources': {p: sha(raw) for p, raw in inputs.items()}}
    with tempfile.TemporaryDirectory() as folder:
        for row in result['boards']:
            bid = row['board_id']
            raw = (BASE / (bid + '.receipt.json')).read_bytes()
            if sha(raw) != row['historical_receipt_sha256']:
                raise ValueError(f'{bid}: historical receipt changed')
            expected = json.loads(raw)
            if expected['source_sha256'][IO] != sha(old_io):
                raise ValueError(f'{bid}: historical IO report mismatch')
            if row['source_changes'][IO] != {'historical': sha(old_io), 'current': sha(display_io)}:
                raise ValueError(f'{bid}: display epoch IO binding changed')
            row['source_changes'][IO] = {'historical': sha(old_io), 'current': sha(new_io)}
            for path, change in row['source_changes'].items():
                if expected['source_sha256'][path] != change['historical'] or sha(Path(path).read_bytes()) != change['current']:
                    raise ValueError(f'{bid}: source hash mismatch: {path}')
                expected['source_sha256'][path] = change['current']
            target = Path(folder) / (bid + '.json')
            actual = generate(BASE / 'proposal.json', bid, target)
            if actual != expected or actual['model_entry_allowed']:
                raise ValueError(f'{bid}: source projection differs or model admitted')
            if actual['definition_sha256'] != row['unchanged_definition_sha256']:
                raise ValueError(f'{bid}: definition changed')
            row['current_source_receipt_sha256'] = sha(target.with_suffix('.receipt.json').read_bytes())
    result['latest_source_audit'] = ('Source projection only; exact historical receipt equality '
        'except the two named source hashes. No native/model receipt rebind or electrical acceptance.')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = (json.dumps(derive(), indent=2) + '\n').encode()
    if args.check:
        if OUTPUT.read_bytes() != data:
            raise SystemExit('FAIL: stale peripheral source equivalence epoch')
    else:
        OUTPUT.write_bytes(data)
