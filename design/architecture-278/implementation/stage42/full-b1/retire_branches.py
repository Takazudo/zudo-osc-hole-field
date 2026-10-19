"""Remove exact reviewed obsolete supply leaves only in a new disposable copy."""
from pathlib import Path
import argparse
import json
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'stage41/native-pilot'))
from identity_guard import digest, inventory, compare, top_level_spans, kind, value
from retirement_guard import bound_retirements, PROOF
ROOT = Path(__file__).resolve().parents[5]


def retire(source, signal_path, output):
    cache = (ROOT / '.circuit-cache').resolve()
    if source.resolve().parent != cache or output.resolve().parent != cache or output.exists():
        raise ValueError('existing source/new direct disposable cache directory required')
    raw = (source / 'osc-jack-left.kicad_pcb').read_text()
    proof_raw = PROOF.read_text(); proof = json.loads(proof_raw)
    if digest(raw) != proof['candidate_sha256']:
        raise ValueError('contact proof candidate binding')
    receipt = json.loads((source / 'prepare-receipt.json').read_text())
    if receipt.get('retired_stage42_supply_copper'):
        raise ValueError('already retired')
    receipt['retired_stage42_supply_copper'] = proof['screened_retirements']
    receipt['supply_contact_proof_sha256'] = digest(proof_raw)
    canonical = (ROOT / 'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_text()
    if digest(canonical) != receipt['canonical_sha256']:
        raise ValueError('canonical baseline binding')
    bound_retirements(receipt, canonical)
    hashes = {r['sha256'] for r in proof['screened_retirements']}
    withdraw = set(proof['withdraw_new_copper'])
    signal = json.loads(signal_path.read_text())
    if signal['removed_uuids'] or {r['uuid'] for r in signal['copper'] if r['uuid'] in withdraw} != withdraw:
        raise ValueError('withdrawal proposal binding')
    spans = []; found = set()
    for a, b in top_level_spans(raw):
        part = raw[a:b]
        if kind(part) in ('segment', 'via') and (digest(part) in hashes or value(part, 'uuid') in withdraw):
            spans.append((a, b)); found.add(value(part, 'uuid')); hashes.add(digest(part))
    expected = {r['uuid'] for r in proof['screened_retirements']} | withdraw
    if found != expected or len(spans) != len(expected):
        raise ValueError('missing/ambiguous cleanup occurrence')
    edited = raw
    for a, b in reversed(spans): edited = edited[:a] + edited[b:]
    if not compare(inventory(raw), inventory(edited), hashes, [])['accepted']:
        raise ValueError('unexpected raw cleanup delta')
    signal['copper'] = [r for r in signal['copper'] if r['uuid'] not in withdraw]
    output.mkdir()
    for item in source.iterdir():
        if item.is_dir(): shutil.copytree(item, output / item.name)
        elif item.suffix in ('.kicad_pro', '.kicad_sch', '.kicad_dru') or item.name in ('fp-lib-table', 'sym-lib-table'):
            shutil.copy2(item, output / item.name)
    (output / 'osc-jack-left.kicad_pcb').write_text(edited)
    (output / 'prepare-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (output / 'signal-proposal.json').write_text(json.dumps(signal, indent=2) + '\n')
    print(json.dumps({'retired_baseline_objects': len(proof['screened_retirements']),
                      'withdrawn_new_objects': len(withdraw), 'candidate_sha256': digest(edited),
                      'status': 'RAW DELTA ONLY; full native gates pending'}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('source', 'signal', 'output'): p.add_argument(name, type=Path)
    a = p.parse_args(); retire(a.source, a.signal, a.output)
