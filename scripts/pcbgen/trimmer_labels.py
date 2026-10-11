"""Add source-owned trimmer silk labels to an explicit candidate PCB.

The policy is deliberately a placement decision, separate from the function
dictionary. This stage preserves every input byte except its own gr_text blocks.
Physical clearance and native acceptance require the companion native regression.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import UUID_RE, replace_spans, stable_uuid, top_level_spans

OWNER = "trimmer-labels-v1"
POSE_RE = re.compile(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)')
LAYER_RE = re.compile(r'\(layer\s+"([^"]+)"\)')
PROPERTY_RE = re.compile(r'\(property\s+"([^"]+)"\s+"((?:\\.|[^"\\])*)"')
TEXT_RE = re.compile(r'^\(gr_text\s+"((?:\\.|[^"\\])*)"')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _quote(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def _children(block: str):
    return [(a, b, block[a:b]) for a, b in top_level_spans(block)]


def _property(block: str, name: str) -> str:
    values = [m.group(2) for _, _, child in _children(block)
              if (m := PROPERTY_RE.match(child)) and m.group(1) == name]
    if len(values) != 1:
        raise ValueError(f'exactly one {name} property required')
    return values[0]


def _footprints(board: str, wanted: set[str]) -> dict[str, dict]:
    result = {}
    for _, _, block in _children(board):
        if not block.startswith('(footprint '):
            continue
        ref = _property(block, 'Reference')
        if ref not in wanted:
            continue
        if ref in result:
            raise ValueError(f'duplicate Ref {ref}')
        at = next((POSE_RE.match(c) for _, _, c in _children(block) if c.startswith('(at ')), None)
        layer = next((LAYER_RE.match(c) for _, _, c in _children(block) if c.startswith('(layer ')), None)
        if not at or not layer:
            raise ValueError(f'missing footprint pose/layer {ref}')
        result[ref] = dict(block=_property(block, 'Block'), role=_property(block, 'Role'),
                           x=float(at[1]), y=float(at[2]), angle=float(at[3] or 0),
                           side=layer[1])
    return result


def _owned(board: str, board_id: str):
    """Return owned top-level text spans, rejecting UUID hijacks."""
    found = {}
    rows = json.loads((ROOT/'design/service/trimmer-inventory.json').read_text())['trimmers']
    owner_rows = {stable_uuid(board_id, OWNER, row['ref']): row for row in rows
                  if row['placement']['board_id'] == board_id}
    owner_ids = set(owner_rows)
    ids = [m[1].lower() for m in UUID_RE.finditer(board)]
    if any(ids.count(uid) > 1 for uid in owner_ids if uid in ids):
        raise ValueError('owned UUID collision in input board')
    all_ids = set(ids)
    for a, b, block in _children(board):
        match = UUID_RE.search(block)
        if not match:
            continue
        uid = match[1].lower()
        if uid in owner_ids:
            if not block.startswith('(gr_text '):
                raise ValueError(f'owned UUID collision: {uid}')
            label = TEXT_RE.match(block)
            if not label or label[1].replace('\\n', ' ') != owner_rows[uid]['label']:
                raise ValueError(f'owned UUID collision or altered label: {uid}')
            found[uid] = (a, b, block)
    if (all_ids & owner_ids) != set(found):
        raise ValueError('owned UUID collision in nested item')
    return found, all_ids


def _strip_owned(board: str, owned: dict) -> str:
    if not owned:
        return board
    spans = sorted((a,b) for a,b,_ in owned.values())
    first, last = spans[0][0], spans[-1][1]
    if first < 2 or last >= len(board) or board[first-2:first] != '\n\t' or board[last] != '\n':
        raise ValueError('owned text boundary changed')
    cursor = first
    for a,b in spans:
        if board[cursor:a].strip():
            raise ValueError('unowned item interleaved with labels')
        cursor = b
    return board[:first-2] + board[last+1:]


def _format_number(value: float) -> str:
    return format(value, '.6f').rstrip('0').rstrip('.') if value else '0'


def _render(row: dict, entry: dict, side: str, uid: str) -> str:
    label = entry.get('text', row['label'])
    if not isinstance(label, str) or not label or len(label) > 80 or label.count('\n') > 1:
        raise ValueError(f'invalid one/two-line label {row["ref"]}')
    if label.replace('\n', ' ') != row['label']:
        raise ValueError(f'label differs from reviewed function dictionary {row["ref"]}')
    if any(ord(c) < 32 and c != '\n' for c in label):
        raise ValueError(f'control character in label {row["ref"]}')
    layer = 'F.SilkS' if side == 'F.Cu' else 'B.SilkS'
    mirror = ' mirror' if side == 'B.Cu' else ''
    x, y, angle = (entry[k] for k in ('x_mm', 'y_mm', 'angle_deg'))
    return (f'\t(gr_text "{_quote(label)}"\n'
            f'\t\t(at {_format_number(x)} {_format_number(y)} {_format_number(angle)})\n'
            f'\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{uid}")\n'
            f'\t\t(effects (font (size 1 1) (thickness 0.15)) (justify{mirror}))\n'
            f'\t)')


def apply(board_path: Path, policy_path: Path, output_path: Path, *, check=False) -> dict:
    board_path, policy_path, output_path = map(Path, (board_path, policy_path, output_path))
    if board_path.resolve() == output_path.resolve():
        raise ValueError('input/output must differ')
    raw = board_path.read_bytes()
    policy_raw = policy_path.read_bytes()
    policy = json.loads(policy_raw)
    if policy.get('schema_version') != 1 or not isinstance(policy.get('board_id'), str):
        raise ValueError('schema_version 1 and board_id required')
    if policy.get('inventory_sha256') != digest((ROOT/'design/service/trimmer-inventory.json').read_bytes()):
        raise ValueError('stale inventory digest')
    if policy.get('input_board_sha256') != digest(raw):
        # Reapplication is accepted only when every non-owned byte matches the
        # original input digest recorded by an optional policy base path.
        base = policy.get('base_board')
        if not base:
            raise ValueError('wrong/stale input board digest')
        base_path = (policy_path.parent/base).resolve()
        if not base_path.is_file() or digest(base_path.read_bytes()) != policy['input_board_sha256']:
            raise ValueError('wrong/stale base board')
        base_text = base_path.read_text()
        owned, _ = _owned(raw.decode(), policy['board_id'])
        stripped = _strip_owned(raw.decode(), owned)
        if stripped != base_text:
            raise ValueError('non-owned input board drift')
    if check and not output_path.exists():
        raise ValueError('check output absent')
    if output_path.exists() and not check:
        raise ValueError('fresh output required')
    inventory = json.loads((ROOT/'design/service/trimmer-inventory.json').read_bytes())
    board = raw.decode()
    rows = {r['ref']: r for r in inventory['trimmers'] if r['placement']['board_id'] == policy['board_id']}
    footprints = _footprints(board, set(rows))
    owned, all_ids = _owned(board, policy['board_id'])
    placements = policy.get('labels')
    if not isinstance(placements, list):
        raise ValueError('explicit labels policy required')
    expected = {}
    for entry in placements:
        ref = entry.get('ref')
        if ref not in rows or ref not in footprints or ref in expected:
            raise ValueError(f'unknown/duplicate Ref {ref}')
        row, fp = rows[ref], footprints[ref]
        if (entry.get('block'), entry.get('role')) != (row['block'], row['role']) or (fp['block'], fp['role']) != (row['block'], row['role']):
            raise ValueError(f'Block/Role mismatch {ref}')
        pose = row['placement']
        if fp['side'] != pose['side'] or any(abs(fp[k]-pose[pk]) > 1e-4 for k,pk in [('x','native_x_mm'),('y','native_y_mm'),('angle','native_orientation_deg')]):
            raise ValueError(f'stale footprint pose {ref}')
        if entry.get('face') != fp['side']:
            raise ValueError(f'wrong face {ref}')
        if set(entry) - {'ref','block','role','face','x_mm','y_mm','angle_deg','text'}:
            raise ValueError(f'unsupported policy keys {ref}')
        if any(type(entry.get(k)) not in (int,float) or not math.isfinite(entry[k]) for k in ('x_mm','y_mm','angle_deg')):
            raise ValueError(f'finite label pose required {ref}')
        uid = stable_uuid(policy['board_id'], OWNER, ref)
        expected[uid] = _render(row, entry, fp['side'], uid)
        if uid in all_ids and uid not in owned:
            raise ValueError(f'owned UUID collision {ref}')
    # Remove only this owner's prior annotations, including refs dropped by
    # the policy. No existing reference or third-party artwork is edited.
    result = _strip_owned(board, owned)
    closing = result.rfind(')')
    if closing < 0 or result[closing+1:].strip():
        raise ValueError('invalid board end')
    additions = '\n' + '\n'.join(expected.values()) + '\n' if expected else ''
    result = result[:closing] + additions + result[closing:]
    # Existing owned blocks may have occupied arbitrary positions. Verify
    # removing only our additions recovers the exact non-owned input bytes.
    original_unowned = _strip_owned(board, owned)
    if result.replace(additions, '', 1) != original_unowned:
        raise ValueError('non-annotation bytes changed')
    if board_path.read_bytes() != raw or policy_path.read_bytes() != policy_raw:
        raise ValueError('inputs changed during generation')
    encoded = result.encode()
    if check:
        if output_path.read_bytes() != encoded:
            raise ValueError('output differs from source-owned regeneration')
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(encoded)
    return {'input_sha256': digest(raw), 'output_sha256': digest(encoded), 'label_count': len(expected),
            'clearance_status': 'UNRESOLVED: body/mask/pad/edge/text conflicts require native geometry review',
            'native_status': 'NOT RUN; source-only byte-preservation stage'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('board','policy','output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(apply(args.board,args.policy,args.output,check=args.check), indent=2))
