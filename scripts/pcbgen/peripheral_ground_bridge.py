"""Insert one source-declared finite optical F/B ground bridge before fill.

The original board text is retained byte for byte. Native DRC and complete
source-contact continuity remain mandatory after the fill.
"""
import hashlib

from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.verify_local_links import blocks


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def insert(text, board_id, bridge):
    if board_id != 'osc-stage-optical' or bridge != {
        'source_xy_mm': [218, 166], 'native_xy_mm': [318, 216],
        'net': 'AGND', 'layers': ['F.Cu', 'B.Cu'],
        'diameter_mm': 0.7, 'drill_mm': 0.3,
    }:
        raise ValueError('unreviewed peripheral bridge source geometry')
    if not text.startswith('(kicad_pcb') or not text.endswith('\n)\n'):
        raise ValueError('native PCB serialization differs from source bridge insertion contract')
    uid = stable_uuid(board_id, 'ground-prerequisite-bridge', 'F-B-one')
    via = (f'\t(via\n\t\t(at 318 216)\n\t\t(size 0.7)\n\t\t(drill 0.3)\n'
           f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "AGND")\n'
           f'\t\t(uuid "{uid}")\n\t)\n')
    if uid in text or '\n\t(via\n\t\t(at 318 216)' in text:
        raise ValueError('source bridge already present')
    changed = text[:-2] + via + ')\n'
    # Check direct source text ownership without SaveBoard reserialization.
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix='optical-ground-bridge-') as folder:
        before_path = Path(folder)/'before.kicad_pcb'
        after_path = Path(folder)/'after.kicad_pcb'
        before_path.write_text(text)
        after_path.write_text(changed)
        before, after = blocks(before_path), blocks(after_path)
    for kind in ('footprint', 'zone', 'segment', 'arc'):
        if before[kind] != after[kind]:
            raise ValueError('ground bridge changed original ' + kind)
    if set(after['via']) != set(before['via']) | {uid} or any(
        after['via'].get(key) != block for key, block in before['via'].items()
    ):
        raise ValueError('ground bridge changed original via state')
    return changed, {
        'board_id': board_id, 'source_bridge': bridge, 'via_uuid': uid,
        'before_sha256': digest(text), 'after_sha256': digest(changed),
        'scope': 'One exact source AGND F/B 0.7/0.3 mm via; original blocks exact. Native rule, physical, and all 72 ground-contact gates still required.',
    }
