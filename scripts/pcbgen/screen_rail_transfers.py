"""All fitted rail-contact screen; never removes local access from the matrix.

The source-current norm and numerical contact profiles are explicit conditions.
This diagnostic neither selects them nor assigns a common-plane/K budget.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def bind_artifact_paths(report, matrix_path, ledger_path):
    """Bind the screen to exact files as well as their complete JSON contents."""
    paths = {'matrix': Path(matrix_path), 'ledger': Path(ledger_path)}
    artifacts = {}
    for name, path in paths.items():
        raw = path.read_bytes()
        if content_hash(json.loads(raw)) != report['input_receipts'][name + '_content_sha256']:
            raise ValueError('screen input file differs from its computed JSON receipt')
        artifacts[name] = {'path': str(path.resolve()), 'sha256': hashlib.sha256(raw).hexdigest()}
    profile = report['input_receipts']['profile_receipt']
    if hashlib.sha256(Path(profile['path']).read_bytes()).hexdigest() != profile['sha256']:
        raise ValueError('finite-profile receipt differs from its matrix binding')
    report['input_artifacts'] = artifacts
    return report


def screen(receipt, ledger, net):
    if net not in ('+12V', '-12V', '+5V'):
        raise ValueError('explicit physical source rail required')
    if receipt['board_sha256'] != ledger['board_sha256']:
        raise ValueError('matrix and rail ledger have different board identities')
    mapping = receipt.get('conductor_role_mapping', {})
    if mapping.get('actual_native_net') != net:
        raise ValueError('matrix lacks its explicit physical rail mapping')
    if not ledger.get('native_export_sha256') or mapping.get('original_native_export_sha256') != ledger['native_export_sha256']:
        raise ValueError('matrix and ledger have different native-export authority')
    for field in ('native_export_sha256', 'model_source_sha256', 'rail_wrapper_source_sha256', 'profile_receipt'):
        if not receipt.get(field):
            raise ValueError('matrix lacks complete profile/model provenance: ' + field)
    ports = receipt['ports']
    loads = [i for i, p in enumerate(ports) if p['kind'] == 'load']
    expected = {(p['ref'], p['pad']) for p in ledger['pads'] if p['net'] == net}
    actual = {(ports[i]['ref'], ports[i]['pad']) for i in loads}
    if not loads or actual != expected or len(actual) != len(loads):
        raise ValueError('matrix does not cover every exact fitted rail contact once')
    if any(not p['native_connected_to_load_land'] for p in ledger['pads'] if p['net'] == net):
        raise ValueError('native rail feed is incomplete')
    upper = np.asarray(receipt['matrices_ohm']['upper'], dtype=float)
    lower = np.asarray(receipt['matrices_ohm']['lower'], dtype=float)
    if upper.shape != (len(ports), len(ports)) or lower.shape != upper.shape:
        raise ValueError('rail matrix dimensions do not match its profiles')
    if not np.isfinite(upper).all() or not np.isfinite(lower).all():
        raise ValueError('nonfinite rail energy')
    gap = np.diag(upper - lower)
    if min(gap) < -1e-10:
        raise ValueError('negative variational diagonal gap')
    gaps = np.maximum(gap[loads], 0.)
    centre = ((upper + lower) / 2)[np.ix_(loads, loads)]
    widths = .5 * np.sqrt(gaps[:, None] * gaps[None, :])
    coefficients = np.abs(centre) + widths
    current = float(ledger['source_envelope_A'][net])
    if not np.isfinite(current) or current <= 0:
        raise ValueError('positive finite rail source envelope required')
    rows = []
    for row, index in enumerate(loads):
        cause = int(np.argmax(coefficients[row]))
        source = ports[loads[cause]]
        rows.append({'ref': ports[index]['ref'], 'pad': ports[index]['pad'],
            'absolute_drop_upper_V': float(coefficients[row, cause] * current),
            'transfer_upper_ohm': float(coefficients[row, cause]),
            'extreme_injection_ref': source['ref'], 'extreme_injection_pad': source['pad'],
            'centre_ohm': float(centre[row, cause]),
            'interval_halfwidth_ohm': float(widths[row, cause])})
    return {'status': 'NOT ACCEPTED: finite numerical profiles and conditional current norm only',
        'input_receipts': {'matrix_content_sha256': content_hash(receipt),
            'ledger_content_sha256': content_hash(ledger),
            'profile_receipt': receipt['profile_receipt'],
            'model_source_sha256': receipt['model_source_sha256'],
            'rail_wrapper_source_sha256': receipt['rail_wrapper_source_sha256'],
            'selected_export_sha256': receipt['native_export_sha256'],
            'original_native_export_sha256': ledger['native_export_sha256']},
        'board_sha256': receipt['board_sha256'], 'physical_net': net,
        'reference_main': receipt['reference_main'], 'fitted_contact_count': len(loads),
        'aggregate_absolute_current_A': current,
        'current_condition': 'The sum of absolute currents at all listed rail contacts is at most the stated source envelope, with the balancing current at the one reference main. Input source limiting alone does not establish this class during capacitor discharge or circulating currents.',
        'method': 'For compatible Loewner matrices, use abs((U+L)/2) + sqrt(diag(U-L) outer diag(U-L))/2, then maximize over one aggregate absolute-current norm.',
        'accounting': 'All represented foil, shared neck, main-land, local pad, track and barrel terms remain in this complete pad-to-main transfer. No private access is subtracted or assigned zero cost.',
        'common_rail_and_K_allocation': 'NOT RUN: the separate combined 1 mOhm common-rail contract and positive actual K allocation remain required.',
        'distribution_total': 'NOT RUN: combine compatible whole-wire, termination, common and local rail/return costs under the unchanged 20 mV and 0.20 V limits.',
        'worst': max(rows, key=lambda r: r['absolute_drop_upper_V']), 'contacts': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('matrix', type=Path)
    parser.add_argument('ledger', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--net', required=True, choices=('+12V', '-12V', '+5V'))
    args = parser.parse_args()
    result = screen(json.loads(args.matrix.read_text()), json.loads(args.ledger.read_text()), args.net)
    bind_artifact_paths(result, args.matrix, args.ledger)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['worst'], indent=2))
