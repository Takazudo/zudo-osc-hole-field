"""Freshness guard for the current OSC PCB checkpoint record.

Run: python3 scripts/checks/osc_pcb_checkpoint.py
Byte and receipt agreement only. It runs no KiCad, proves no routing quality and
qualifies no hardware; every board stays an unvalidated draft.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = ROOT / 'circuit' / 'routing' / 'osc-pcb-current-checkpoint.json'
RAILS = ('+12V', '-12V', '+5V')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def fail(board_id, what):
    raise ValueError(f'{board_id}: {what}; update the checkpoint from accepted evidence, do not weaken the guard')


def check_board(board_id, entry, root):
    if sha(root / entry['board']) != entry['board_sha256']:
        fail(board_id, 'board bytes differ from the checkpoint')
    receipt_path = root / entry['receipt']['path']
    if sha(receipt_path) != entry['receipt']['sha256']:
        fail(board_id, 'receipt bytes differ from the checkpoint')
    mirror = entry['receipt'].get('mirror')
    if mirror and sha(root / mirror) != entry['receipt']['sha256']:
        fail(board_id, 'receipt mirror differs from the receipt')
    receipt = json.loads(receipt_path.read_text())
    gate = receipt['final_gate'] if entry['receipt']['gate'] == 'final_gate' else receipt
    if not (receipt.get('adopted') and gate.get('adopted')):
        fail(board_id, 'receipt is not an adopted gate')
    if gate.get('candidate_board_sha256') != entry['board_sha256']:
        fail(board_id, 'receipt gate names a different board')
    conn = entry['connectivity']
    if gate.get('open_edges_after') != conn['open_edges']:
        fail(board_id, 'open edges disagree with the receipt')
    if conn.get('per_net_open_map_sha256'):
        nets = receipt['open_by_net_after']
        if digest(nets) != conn['per_net_open_map_sha256']:
            fail(board_id, 'per-net open map disagrees with the receipt')
        observed = {'rail_open_edges': {k: nets.get(k, 0) for k in RAILS},
                    'agnd_open_edges': nets.get('AGND', 0), 'open_nets': len(nets)}
    else:
        after = receipt['after']
        observed = {'rail_open_edges': after['rail_open_edges'], 'agnd_open_edges': after['agnd_open_edges'],
                    'agnd_islands': after['agnd_islands'], 'signal_open_edges': after['other_signal_open_edges'],
                    'main_agnd_group_pads': receipt['precision_returns']['main_agnd_group_after']}
    for key, value in observed.items():
        if conn.get(key) != value:
            fail(board_id, f'{key} disagrees with the receipt')
    if conn['open_edges'] != conn['signal_open_edges'] + conn['agnd_open_edges'] + sum(conn['rail_open_edges'].values()):
        fail(board_id, 'open-edge split does not add up')
    state = entry['native_state_record']
    recorded = json.loads((root / state['path']).read_text())['source']['input_board_sha256']
    if recorded != state['input_board_sha256']:
        fail(board_id, 'native state record input differs from the checkpoint')
    if state['fresh'] != (recorded == entry['board_sha256']):
        fail(board_id, 'native state freshness flag is not truthful')


def check_docs(checkpoint, root):
    relative = str(CHECKPOINT.relative_to(ROOT))
    for doc, boards in checkpoint['referenced_by'].items():
        text = (root / doc).read_text()
        if relative not in text:
            raise ValueError(f'{doc}: does not reference {relative}')
        for board_id in boards:
            entry = checkpoint['boards'][board_id]
            if entry['board_sha256'] not in text or entry['label'] not in text:
                raise ValueError(f'{doc}: does not name the current {board_id} label and hash')


def check(checkpoint, root=ROOT):
    for board_id, entry in checkpoint['boards'].items():
        check_board(board_id, entry, root)
    check_docs(checkpoint, root)


def main():
    checkpoint = json.loads(CHECKPOINT.read_text())
    check(checkpoint)
    labels = ' / '.join(e['label'] for e in checkpoint['boards'].values())
    print(f'PASS: checkpoint {labels} matches board bytes, receipts and docs; '
          f"candidate {checkpoint['candidate']['status']}; native refresh NOT RUN; qualification NOT RUN")


if __name__ == '__main__':
    main()
