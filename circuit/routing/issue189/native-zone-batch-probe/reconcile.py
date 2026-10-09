"""Independently bind a completed timing probe to source, saved fixtures and reports."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zipfile

sys.path.insert(0, str(Path.cwd()))
from scripts.pcbgen.probe_zone_batches import ARCHIVE_SHA, BEFORE_SHA, ZONE, INDICES, batch_text, identities
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts
from scripts.pcbgen.uuid_tools import top_level_spans, UUID_RE


def main(artifact, artifact_sha, source, golden, output):
    sha = lambda b: hashlib.sha256(b).hexdigest()
    assert sha(artifact.read_bytes()) == artifact_sha
    assert sha(golden.read_bytes()) == ARCHIVE_SHA
    assert sha(source.read_bytes()) == BEFORE_SHA
    text = source.read_text()
    artwork = set()
    for a, b in top_level_spans(text):
        block = text[a:b]
        kind = block[1:].split(None, 1)[0].rstrip(')')
        if kind == 'footprint' or ((kind.startswith('gr_') or kind in ('dimension', 'image')) and not re.search(r'\(layer "Edge.Cuts"\)', block)):
            artwork.add(UUID_RE.search(block)[1])
    parts = zone_fixture_parts(text, ZONE, artwork)
    context = {suffix: source.with_suffix(suffix).read_bytes() for suffix in ('.kicad_pro', '.kicad_dru')}
    with zipfile.ZipFile(artifact) as z, zipfile.ZipFile(golden) as old:
        names = [n for n in z.namelist() if n.endswith('/result.json') and 'zone-batch-result/' in n]
        assert len(names) == 1
        prefix = names[0][:-len('result.json')]
        result = json.loads(z.read(names[0]))
        assert result['status'] == 'BEFORE-ONLY SAMPLE EQUIVALENCE; NOT COMPLETE WARNING EVIDENCE; NEVER ACCEPTANCE'
        assert result['version'] == '10.0.6'
        assert result['before_sha256'] == BEFORE_SHA and result['archive_sha256'] == ARCHIVE_SHA
        assert result['indices'] == list(INDICES)
        assert [r['batch_size'] for r in result['trials']] == [1, 4, 16]
        assert result['context_sha256'] == {s: sha(b) for s, b in context.items()}
        single = result['trials'][0]['fixtures']
        assert len(single) == 16 and all(len(f['item_uuids']) == 1 for f in single)
        ids = [f['item_uuids'][0] for f in single]
        assert len(set(ids)) == 16
        expected_sets = []
        for index, uid in zip(INDICES, ids):
            old_prefix = f'zone-{ZONE}/0-{index:04d}/'
            new_prefix = prefix + f'golden/{index:04d}/'
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
                name = source.stem + suffix
                assert z.read(new_prefix + name) == old.read(old_prefix + name)
            assert z.read(new_prefix + 'drc.json') == old.read(old_prefix + 'drc.json')
            assert batch_text(parts, [uid]).encode() == old.read(old_prefix + source.name)
            expected_sets.append(identities(json.loads(old.read(old_prefix + 'drc.json'))))
        geometries = set()
        for trial in result['trials']:
            size = trial['batch_size']
            assert len(trial['fixtures']) == math.ceil(16 / size)
            assert math.isfinite(trial['elapsed_seconds']) and trial['elapsed_seconds'] > 0
            for start, fixture in zip(range(0, 16, size), trial['fixtures']):
                chunk = ids[start:start + size]
                assert fixture['item_uuids'] == chunk
                folder = prefix + f'batch-{size}/{start:04d}/'
                board_bytes = z.read(folder + source.name)
                assert board_bytes == batch_text(parts, chunk).encode()
                assert sha(board_bytes) == fixture['fixture_sha256']
                for suffix, data in context.items():
                    assert z.read(folder + source.stem + suffix) == data
                report = z.read(folder + 'drc.json')
                assert sha(report) == fixture['report_sha256']
                actual = identities(json.loads(report))
                assert actual == set().union(*expected_sets[start:start + size])
                assert actual == {(a, b, tuple(c)) for a, b, c in fixture['identities']}
                assert 0 < fixture['native_drc_seconds'] <= fixture['fixture_seconds']
                geometries.add(fixture['native_geometry_sha256'])
            assert sum(f['fixture_seconds'] for f in trial['fixtures']) <= trial['elapsed_seconds']
        assert len(geometries) == 1 and re.fullmatch('[0-9a-f]{64}', next(iter(geometries)))
        baseline = result['trials'][0]['elapsed_seconds']
        comparisons = [dict(batch_size=t['batch_size'], elapsed_seconds=t['elapsed_seconds'],
                            speedup=baseline / t['elapsed_seconds']) for t in result['trials']]
        receipt = dict(status='RECONCILED BEFORE-ONLY TIMING SAMPLE; NEVER ACCEPTANCE',
            artifact_sha256=artifact_sha, source_sha256=BEFORE_SHA, golden_sha256=ARCHIVE_SHA,
            raw_reports_verified=37, single_item_count=16, comparisons=comparisons,
            meets_predeclared_2x=any(c['speedup'] >= 2 for c in comparisons[1:]),
            positive_native_detection='NOT ESTABLISHED BY THIS ALL-NEGATIVE SAMPLE',
            full_paired_zone_coverage=False, adopted=False)
        output.write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('artifact', type=Path)
    parser.add_argument('artifact_sha')
    parser.add_argument('source', type=Path)
    parser.add_argument('golden', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.artifact, args.artifact_sha, args.source, args.golden, args.output)
