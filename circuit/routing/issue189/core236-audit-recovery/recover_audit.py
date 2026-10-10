"""Extract pinned saved evidence or combine complete audit; never reroute/publish."""
import argparse,hashlib,json,pathlib,sys,zipfile
sys.path.insert(0,str(pathlib.Path.cwd()))
SHA='d02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5'
BEFORE='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'
AFTER='f27efe521f4ed4f6c0ceb53f45f58a82a824c05475ef012a2034a0d1d2a154d1'

def extract(archive,destination,manifest_path):
    with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==SHA
    manifest=json.loads(manifest_path.read_text());assert manifest['artifact_sha256']==SHA and manifest['archive_bytes']==archive.stat().st_size
    inventory={r['path']:r for r in manifest['inventory']}
    destination.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        assert {n for n in z.namelist() if not n.endswith('/')}==set(inventory)
        for item in z.infolist():
            if item.is_dir():continue
            relative=pathlib.PurePosixPath(item.filename)
            assert not relative.is_absolute() and '..' not in relative.parts and (item.external_attr>>16)&0o170000!=0o120000
            data=z.read(item);r=inventory[item.filename]
            assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
            path=destination/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    for stage,expected in [('start',BEFORE),('merge',AFTER),('fresh',AFTER)]:
        p=destination/'.circuit-cache'/('osc-core-grid-shards-'+stage)/'osc-core.kicad_pcb'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
    print('Exact original archive and all inventory entries extracted; no native execution or adoption')

def combine(root,zones,output):
    from scripts.pcbgen.complete_native_warnings import complete_reports
    from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
    root=root/'.circuit-cache';before=root/'osc-core-grid-shards-start';fresh=root/'osc-core-grid-shards-fresh';merge=root/'osc-core-grid-shards-merge'
    boards=[p/'osc-core.kicad_pcb' for p in (before,fresh)]
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in boards]==[BEFORE,AFTER]
    read=lambda p:json.loads(p.read_text());audits=root/'osc-core-grid-shards-complete-warnings/native-audits'
    a,b,proof=complete_reports(*boards,read(before/'drc.json'),read(fresh/'drc.json'),audits/'holes-before',audits/'holes-after',audits/'silk',zones)
    start_dump=read(before/'dump.json');fresh_dump=read(fresh/'dump.json');merge_dump=read(merge/'dump.json')
    assert start_dump['open_edges']==1402 and fresh_dump['open_edges']==merge_dump['open_edges']==1312
    assert connectivity_signature(merge_dump)==connectivity_signature(fresh_dump)
    gate=promotion_gate(start_dump,fresh_dump,a,b)
    assert gate['adopted'] and not gate['native_errors'] and not gate['split_pad_groups'] and not gate['new_warning_identities'],gate
    output.mkdir(parents=True,exist_ok=False)
    for name,value in [('complete-before-drc',a),('complete-after-drc',b),('complete-warning-proof',proof),('eligibility',dict(status='COMPLETE SAVED NATIVE WARNING EVIDENCE ELIGIBLE; NO ADOPTION/PUBLICATION',adopted=False,source_artifact=11671963117,source_archive_sha256=SHA,before_sha256=BEFORE,after_sha256=AFTER,gate=gate,publication_equivalence='REQUIRED; NOT RUN BY THIS READ-ONLY JOB'))]:
        (output/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    print('Complete warning/promotion proof eligible; no canonical board changed; publication gate remains')

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    e=sub.add_parser('extract');e.add_argument('archive',type=pathlib.Path);e.add_argument('destination',type=pathlib.Path);e.add_argument('manifest',type=pathlib.Path)
    c=sub.add_parser('combine');c.add_argument('root',type=pathlib.Path);c.add_argument('zones',type=pathlib.Path);c.add_argument('output',type=pathlib.Path)
    a=p.parse_args()
    if a.mode=='extract':extract(a.archive,a.destination,a.manifest)
    else:combine(a.root,a.zones,a.output)
