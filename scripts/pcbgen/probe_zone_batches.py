"""Read-only timing/equivalence probe; never supplies board acceptance evidence.

Compare batches of 1/4/16 artwork items against the same 16 saved native
single-item reports from the incomplete issue189 zone run. Only the before
board is covered. A passing probe does not certify after-board warnings.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.audit_added_mask import new_silk_identities
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts, native_zone_signature

ARCHIVE_SHA = '925d83879571b2127af73526ead4cef86472138f3093fc909dfcf19a22f54c1b'
BEFORE_SHA = '95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5'
ZONE = '601e02b2-8ccb-5c28-83e5-03789d47fbbd'
INDICES = tuple(round(i * 133 / 15) for i in range(16))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def batch_text(parts, selected):
    selected = list(selected)
    known = {uid for uid, _ in parts if uid is not None}
    if not selected or len(selected) != len(set(selected)) or not set(selected) <= known:
        raise ValueError('empty, duplicate or unknown artwork selection')
    return ''.join(block for uid, block in parts if uid is None or uid in selected)


def identities(report):
    if report.get('kicad_version') != '10.0.6':
        raise ValueError('report native version mismatch')
    return {(v['type'], v['severity'], tuple(sorted(i['uuid'] for i in v['items'])))
            for v in new_silk_identities(report, ZONE)}


def artwork(board, pcbnew):
    return [*board.GetFootprints(),
            *(x for x in board.GetDrawings() if x.GetLayer() != pcbnew.Edge_Cuts)]


def shown_text(board):
    objects = list(board.GetDrawings())
    for fp in board.GetFootprints():
        objects.extend([*fp.GetFields(), *fp.GraphicalItems()])
    return {x.m_Uuid.AsString(): x.GetShownText(True)
            for x in objects if hasattr(x, 'GetShownText')}


def main(before, archive, output):
    import pcbnew
    version = subprocess.check_output(['kicad-cli', 'version'], text=True).strip()
    if version != '10.0.6' or sha(before) != BEFORE_SHA or sha(archive) != ARCHIVE_SHA:
        raise ValueError('pinned native version or immutable input mismatch')
    output.mkdir(parents=True, exist_ok=False)
    result = dict(status='STARTED; NO EQUIVALENCE RESULT; NEVER ACCEPTANCE',
                  version=version, before_sha256=BEFORE_SHA, archive_sha256=ARCHIVE_SHA,
                  indices=INDICES, scope='16 before-board artwork items only', trials=[])
    result_path = output / 'result.json'
    result_path.write_text(json.dumps(result, indent=2) + '\n')
    source = pcbnew.LoadBoard(str(before))
    source_text = shown_text(source)
    signature = native_zone_signature(next(z for z in source.Zones()
                                          if z.m_Uuid.AsString() == ZONE).GetFilledPolysList(pcbnew.F_Cu))
    parts = zone_fixture_parts(before.read_text(), ZONE,
                               {x.m_Uuid.AsString() for x in artwork(source, pcbnew)})
    context = {suffix: before.with_suffix(suffix).read_bytes()
               for suffix in ('.kicad_pro', '.kicad_dru')}
    result['context_sha256'] = {s: hashlib.sha256(b).hexdigest() for s, b in context.items()}

    def verify(path, expected_ids):
        board = pcbnew.LoadBoard(str(path))
        zones = list(board.Zones())
        if len(zones) != 1 or zones[0].m_Uuid.AsString() != ZONE:
            raise ValueError('fixture zone identity mismatch')
        if native_zone_signature(zones[0].GetFilledPolysList(pcbnew.F_Cu)) != signature:
            raise ValueError('fixture native zone geometry mismatch')
        if list(board.GetTracks()) or any(list(fp.Pads()) for fp in board.GetFootprints()):
            raise ValueError('fixture retained unrelated copper')
        actual_ids = [x.m_Uuid.AsString() for x in artwork(board, pcbnew)]
        if len(actual_ids) != len(set(actual_ids)) or (expected_ids is not None and set(actual_ids) != set(expected_ids)):
            raise ValueError('fixture artwork scope mismatch')
        if any(source_text.get(k) != v for k, v in shown_text(board).items()):
            raise ValueError('fixture rendered text changed')
        for suffix, data in context.items():
            if path.with_suffix(suffix).read_bytes() != data:
                raise ValueError('fixture project/rules changed')
        return actual_ids

    golden = []
    with zipfile.ZipFile(archive) as saved:
        if json.loads(saved.read('result.json'))['before_sha256'] != BEFORE_SHA:
            raise ValueError('saved source mismatch')
        for index in INDICES:
            prefix = f'zone-{ZONE}/0-{index:04d}'
            folder = output / 'golden' / f'{index:04d}'
            folder.mkdir(parents=True)
            path = folder / before.name
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
                path.with_suffix(suffix).write_bytes(saved.read(f'{prefix}/{before.stem}{suffix}'))
            report_bytes = saved.read(f'{prefix}/drc.json')
            (folder / 'drc.json').write_bytes(report_bytes)
            ids = verify(path, None)
            if len(ids) != 1:
                raise ValueError('golden fixture is not a single artwork item')
            expected = identities(json.loads(report_bytes))
            if batch_text(parts, ids).encode() != path.read_bytes():
                raise ValueError('golden fixture source bytes differ from reconstruction')
            golden.append((ids[0], expected))
    if len({uid for uid, _ in golden}) != len(INDICES):
        raise ValueError('golden artwork scope is ambiguous')

    for size in (1, 4, 16):
        trial = dict(batch_size=size, fixtures=[], elapsed_seconds=None)
        started = time.monotonic()
        for start in range(0, len(golden), size):
            chunk = golden[start:start + size]
            ids = [uid for uid, _ in chunk]
            expected = set().union(*(rows for _, rows in chunk))
            folder = output / f'batch-{size}' / f'{start:04d}'
            folder.mkdir(parents=True)
            path = folder / before.name
            fixture_start = time.monotonic()
            path.write_text(batch_text(parts, ids))
            for suffix, data in context.items():
                path.with_suffix(suffix).write_bytes(data)
            verify(path, ids)
            report = folder / 'drc.json'
            native_start = time.monotonic()
            subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all',
                            '--output', str(report), str(path)], check=True, stdout=subprocess.DEVNULL)
            native_elapsed = time.monotonic() - native_start
            verify(path, ids)
            actual = identities(json.loads(report.read_text()))
            if actual != expected:
                raise ValueError('batch warning identities differ from golden single-item union')
            trial['fixtures'].append(dict(item_uuids=ids, fixture_sha256=sha(path),
                report_sha256=sha(report), native_geometry_sha256=signature,
                identities=sorted(actual), native_drc_seconds=native_elapsed,
                fixture_seconds=time.monotonic() - fixture_start))
            print(f'batch{size} items{start}:{start+len(chunk)} exact identities{len(actual)}', flush=True)
        trial['elapsed_seconds'] = time.monotonic() - started
        result['trials'].append(trial)
        result_path.write_text(json.dumps(result, indent=2) + '\n')
    result['status'] = 'BEFORE-ONLY SAMPLE EQUIVALENCE; NOT COMPLETE WARNING EVIDENCE; NEVER ACCEPTANCE'
    result_path.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.before, args.archive, args.output)
