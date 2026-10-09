"""Native positive/negative batching controls; never board acceptance evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.probe_zone_batches import BEFORE_SHA, ZONE, artwork, sha
from scripts.pcbgen.audit_zone_silk_scope import native_zone_signature, zone_fixture_parts
from scripts.pcbgen.audit_added_mask import new_silk_identities

IDS = [str(uuid.uuid5(uuid.NAMESPACE_URL, 'issue189-zone-batch-control-' + str(i))) for i in range(3)]


def control_text(parts, selected, point, zone_layer="F.Mask"):
    """Create an exposed mask-zone control with identical polygon coordinates."""
    if not selected or len(selected) != len(set(selected)) or not set(selected) <= set(range(3)):
        raise ValueError('invalid control selection')
    if zone_layer not in ('F.Cu', 'F.Mask'):
        raise ValueError('unsupported control zone layer')
    common = ''.join(block.replace('"F.Cu"', '"' + zone_layer + '"') if block.startswith('(zone') else block
                     for uid, block in parts if uid is None)
    end = common.rfind(')')
    if end < 0:
        raise ValueError('missing board terminator')
    drawings = []
    for index in selected:
        x, y = point if index < 2 else (1000., 1000.)
        y += index * .05
        drawings.append(f'(gr_line (start {x:.6f} {y:.6f}) (end {x + .2:.6f} {y:.6f}) '
                        f'(stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "{IDS[index]}"))\n')
    return common[:end] + ''.join(drawings) + common[end:]


def selected_identities(report):
    if report.get('kicad_version') != '10.0.6':
        raise ValueError('native version mismatch')
    return {(r['type'], r['severity'], tuple(sorted(x['uuid'] for x in r['items'])))
            for r in new_silk_identities(report, ZONE)}


def main(source, output):
    import pcbnew
    if subprocess.check_output(['kicad-cli', 'version'], text=True).strip() != '10.0.6' or sha(source) != BEFORE_SHA:
        raise ValueError('pinned native source/version mismatch')
    output.mkdir(parents=True, exist_ok=False)
    result = dict(status='STARTED; CONTROLS NOT COMPLETE; NEVER ACCEPTANCE', before_sha256=BEFORE_SHA,
                  version='10.0.6', control_zone_layer='F.Mask',
                  deliberate_fixture_changes='Map the copied F.Cu zone and filled polygon layer to F.Mask; add synthetic silk only. Never a source board.', controls=[])
    receipt = output / 'result.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    board = pcbnew.LoadBoard(str(source))
    zone = next(z for z in board.Zones() if z.m_Uuid.AsString() == ZONE)
    poly = zone.GetFilledPolysList(pcbnew.F_Cu)
    signature = native_zone_signature(poly)
    point = None
    # Search near real vertices, requiring a generous contained neighborhood.
    for i in range(poly.OutlineCount()):
        chain = poly.Outline(i)
        for j in range(chain.PointCount()):
            vertex = chain.CPoint(j)
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                x, y = vertex.x + dx * 500000, vertex.y + dy * 500000
                if all(poly.Contains(pcbnew.VECTOR2I(x + ox, y + oy))
                       for ox in (-300000, 0, 500000) for oy in (-300000, 0, 500000)):
                    point = (x / 1e6, y / 1e6)
                    break
            if point is not None:
                break
        if point is not None:
            break
    if point is None:
        raise ValueError('no verified interior control point')
    parts = zone_fixture_parts(source.read_text(), ZONE, {a.m_Uuid.AsString() for a in artwork(board, pcbnew)})
    unions = {}
    for name, selected, zone_layer in [('covered-copper', [0, 1], 'F.Cu'), ('positive-a', [0], 'F.Mask'), ('positive-b', [1], 'F.Mask'), ('negative', [2], 'F.Mask'), ('batch', [0, 1, 2], 'F.Mask')]:
        folder = output / name
        folder.mkdir()
        fixture = folder / source.name
        fixture.write_text(control_text(parts, selected, point, zone_layer))
        for suffix in ('.kicad_pro', '.kicad_dru'):
            shutil.copyfile(source.with_suffix(suffix), fixture.with_suffix(suffix))
        loaded = pcbnew.LoadBoard(str(fixture))
        zones = list(loaded.Zones())
        if len(zones) != 1 or zones[0].m_Uuid.AsString() != ZONE or native_zone_signature(zones[0].GetFilledPolysList(pcbnew.F_Mask if zone_layer == 'F.Mask' else pcbnew.F_Cu)) != signature:
            raise ValueError('control changed native zone geometry')
        if list(loaded.GetTracks()) or list(loaded.GetFootprints()):
            raise ValueError('unrelated control copper/footprints remain')
        if {a.m_Uuid.AsString() for a in artwork(loaded, pcbnew)} != {IDS[i] for i in selected}:
            raise ValueError('control artwork scope mismatch')
        report = folder / 'drc.json'
        subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '--output', str(report), str(fixture)], check=True)
        for suffix in ('.kicad_pro', '.kicad_dru'):
            if source.with_suffix(suffix).read_bytes() != fixture.with_suffix(suffix).read_bytes():
                raise ValueError('native control context changed')
        observed = selected_identities(json.loads(report.read_text()))
        expected_art = {IDS[i] for i in selected if i < 2} if zone_layer == 'F.Mask' else set()
        actual_art = {u for _, _, ids in observed for u in ids if u != ZONE}
        if actual_art != expected_art:
            raise ValueError('native positive/negative control did not detect exactly the expected artwork')
        unions[name] = observed
        result['controls'].append(dict(name=name, selected=selected, zone_layer=zone_layer, identities=sorted(observed),
            fixture_sha256=sha(fixture), report_sha256=sha(report), native_geometry_sha256=signature))
        receipt.write_text(json.dumps(result, indent=2) + '\n')
    if unions['batch'] != unions['positive-a'] | unions['positive-b'] | unions['negative']:
        raise ValueError('batch detection differs from single-item controls')
    result.update(status='NATIVE POSITIVE AND NEGATIVE CONTROLS PASS; NEVER ACCEPTANCE', point_mm=point)
    receipt.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.source, args.output)
