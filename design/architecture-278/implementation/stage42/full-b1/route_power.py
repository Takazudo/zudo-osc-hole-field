"""Six same-face IC/bypass links and twelve local plane fanouts.

Native effective-shape screening proposes geometry only. Actual zone connection,
DRC and complete baseline connectivity are mandatory subsequent gates.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import pcbnew
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stage41/native-pilot"))
from native_guard import check_native
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.route_source_local import box_hit


def propose(path, output):
    raw = path.read_text(); board = pcbnew.LoadBoard(str(path)); check_native(board, raw)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    pads = [p for f in board.GetFootprints() for p in f.Pads()]
    tracks = list(board.GetTracks()); layers = list(board.GetEnabledLayers().CuStack())
    keepouts = [z for z in board.Zones() if z.GetIsRuleArea()]
    rows = []; paths = []
    def pad(ref, number):
        return next(p for p in fps[ref].Pads() if p.GetNumber() == number)
    def mm(p): return [pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)]
    def segment_clear(a, b, net):
        segment = pcbnew.SEG(a, b)
        clearance = pcbnew.FromMM(.25 + .4/2)
        if any(p.IsOnLayer(face) and p.GetNetname() != net and p.GetEffectiveShape(face).Collide(segment, clearance) for p in pads): return False
        if any(t.IsOnLayer(face) and t.GetNetname() != net and t.GetEffectiveShape(face).Collide(segment, clearance) for t in tracks): return False
        if any(z.IsOnLayer(face) and z.GetDoNotAllowTracks() and box_hit(z.GetBoundingBox(), a, b, clearance) for z in keepouts): return False
        return True
    def via_clear(at, net):
        shape = pcbnew.SHAPE_CIRCLE(at, pcbnew.FromMM(.35))
        for item in [*pads, *tracks]:
            if item.GetNetname() == net: continue
            if any(item.IsOnLayer(l) and item.GetEffectiveShape(l).Collide(shape, pcbnew.FromMM(.25)) for l in layers): return False
        for p in pads:
            if p.HasHole() and math.dist((at.x, at.y), (p.GetPosition().x, p.GetPosition().y)) < (max(p.GetDrillSize().x, p.GetDrillSize().y) + pcbnew.FromMM(.3))/2 + pcbnew.FromMM(.25): return False
        for t in tracks:
            if t.Type() == pcbnew.PCB_VIA_T and math.dist((at.x, at.y), (t.GetPosition().x, t.GetPosition().y)) < (t.GetDrillValue() + pcbnew.FromMM(.3))/2 + pcbnew.FromMM(.25): return False
        if any(z.GetDoNotAllowVias() and box_hit(z.GetBoundingBox(), at, at, pcbnew.FromMM(.6)) for z in keepouts): return False
        return True
    def add_segment(a, b, net, tag):
        row = {'kind': 'segment', 'net': net, 'start_nm': [a.x, a.y], 'end_nm': [b.x, b.y], 'width_nm': 400000, 'layer': board.GetLayerName(face)}
        row['uuid'] = stable_uuid('osc-jack-left', 'stage42-power', tag + json.dumps(row, sort_keys=True))
        t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(b); t.SetWidth(400000); t.SetLayer(face); t.SetNetCode(board.FindNet(net).GetNetCode()); t.SetUuid(pcbnew.KIID(row['uuid']))
        board.Add(t); tracks.append(t); rows.append(row)
    def add_via(at, net, tag):
        row = {'kind': 'via', 'net': net, 'at_nm': [at.x, at.y], 'diameter_nm': 700000, 'drill_nm': 300000, 'layers': ['F.Cu', 'B.Cu'], 'locked': False}
        row['uuid'] = stable_uuid('osc-jack-left', 'stage42-power', tag + json.dumps(row, sort_keys=True))
        t = pcbnew.PCB_VIA(board); t.SetViaType(pcbnew.VIATYPE_THROUGH); t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); t.SetPosition(at); t.SetWidth(700000); t.SetDrill(300000); t.SetNetCode(board.FindNet(net).GetNetCode()); t.SetUuid(pcbnew.KIID(row['uuid']))
        board.Add(t); tracks.append(t); rows.append(row)
    for ic, cap, pin, supply, plane in [
        ('U3102', 'C3106', '4', '+12V', 'In4.Cu'), ('U3102', 'C3107', '11', '-12V', 'In3.Cu'),
        ('U3101', 'C3104', '13', '+12V', 'In4.Cu'), ('U3101', 'C3105', '4', '-12V', 'In3.Cu'),
        ('U3103', 'C3108', '4', '+12V', 'In4.Cu'), ('U3103', 'C3109', '11', '-12V', 'In3.Cu')]:
        face = fps[ic].GetLayer()
        if fps[cap].GetLayer() != face: raise ValueError('cross-face bypass')
        a, b = pad(ic, pin), pad(cap, '1')
        if a.GetNetname() != supply or b.GetNetname() != supply: raise ValueError('bypass net mismatch')
        if not segment_clear(a.GetPosition(), b.GetPosition(), supply): raise ValueError('blocked direct bypass ' + cap)
        add_segment(a.GetPosition(), b.GetPosition(), supply, cap + '-rail-link')
        paths.append({'role': 'IC-to-bypass supply', 'cap': cap, 'net': supply, 'from_pad': ic + ':' + pin, 'to_pad': cap + ':1', 'length_mm': math.dist(mm(a.GetPosition()), mm(b.GetPosition()))})
        for number, net, destination in [('1', supply, plane), ('2', 'AGND', 'In1.Cu')]:
            if pad(cap, number).GetNetname() != net:
                raise ValueError('fanout pad net mismatch')
            start = pad(cap, number).GetPosition(); chosen = None
            for radius in (1., 1.25, 1.5, 2., 2.5, 3.):
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
                    scale = radius/math.hypot(dx,dy)
                    end = pcbnew.VECTOR2I(start.x+pcbnew.FromMM(dx*scale), start.y+pcbnew.FromMM(dy*scale))
                    if segment_clear(start, end, net) and via_clear(end, net): chosen = end; break
                if chosen is not None: break
            if chosen is None: raise ValueError('no screened local fanout ' + cap + ':' + number)
            tag = cap + '-' + number
            add_segment(start, chosen, net, tag); add_via(chosen, net, tag)
            paths.append({'role': 'bypass ground return' if number == '2' else 'supply plane fanout', 'cap': cap, 'net': net, 'from_pad': cap + ':' + number, 'plane': destination, 'start_mm': mm(start), 'via_mm': mm(chosen), 'length_mm': math.dist(mm(start), mm(chosen)), 'vias': 1})
    proposal = {'board_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'removed_uuids': [], 'copper': rows}
    output.write_text(json.dumps(proposal, indent=2) + '\n')
    output.with_name(output.stem + '-paths.json').write_text(json.dumps({'paths': paths, 'status': 'GEOMETRIC PROPOSAL; actual plane connections not yet checked'}, indent=2) + '\n')
    print(json.dumps({'objects': len(rows), 'paths': paths}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('board', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); propose(a.board, a.output)
