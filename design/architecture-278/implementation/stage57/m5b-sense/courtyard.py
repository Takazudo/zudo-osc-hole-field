"""Report courtyard contact of the Stage57 added copper (oracle only). Report, never clearance proof.

Usage (through scripts/kicad/run.sh): courtyard.py BOARD PROPOSAL OUTPUT
"""
from pathlib import Path
import hashlib, json, sys
import pcbnew


def main(board_path, proposal_path, output):
    board = pcbnew.LoadBoard(str(board_path)); proposal = json.loads(Path(proposal_path).read_text())
    new = {r['uuid'] for r in proposal['copper']}
    items = [t for t in board.GetTracks() if t.m_Uuid.AsString() in new]
    if len(items) != len(new): raise ValueError('added copper not found')
    rows = []
    for f in board.GetFootprints():
        for side, layer in (('front', pcbnew.F_CrtYd), ('back', pcbnew.B_CrtYd)):
            cy = f.GetCourtyard(layer)
            if cy.OutlineCount() == 0: continue
            for t in items:
                is_via = t.GetClass() == 'PCB_VIA'
                cu_layers = (pcbnew.F_Cu, pcbnew.B_Cu) if is_via else (t.GetLayer(),)
                if not is_via and t.GetLayer() not in (pcbnew.F_Cu, pcbnew.B_Cu): continue  # inner tracks: no courtyard layer
                if not is_via and (t.GetLayer() == pcbnew.F_Cu) != (side == 'front'): continue
                shape = pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(shape, cu_layers[0] if side == 'front' or not is_via else pcbnew.B_Cu, 0, 5000, pcbnew.ERROR_INSIDE)
                inter = pcbnew.SHAPE_POLY_SET(shape); inter.BooleanIntersection(cy)
                if inter.OutlineCount():
                    rows.append(dict(ref=f.GetReference(), courtyard=side, uuid=t.m_Uuid.AsString(),
                                     kind='via' if is_via else 'segment', overlap_area_mm2=round(inter.Area() / 1e12, 6)))
    rows.sort(key=lambda r: (r['ref'], r['courtyard'], r['uuid']))
    out = dict(board_sha256=hashlib.sha256(Path(board_path).read_bytes()).hexdigest(), added_objects=len(items), contacts=rows,
               note='Courtyard contact is reported, never used as clearance or assembly proof.')
    Path(output).write_text(json.dumps(out, indent=2, sort_keys=True) + '\n'); print(json.dumps(dict(contacts=len(rows), refs=sorted({r['ref'] for r in rows}))))


if __name__ == '__main__':
    main(*sys.argv[1:4])
