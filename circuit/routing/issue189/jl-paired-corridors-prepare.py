"""Retain the two complete, locally successful transactions from the six-cut pilot.

Native acceptance is still mandatory: removing other transactions can change fills.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
source = HERE / 'jl-six-corridors-copper.json'
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'c9bc6cc806987b0ab70badfd0b2250a30695da765c6bc6416c7458a9232187cd'
delta = json.loads(source.read_text())
assert hashlib.sha256((ROOT / 'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest() == delta['base_sha256']
targets = {'X23ECF9EB43629B723874', 'XA3808316751BA419D842'}
selection = json.loads((HERE / 'jl-six-corridors-selection.json').read_text())
transactions = [e for e in selection if e['target'] in targets]
assert len(transactions) == 2
nets = {n for e in transactions for n in [e['target'], *e['victims']]}
receipt = json.loads((HERE / 'jl-six-corridors-result.json').read_text())
assert not nets & {g['net'] for g in receipt['gate']['split_pad_groups']}
out = {**delta, 'nets': sorted(nets), 'added': [a for a in delta['added'] if a['net'] in nets],
       'removed': [a for a in delta['removed'] if a['net'] in nets]}
assert {a['uuid'] for a in out['removed']} == {u for e in transactions for u in e['removed_source_uuids']}
(HERE / 'jl-paired-corridors-copper.json').write_text(json.dumps(out, sort_keys=True) + '\n')
print('Prepared whole transactions:', len(out['added']), 'added,', len(out['removed']), 'removed; native subset gate NOT RUN')
