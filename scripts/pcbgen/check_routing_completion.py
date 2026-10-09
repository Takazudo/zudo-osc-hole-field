#!/usr/bin/env python3
"""Check zero native JL/JR/core edges; never promote copper or qualify hardware.

Run through the heavy guard. This is separate from intermediate draft CI, which
intentionally permits reported unconnected items. All three boards are required.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen import route_jack_grid as driver

BOARDS = ('osc-jack-left', 'osc-jack-right', 'osc-core')


def zero_gate(settled, fresh, settled_drc, fresh_drc):
    """Use complete native island membership, never capped CLI samples."""
    counts = [d['open_edges'] for d in (settled, fresh)]
    island_counts = [sum(max(0, len(g) - 1) for g in d['islands'].values())
                     for d in (settled, fresh)]
    native_errors = any(any(v['severity'] == 'error' for v in r['violations'])
                        or r['schematic_parity'] for r in (settled_drc, fresh_drc))
    same_membership = driver.connectivity_signature(settled) == driver.connectivity_signature(fresh)
    warnings = [driver.warning_identities(r) for r in (settled_drc, fresh_drc)]
    same_warnings = set(warnings[0]) == set(warnings[1])
    return {'zero_native_edges': counts == island_counts == [0, 0],
            'native_errors_or_parity': native_errors,
            'fresh_membership_matches': same_membership,
            'fresh_warning_identities_match': same_warnings,
            'warning_identities': warnings,
            'native_open_edges': counts,
            'island_open_edges': island_counts,
            'passed': counts == island_counts == [0, 0] and not native_errors
                      and same_membership and same_warnings}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context_hashes(directory):
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and (p.suffix in ('.kicad_pro', '.kicad_dru', '.kicad_sch')
                                or p.name in ('fp-lib-table', 'sym-lib-table'))}


def main():
    out = ROOT / '.circuit-cache/routing-completion.json'
    out.parent.mkdir(exist_ok=True)
    receipt = {'status': 'RUNNING; NOT PASSED', 'passed': False, 'boards': {},
               'scope': 'Zero JL/JR/core connectivity only; warnings still require review. '
                        'Other-board regressions and hardware qualification are separate.'}
    def save():
        out.write_text(json.dumps(receipt, indent=2) + '\n')
    save()  # Invalidate any previous success before native work begins.
    try:
        for board_id in BOARDS:
            source = ROOT / 'boards' / board_id / f'{board_id}.kicad_pcb'
            source_hash = digest(source)
            context = context_hashes(source.parent)
            base = driver.workspace(board_id, 'completion-settled') / source.name
            shutil.copyfile(source, base)
            drc, settled = driver.check(base)
            if settled['board_sha256'] != digest(base):
                raise ValueError('settled native dump does not match saved board')
            fresh_board = driver.workspace(board_id, 'completion-fresh') / source.name
            shutil.copyfile(base, fresh_board)
            fresh_drc, fresh = driver.check(fresh_board)
            if (fresh['board_sha256'] != digest(fresh_board) or digest(source) != source_hash
                    or context_hashes(source.parent) != context):
                raise ValueError('fresh dump or canonical input changed during verification')
            receipt['boards'][board_id] = {
                'input_board_sha256': source_hash, 'project_context_sha256': context,
                'settled_board_sha256': digest(base), 'fresh_board_sha256': digest(fresh_board),
                **zero_gate(settled, fresh, drc, fresh_drc)}
            save()
        receipt['passed'] = all(receipt['boards'][b]['passed'] for b in BOARDS)
        receipt['status'] = 'ZERO-EDGE GATE PASSED; UNVALIDATED DRAFT' if receipt['passed'] else 'INCOMPLETE; NOT PASSED'
    except Exception as error:
        receipt.update(status='NATIVE CHECK FAILED; NOT PASSED', error=str(error))
        raise
    finally:
        save()
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
