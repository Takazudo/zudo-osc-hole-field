"""Printed spacer models for the board stack (DS-45): plain sleeves as binary STL.

  python3 scripts/stack/spacers/spacers.py           write design/stack/spacers/generated/*.stl
  python3 scripts/stack/spacers/spacers.py --check   fail if a retained file differs from the parameter list

The parameter list is design/stack/spacers/spacer-set.json. A model is geometry only: nothing here is a
measured length, a fit or a load rating.
"""
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / 'design/stack/spacers/spacer-set.json'
OUT = ROOT / 'design/stack/spacers/generated'


def load(path=SPEC):
    return json.loads(Path(path).read_text())


def snap(x):
    """Vertices sit on a 0.1 micrometre grid, so the bytes do not depend on the platform's sin and cos."""
    return round(x * 10000) / 10000 + 0.0


def length_mm(spec, member):
    return snap(member['gap_mm'] + spec['length_allowance_mm'])


def ring(radius, facets, cx, cy):
    return [(snap(cx + radius * math.cos(2 * math.pi * i / facets)),
             snap(cy + radius * math.sin(2 * math.pi * i / facets))) for i in range(facets)]


def sleeve(outer_d, bore_d, length, facets, cx=0.0, cy=0.0):
    """Triangles of a tube standing on z = 0, each wound counter-clockwise seen from outside the solid."""
    o, b, z1 = ring(outer_d / 2, facets, cx, cy), ring(bore_d / 2, facets, cx, cy), snap(length)
    tris = []
    for i in range(facets):
        j = (i + 1) % facets
        ob0, ob1, ot0, ot1 = (*o[i], 0.0), (*o[j], 0.0), (*o[i], z1), (*o[j], z1)
        bb0, bb1, bt0, bt1 = (*b[i], 0.0), (*b[j], 0.0), (*b[i], z1), (*b[j], z1)
        tris += [(ob0, ob1, ot1), (ob0, ot1, ot0),   # outer wall
                 (bb0, bt1, bb1), (bb0, bt0, bt1),   # bore wall
                 (ot0, ot1, bt1), (ot0, bt1, bt0),   # top face
                 (ob0, bb1, ob1), (ob0, bb0, bb1)]   # bottom face
    return tris


def normal(tri):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    ux, uy, uz, vx, vy, vz = bx - ax, by - ay, bz - az, cx - ax, cy - ay, cz - az
    n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    k = math.sqrt(sum(c * c for c in n))
    return tuple(round(c / k, 6) + 0.0 for c in n)


def stl_bytes(title, tris):
    header = ('binary STL; %s; units mm; candidate for an unvalidated draft' % title).encode('ascii')
    assert len(header) <= 80 and not header.startswith(b'solid'), title
    out = [header.ljust(80, b' '), struct.pack('<I', len(tris))]
    for tri in tris:
        out.append(struct.pack('<12fH', *normal(tri), *tri[0], *tri[1], *tri[2], 0))
    return b''.join(out)


def plate_positions(spec):
    """Centres of every piece on the plate: one block per member, the members apart by the group gap."""
    pitch, y0, out = spec['plate']['pitch_mm'], 0.0, []
    for m in spec['members']:
        count, cols = m['quantity'] + m['spares'], m['plate_columns']
        rows = math.ceil(count / cols)
        out += [(m, (k % cols) * pitch, y0 + (k // cols) * pitch) for k in range(count)]
        y0 += (rows - 1) * pitch + spec['plate']['group_gap_mm']
    return out


def outputs(spec=None):
    """File name -> bytes for every retained model."""
    spec = spec or load()
    s = spec['sleeve']

    def tube(m, cx=0.0, cy=0.0):
        return sleeve(s['outer_diameter_mm'], s['bore_diameter_mm'], length_mm(spec, m), s['facets'], cx, cy)

    files = {m['file']: stl_bytes('%s length %.1f' % (m['id'], length_mm(spec, m)), tube(m)) for m in spec['members']}
    plate = [t for m, x, y in plate_positions(spec) for t in tube(m, x, y)]
    files[spec['plate']['file']] = stl_bytes('spacer set plate', plate)
    return files


def main(argv):
    files = outputs()
    if '--check' in argv:
        stale = [n for n, data in files.items() if not (OUT / n).is_file() or (OUT / n).read_bytes() != data]
        extra = sorted(p.name for p in OUT.glob('*') if p.name not in files) if OUT.is_dir() else []
        if stale or extra:
            print('FAIL: differs from the parameter list: %s; not generated here: %s' % (stale, extra))
            return 1
        print('PASS: %d retained models match the parameter list' % len(files))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (OUT / name).write_bytes(data)
        print('wrote %s (%d triangles)' % (name, (len(data) - 84) // 50))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
