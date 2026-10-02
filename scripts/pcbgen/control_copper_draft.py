"""Replay explicit partial P copper without rerunning the autorouter.

Only new copper and source-owned ground pours are appended to the checked
layout. Original footprint, outline, setup and reservation bytes are kept.
This is an unvalidated draft, not a conductor-model acceptance gate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.verify_local_links import blocks


def validate(spec):
    if spec['schema_version'] != 1 or spec['board_id'] != 'osc-control':
        raise ValueError('Exact P copper source required')
    if spec['coordinate_frame'] != 'native KiCad integer nanometres':
        raise ValueError('Native integer coordinate frame required')
    rows = spec['copper']
    ids = set()
    for row in rows:
        uid = row['uuid']
        if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', uid) or uid in ids:
            raise ValueError('Copper UUID must be unique and explicit')
        ids.add(uid)
        if not isinstance(row['net'], str) or not row['net']:
            raise ValueError('Every copper object needs a named source net')
        if row['kind'] == 'segment':
            expected = {'kind','uuid','net','start_nm','end_nm','width_nm','layer'}
            vectors = (row['start_nm'], row['end_nm'])
            if row['layer'] not in ('F.Cu','In1.Cu','In2.Cu','B.Cu'):
                raise ValueError('Unexpected signal layer')
            width = 400000 if row['net'] in ('+12V','-12V','+5V') else 300000
            if type(row['width_nm']) is not int or row['width_nm'] != width or vectors[0] == vectors[1]:
                raise ValueError('Source class width or segment length changed')
        elif row['kind'] == 'via':
            expected = {'kind','uuid','net','at_nm','diameter_nm','drill_nm','layers','locked'}
            vectors = (row['at_nm'],)
            if (type(row['diameter_nm']) is not int or row['diameter_nm'] != 700000 or
                    type(row['drill_nm']) is not int or row['drill_nm'] != 300000 or
                    row['layers'] != ['F.Cu','B.Cu'] or type(row['locked']) is not bool):
                raise ValueError('Source through-via geometry changed')
        else:
            raise ValueError('Unsupported copper primitive')
        if set(row) != expected:
            raise ValueError('Unexpected copper source fields')
        if any(not isinstance(v, list) or len(v) != 2 or
               any(type(x) is not int or abs(x) >= 2**31 for x in v) for v in vectors):
            raise ValueError('Finite bounded integer coordinates required')
    by_id = {row['uuid']: row for row in rows}
    arrays = spec['main_arrays']
    if len(arrays) != 6 or len({a['ref'] for a in arrays}) != 6:
        raise ValueError('All six main-terminal arrays required')
    assigned = set()
    for array in arrays:
        if len(array['via_uuids']) != 25:
            raise ValueError('Each main terminal requires its 25 source vias')
        for uid in array['via_uuids']:
            if uid in assigned or uid not in by_id:
                raise ValueError('Main-array via identity missing or duplicated')
            assigned.add(uid)
            row = by_id[uid]
            if row['kind'] != 'via' or row['net'] != array['net'] or not row['locked']:
                raise ValueError('Main-array via net/type/lock changed')
    return rows


def require_connected_ground_copper(spec, native):
    """Reject isolated source ground copper, including non-array stitches."""
    expected = {row['uuid'] for row in spec['copper'] if row['net'] == 'AGND'}
    disconnected = expected - set(native['main_rail_members']['AGND'])
    if disconnected:
        raise ValueError('Source ground copper is disconnected from main ground: '+
                         ', '.join(sorted(disconnected)))
    return len(expected)


def build(source, output):
    import pcbnew
    from scripts.pcbgen.definition import load_definition
    from scripts.pcbgen.route_kicad import apply_classes, ensure_zones
    source, output = Path(source), Path(output)
    raw = source.read_bytes()
    spec = json.loads(raw)
    rows = validate(spec)
    base = ROOT/spec['base_board']
    definition_path = ROOT/spec['definition']
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if digest(base) != spec['base_sha256'] or digest(definition_path) != spec['definition_sha256']:
        raise ValueError('Checked base layout or definition changed')
    inputs = [source, base, definition_path] + [base.with_suffix(s) for s in ('.kicad_pro','.kicad_sch','.kicad_dru')]
    before = {str(p): digest(p) for p in inputs}
    if output.resolve() == base.resolve() or any(output.with_suffix(s).exists() for s in ('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru')):
        raise ValueError('Fresh distinct draft output required')
    original = blocks(base)
    if any(original[k] for k in ('segment','via','arc')):
        raise ValueError('Base layout must be unrouted')
    board = pcbnew.LoadBoard(str(base))
    definition = load_definition(definition_path)
    # pcbnew.LoadBoard is not a substitute for applying the source net classes.
    # The stored fill must use the same clearances as the subsequent CLI DRC.
    apply_classes(board, definition.routing)
    fps = {f.GetReference():f for f in board.GetFootprints()}
    by_id = {row['uuid']:row for row in rows}
    for array in spec['main_arrays']:
        if array['ref'] not in fps:
            raise ValueError('Missing main terminal')
        fp = fps[array['ref']]
        pads = list(fp.Pads())
        if (str(fp.GetFPID().GetLibItemName()) != 'LoadWireTerminal_4x4mm' or
                len(pads) != 1 or pads[0].GetNetname() != array['net']):
            raise ValueError('Main array does not own its exact source terminal')
        pad = pads[0]
        if pad.GetShape() != pcbnew.PAD_SHAPE_RECT or pad.GetSize().x != 4000000 or pad.GetSize().y != 4000000:
            raise ValueError('Main array requires its exact square terminal')
        for uid in array['via_uuids']:
            via = by_id[uid]
            if max(abs(via['at_nm'][0]-pad.GetPosition().x),
                   abs(via['at_nm'][1]-pad.GetPosition().y))+via['diameter_nm']//2 > 2000000:
                raise ValueError('Main-array annulus leaves its owning terminal')
    for row in rows:
        net = board.FindNet(row['net'])
        if net is None or net.GetNetCode() <= 0:
            raise ValueError('Copper net absent from current board: '+row['net'])
        if row['kind'] == 'segment':
            item = pcbnew.PCB_TRACK(board)
            item.SetStart(pcbnew.VECTOR2I(*row['start_nm']))
            item.SetEnd(pcbnew.VECTOR2I(*row['end_nm']))
            item.SetWidth(row['width_nm'])
            item.SetLayer(board.GetLayerID(row['layer']))
        else:
            item = pcbnew.PCB_VIA(board)
            item.SetViaType(pcbnew.VIATYPE_THROUGH)
            item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            item.SetPosition(pcbnew.VECTOR2I(*row['at_nm']))
            item.SetWidth(row['diameter_nm'])
            item.SetDrill(row['drill_nm'])
            item.SetLocked(row['locked'])
        item.SetNetCode(net.GetNetCode())
        item.SetUuid(pcbnew.KIID(row['uuid']))
        board.Add(item)
    new_ids, managed = ensure_zones(board, 'osc-control', definition)
    for zone in board.Zones():
        uid = zone.m_Uuid.AsString()
        if uid in new_ids:
            zone.SetUuid(pcbnew.KIID(new_ids[uid]))
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise ValueError('Native ground refill failed')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep the serialization as failed-run evidence if any ownership check fails.
    serialized = output.with_suffix('.serialized.kicad_pcb')
    pcbnew.SaveBoard(str(serialized), board)
    native = blocks(serialized)
    for uid, value in original['zone'].items():
        if native['zone'].get(uid) != value:
            raise ValueError('Native save changed a source reservation')
    expected_zones = {stable_uuid('osc-control','pour',f"{z['name']}:{layer}")
                      for z in definition.routing['zones'] for layer in z['layers']}
    if set(native['zone'])-set(original['zone']) != expected_zones:
        raise ValueError('Unexpected ground-pour ownership')
    copper = {uid:value for kind in ('segment','via','arc') for uid,value in native[kind].items()}
    if set(copper) != {row['uuid'] for row in rows}:
        raise ValueError('Native copper differs from explicit source identity set')
    text = base.read_text()
    end = text.rfind(')')
    additions = [copper[uid] for uid in sorted(copper)] + [native['zone'][uid] for uid in sorted(expected_zones)]
    output.write_text(text[:end]+''.join('\t'+block+'\n' for block in additions)+text[end:])
    final = blocks(output)
    non_copper = final['non_copper'].copy()
    for uid in expected_zones:
        non_copper[final['zone'][uid]] -= 1
    if +non_copper != original['non_copper']:
        raise ValueError('Draft changed original layout, outline, setup or footprints')
    for suffix in ('.kicad_sch','.kicad_dru'):
        shutil.copyfile(base.with_suffix(suffix), output.with_suffix(suffix))
    project = json.loads(base.with_suffix('.kicad_pro').read_bytes())
    project['meta']['filename'] = output.with_suffix('.kicad_pro').name
    output.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2,sort_keys=True)+'\n')
    if any(digest(Path(p)) != value for p,value in before.items()):
        raise ValueError('Source changed during copper replay')
    print('Replayed',len(rows),'explicit copper objects; original non-copper bytes preserved',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    build(args.source,args.output)
