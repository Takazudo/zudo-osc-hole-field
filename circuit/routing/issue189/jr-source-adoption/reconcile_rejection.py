"""Verify the immutable failed source pilot without extracting or adopting files."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path.cwd()))
from scripts.pcbgen.route_jack_grid import connectivity_signature, promotion_gate

archive = Path(sys.argv[1])
assert hashlib.sha256(archive.read_bytes()).hexdigest() == 'd22721f7545bf34ef439805c6dbe61d8e78f1368b21478e7dc7051b2ff8acce7'
with zipfile.ZipFile(archive) as z:
    read = lambda n: json.loads(z.read(n))
    result = read('issue189-jr-source-adoption/result.json')
    assert result['source_commit'] == 'acabdda6118fde6623defe811a0493ba3eeef830'
    assert result['status'] == 'ERROR; NOT ADOPTED'
    assert not result['adopted'] and not result['source_regenerated']
    assert result['all_canonical_pcbs_unchanged']
    for p, digest in result['canonical_board_sha256'].items():
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest
    dumps, reports, receipts = {}, {}, {}
    for stage in ('base', 'candidate', 'fresh'):
        prefix = 'osc-jack-right-grid-189-jr-rb4413-' + stage + '/'
        pcb = z.read(prefix + 'osc-jack-right.kicad_pcb')
        digest = hashlib.sha256(pcb).hexdigest()
        expected = ('35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445' if stage == 'base'
                    else 'ae6e998c8b490394c6d3f7e2749e7d1521b4f9c6120067358a6bdf766cead5ff')
        assert digest == expected
        dumps[stage] = read(prefix + 'dump.json')
        reports[stage] = read(prefix + 'drc.json')
        assert dumps[stage]['board_sha256'] == digest
        assert reports[stage]['kicad_version'] == '10.0.6'
        assert not reports[stage]['schematic_parity']
        assert not any(v['severity'] == 'error' for v in reports[stage]['violations'])
        receipts[stage] = dict(board_sha256=digest, open_edges=dumps[stage]['open_edges'],
            drc_sha256=hashlib.sha256(z.read(prefix + 'drc.json')).hexdigest(),
            dump_sha256=hashlib.sha256(z.read(prefix + 'dump.json')).hexdigest())
    for stage in ('candidate', 'fresh'):
        gate = promotion_gate(dumps['base'], dumps[stage], reports['base'], reports[stage])
        assert gate['adopted']
        receipts[stage]['ordinary_gate'] = gate
    assert connectivity_signature(dumps['candidate']) == connectivity_signature(dumps['fresh'])
    patch = z.read('issue189-jr-source-adoption/generated.patch')
    assert b'native J courtyard clearance J900069 RB4413 0.05999999999998096' in patch
    print(json.dumps(dict(status='REJECTED SOURCE; ORDINARY NATIVE REPLAY VERIFIED; NOT ADOPTED',
        stages=receipts, native_courtyard_gap_mm=.06, required_mm=.25,
        all_canonical_pcbs_unchanged=True, source_sync_and_repeats='NOT RUN'), indent=2))
