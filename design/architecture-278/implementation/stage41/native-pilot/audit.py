"""Complete baseline identity gate before/after native connectivity calls."""
from pathlib import Path
from collections import Counter
import argparse
import json
import re
import sys
import pcbnew
from identity_guard import inventory, compare, digest, kind, structure_matches, bound_retirements
from native_guard import check_native
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans


def proposed_contract(row):
    if row['kind'] == 'segment':
        shape = (tuple(row['start_nm']), tuple(row['end_nm']), (row['width_nm'],), row['layer'])
    elif row['kind'] == 'via':
        shape = (tuple(row['at_nm']), (row['diameter_nm'],), (row['drill_nm'],), tuple(row['layers']))
    else:
        raise ValueError('unknown proposal object')
    return row['kind'], row['uuid'], shape, row['net']


def audit(path, receipt_path, proposals=()):
    source = ROOT / 'boards/osc-jack-left/osc-jack-left.kicad_pcb'
    original, raw = source.read_text(), path.read_text()
    receipt = json.loads(receipt_path.read_text())
    if pcbnew.GetBuildVersion() != '10.0.6' or digest(original) != receipt['canonical_sha256']:
        raise ValueError('version/baseline binding')
    before, after = inventory(original), inventory(raw)
    rows = []
    for p in proposals:
        proposal = json.loads(p.read_text())
        if proposal['removed_uuids']:
            raise ValueError('route proposal may not remove copper')
        rows += proposal['copper']
    allowed_nets = set(receipt['private_net_owners']) | {'+12V', '-12V', 'AGND'}
    if any(r['net'] not in allowed_nets for r in rows):
        raise ValueError('proposal net outside explicit pilot allowlist')
    ids = [r['uuid'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('proposal UUID collision')
    expected_new = Counter(proposed_contract(r) for r in rows)
    actual_new = Counter({k: v for k, v in after['native_contract'].items() if k[1] in ids})
    if actual_new != expected_new:
        raise ValueError('route geometry/net differs from explicit proposal')
    allowed = [k for k, n in after['copper'].items() if k[1] in ids for _ in range(n)]
    gate = compare(before, after, [r['sha256'] for r in bound_retirements(receipt, original)], allowed)
    if not structure_matches(before, after, receipt['prepared_footprint_hashes']):
        raise ValueError('prepared/foreign footprint or other board-object bytes changed')
    if not gate['accepted']:
        raise ValueError('complete raw identity gate: ' + json.dumps(gate))
    def foreign(text):
        result = Counter()
        for a, z in top_level_spans(text):
            part = text[a:z]
            if kind(part) == 'footprint':
                ref = re.search(r'\(property\s+"Reference"\s+"([^"\\]*)"', part)[1]
                if ref not in receipt['scope_refs']:
                    result[digest(part)] += 1
        return result
    if foreign(original) != foreign(raw):
        raise ValueError('foreign/fixed footprint byte change')
    for suffix in ('.kicad_pro', '.kicad_dru', '.kicad_sch'):
        if path.with_suffix(suffix).read_bytes() != source.with_suffix(suffix).read_bytes():
            raise ValueError('project/rules/schematic changed: ' + suffix)
    b = pcbnew.LoadBoard(str(path))
    check_native(b, raw)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    for pose in receipt['poses']:
        f = fps[pose['ref']]
        if f.GetLayer() != b.GetLayerID(pose['layer']) or abs(f.GetOrientationDegrees() % 360 - pose['native_angle'] % 360) > 1e-6:
            raise ValueError('pilot face/orientation changed')
        for q in pose['pads']:
            p = next(p for p in f.Pads() if p.m_Uuid.AsString() == q['uuid'])
            actual = (p.GetPosition().x, p.GetPosition().y)
            expected = tuple(round(v * 1000000) for v in q['xy_mm'])
            if actual != expected:
                raise ValueError('pilot pad pose changed')
    b.GetConnectivity().RecalculateRatsnest()
    check_native(b, raw)
    result = {'accepted_identity_only': True, 'raw_sha256': digest(raw), 'canonical_sha256': digest(original),
              'receipt_sha256': digest(receipt_path.read_text()),
              'proposal_sha256': [digest(p.read_text()) for p in proposals],
              'new_objects': len(rows), 'rule_area_count': sum(after['rules'].values()),
              'native_open_edges': b.GetConnectivity().GetUnconnectedCount(False),
              'checks': gate['checks'], 'foreign_fixed_footprints_byte_equal': True,
              'limits': 'Identity/pose gate only. DRC, complete connectivity and loop geometry are separate.'}
    path.with_name('identity-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('board', type=Path); p.add_argument('receipt', type=Path)
    p.add_argument('--proposal', type=Path, action='append', default=[]); a = p.parse_args()
    audit(a.board, a.receipt, a.proposal)
