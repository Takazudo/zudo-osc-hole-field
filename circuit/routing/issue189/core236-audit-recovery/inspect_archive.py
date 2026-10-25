"""Read-only immutable archive inventory; no native reconstruction or adoption."""
import argparse, hashlib, json, pathlib, sys, zipfile

EXPECTED = 'd02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5'

def inspect(archive, output):
    output.mkdir(parents=True, exist_ok=False)
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == EXPECTED
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert len(names) == len(set(names))
        assert all(not pathlib.PurePosixPath(n).is_absolute() and '..' not in pathlib.PurePosixPath(n).parts for n in names)
        inventory = []
        for name in names:
            if name.endswith('/'):
                continue
            with z.open(name) as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            inventory.append(dict(path=name, bytes=z.getinfo(name).file_size, sha256=digest))
        def find(suffix):
            matches = [n for n in names if n.endswith(suffix)]
            assert len(matches) == 1, (suffix, matches)
            return matches[0]
        def read(suffix):
            return json.loads(z.read(find(suffix)))
        zones = find('osc-core-grid-shards-complete-warnings/native-audits/zones/result.json')[:-len('result.json')]
        zr = json.loads(z.read(zones+'result.json'))
        assert zr['status'] == 'STARTED; NO COMPLETE ZONE EVIDENCE'
        assert zr['version'] == '10.0.6'
        progress = []
        for scope_name in sorted(n for n in names if n.startswith(zones) and n.endswith('-scope.json')):
            scope = json.loads(z.read(scope_name)); uid = scope['zone_uuid']
            selected = scope['selected_item_uuids']; assert selected == sorted(set(selected))
            batches = [selected[i:i+16] for i in range(0, len(selected), 16)]
            expected = [(s, i, b) for s in (0, 1) for i, b in enumerate(batches)]
            rows = [json.loads(line) for line in z.read(zones+'zone-'+uid+'-progress.jsonl').decode().splitlines()]
            assert [(r['stage'], r['batch_index'], r['item_uuids']) for r in rows] == expected[:len(rows)]
            for row in rows:
                folder = zones+'zone-'+uid+f"/{row['stage']}-batch-{row['batch_index']:04d}/"
                fixture = z.read(find(folder+'osc-core.kicad_pcb'))
                report = z.read(find(folder+'drc.json'))
                assert hashlib.sha256(fixture).hexdigest() == row['fixture_sha256']
                assert hashlib.sha256(report).hexdigest() == row['report_sha256']
                d = json.loads(report)
                assert d['kicad_version'] == '10.0.6' and set(d['included_severities']) == {'error','warning','exclusion'}
                for suffix in ('.kicad_pro','.kicad_dru'):
                    source = f"osc-core-grid-shards-{'start' if row['stage']==0 else 'fresh'}/osc-core"+suffix
                    assert z.read(find(folder+'osc-core'+suffix)) == z.read(find(source))
            progress.append(dict(zone_uuid=uid, selected_artwork=len(selected), planned_paired_batches=len(expected), hash_verified_completed_prefix=len(rows), remaining_in_this_zone=len(expected)-len(rows), next_pair=expected[len(rows)][:2] if len(rows)<len(expected) else None))
        # A compact export retains all raw non-zone audits, stages and logs.
        # Completed zone fixture bytes stay in the immutable original archive.
        with zipfile.ZipFile(output/'reconciliation-inputs.zip','w',zipfile.ZIP_DEFLATED) as small:
            for name in names:
                if name.endswith('/') or (name.startswith(zones) and '/' in name[len(zones):]):
                    continue
                small.writestr(name,z.read(name))
        result = dict(status='IMMUTABLE ARCHIVE AND SAVED PREFIX HASH INVENTORY ONLY; NATIVE RECONSTRUCTION/ACCEPTANCE NOT RUN', run=38044514132, source='4768f2f82e8a4d634f8dc2905429616bfcd20c37', artifact=11671963117, artifact_sha256=EXPECTED, archive_bytes=archive.stat().st_size, uncompressed_bytes=sum(r['bytes'] for r in inventory), inventory=inventory, zone_result=zr, zones=progress, later_zone_coverage='UNKNOWN UNTIL FULL NATIVE CLASSIFICATION', full_warning_proof_present=any(n.endswith('native-audits/proof.json') for n in names), subset_sha256=hashlib.sha256((output/'reconciliation-inputs.zip').read_bytes()).hexdigest())
        (output/'archive-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='inventory'},indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('archive',type=pathlib.Path); parser.add_argument('output',type=pathlib.Path)
    args=parser.parse_args(); inspect(args.archive,args.output)
