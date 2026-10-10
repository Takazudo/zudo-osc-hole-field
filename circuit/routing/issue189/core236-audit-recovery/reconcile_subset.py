"""Independently reconcile rejected core236 saved native snapshots; no adoption."""
import collections,hashlib,importlib.util,json,re,subprocess,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups,delta
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata

source='4768f2f82e8a4d634f8dc2905429616bfcd20c37';bid='osc-core'
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda p:subprocess.check_output(['git','show',source+':'+p])
archive=Path(sys.argv[1]);manifest=json.loads(Path(sys.argv[2]).read_text());output=Path(sys.argv[3])
assert manifest['artifact_sha256']=='d02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5'
assert manifest['archive_bytes']==713393322 and sha(archive.read_bytes())==manifest['subset_sha256']
assert not manifest['full_warning_proof_present']
board=blob('boards/osc-core/osc-core.kicad_pcb');assert sha(board)=='fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10'
proposal=json.loads(blob('circuit/routing/issue189/core-supply-two-split-guards/proposal.json'));assert len(proposal['copper'])==115 and not proposal['removed_uuids']
spec=importlib.util.spec_from_file_location('guard',Path.cwd()/'circuit/routing/issue189/core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
inventory={r['path']:r for r in manifest['inventory']};stages={};summaries={}
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist())==len(set(z.namelist()))
    for n in z.namelist():
        data=z.read(n);assert len(data)==inventory[n]['bytes'] and sha(data)==inventory[n]['sha256']
    def path(s):
        rows=[n for n in z.namelist() if n.endswith(s)];assert len(rows)==1,(s,rows);return rows[0]
    def read(s):return json.loads(z.read(path(s)))
    receipt=read('boards/osc-core/reports/grid-routing/shards-issue189-supply-two-split-guards.json')
    assert not receipt['adopted'] and receipt['rejection_reason']=='incomplete_native_warning_evidence'
    assert receipt['copper_added']==115 and receipt['copper_removed']==0 and receipt['independent_connectivity_agrees']
    baseline=collections.Counter(b for rows in copper_block_groups(board.decode()).values() for b in rows);assert sum(baseline.values())==133551
    for key in ('start','merge','fresh'):
        folder='osc-core-grid-shards-'+key;raw=z.read(path(folder+'/osc-core.kicad_pcb'));dump=read(folder+'/dump.json');drc=read(folder+'/drc.json')
        assert sha(raw)==dump['board_sha256'];assert drc['kicad_version']=='10.0.6' and not drc['schematic_parity'] and not any(v['severity']=='error' for v in drc['violations'])
        for suffix in ('.kicad_pro','.kicad_dru'):assert z.read(path(folder+'/osc-core'+suffix))==blob('boards/osc-core/osc-core'+suffix)
        if key=='start':
            assert sha(raw)=='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66';before=dump;before_drc=drc
        for field in ('pads','edges','keepouts','layers'):assert dump[field]==before[field]
        assert zone_metadata(raw.decode())==zone_metadata(board.decode());assert unchanged_nonrouting(board.decode(),raw.decode())==3807
        counts=collections.Counter(b for rows in copper_block_groups(raw.decode()).values() for b in rows);assert not baseline-counts
        change=delta(board.decode(),raw.decode());expected=[] if key=='start' else proposal['copper']
        assert not change['removed'] and len(change['added'])==len(expected)
        assert {r['uuid'] for r in change['added']}=={r['uuid'] for r in expected};guard.require_known_geometry(change['added'],expected)
        assert dump['open_edges']==(1402 if key=='start' else 1312)
        gate=promotion_gate(before,dump,before_drc,drc)
        if key!='start':assert gate['adopted'] and not gate['split_pad_groups'] and not gate['new_warning_identities'] and not gate['native_errors']
        stages[key]=dump;summaries[key]=dict(board_sha256=sha(raw),dump_sha256=sha(z.read(path(folder+'/dump.json'))),drc_sha256=sha(z.read(path(folder+'/drc.json'))),open_edges=dump['open_edges'],open_by_rails={n:len(dump['islands'][n])-1 for n in ('AGND','+12V','-12V')},drc_errors=0,parity=0,retained_copper=133551,added=len(expected),removed=0,unchanged_nonrouting=3807,raw_gate=gate)
    assert connectivity_signature(stages['merge'])==connectivity_signature(stages['fresh'])
    assert summaries['merge']['board_sha256']==summaries['fresh']['board_sha256']==receipt['candidate_board_sha256']=='f27efe521f4ed4f6c0ceb53f45f58a82a824c05475ef012a2034a0d1d2a154d1'
    assert json.loads(json.dumps(summaries['fresh']['raw_gate']))==receipt['raw_promotion_gate']
    log=z.read(path('adoption.log'));settled=[]
    for step,count in re.findall(r'refill pass (\d+): (\d+) open edges',log.decode()):
        if int(step)==1:settled.append([])
        assert int(step)==len(settled[-1])+1;settled[-1].append(int(count))
    assert settled==[[1402]*3,[1312]*3,[1312]*3]
    replay=z.read(path(receipt['copper_replay']['path']));assert sha(replay)==receipt['copper_replay']['sha256']
    copper=json.loads(replay);assert not copper['removed'] and len(copper['added'])==115 and copper['base_sha256']==sha(board);guard.require_known_geometry(copper['added'],proposal['copper'])
    result=dict(status='REJECTED CANDIDATE RECONCILED; COMPLETE WARNING AUDIT AND PUBLICATION GATES STILL REQUIRED',adopted=False,source=source,run=38044514132,artifact=11671963117,artifact_sha256=manifest['artifact_sha256'],subset_sha256=manifest['subset_sha256'],stages=summaries,settled_native_passes=settled,native_log_sha256=sha(log),zones=manifest['zones'],later_zone_coverage=manifest['later_zone_coverage'],warning_evidence='INCOMPLETE',publication_equivalence='NOT RUN',native_fixture_reconstruction='NOT RUN LOCALLY; REQUIRED BY PINNED RESUME VALIDATOR')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='stages'},indent=2))
