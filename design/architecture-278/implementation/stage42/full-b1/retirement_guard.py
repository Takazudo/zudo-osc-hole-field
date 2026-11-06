"""Bind the separately reviewed full-B1 supply cleanup to exact source rows."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'stage41/native-pilot'))
from identity_guard import bound_retirements as original_bound, digest

PROOF = Path(__file__).with_name('evidence') / 'supply-contact-proof.json'


def bound_retirements(receipt, baseline_raw):
    local = receipt.get('retired_stage42_supply_copper', [])
    if not local:
        return original_bound(receipt, baseline_raw)
    proof_raw = PROOF.read_text()
    proof = json.loads(proof_raw)
    if receipt.get('retired_local_supply_copper'):
        raise ValueError('cannot combine Stage41 and Stage42 supply retirements')
    if (local != proof['screened_retirements'] or
            receipt.get('supply_contact_proof_sha256') != digest(proof_raw) or
            proof['canonical_sha256'] != digest(baseline_raw) or
            proof['version'] != '10.0.6'):
        raise ValueError('Stage42 retirement proof binding')
    return original_bound({'retired_private_copper': receipt['retired_private_copper'] + local}, baseline_raw)
