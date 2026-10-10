"""Revalidate saved native evidence; does not run a new native oracle or adopt."""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.complete_native_warnings import complete_reports
from scripts.pcbgen.route_jack_grid import promotion_gate
from scripts.pcbgen.route_shards import delta,reviewed_cut_scope
from scripts.pcbgen.audit_added_mask import added_copper_scope,reviewed_copper_removals
p=argparse.ArgumentParser();p.add_argument('--jr-root',type=Path,required=True);p.add_argument('--cut-archive',type=Path,required=True);p.add_argument('--cut-plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest();bid='osc-jack-right';root=a.jr_root
read=lambda p:json.loads(p.read_text());before=root/'start'/f'{bid}.kicad_pcb';after=root/'fresh'/f'{bid}.kicad_pcb';bd=read(before.with_name('drc.json'));ad=read(after.with_name('drc.json'));audit=root/'native-audits';receipt=read(root/'receipt.json')
assert sha(before.read_bytes())=='7bb70ac47e12c8bb2e2362d78f7602bdf99c2a69214c68aebeef273b0ce11965';assert sha(after.read_bytes())=='e06b7471ddc8f5c8c498c5eb5bf8655cc6de539e92826a5701cf1de06356e136'
full_b,full_a,proof=complete_reports(before,after,bd,ad,audit/'holes-before',audit/'holes-after',audit/'silk',audit/'zones');assert proof==receipt['complete_native_warning_evidence']==read(audit/'proof.json');gate=promotion_gate(read(before.with_name('dump.json')),read(after.with_name('dump.json')),full_b,full_a);assert gate['adopted'];assert all(receipt[k]==json.loads(json.dumps(v)) for k,v in gate.items())
with a.cut_archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='e807c6ad8e9ed9e2d1813a2b8c0a23d74eb8940ea49dc9a23d8fcc1e8879d963'
with zipfile.ZipFile(a.cut_archive) as z:
 def data(suffix):
  ns=[n for n in z.namelist() if n.endswith(suffix)];assert len(ns)==1;return z.read(ns[0])
 def readz(suffix):return json.loads(data(suffix))
 bid='osc-jack-left';base=bid+'-grid-189-local-base/';candidate=bid+'-grid-189-jl118-r8107-via-branch/';old=data(base+bid+'.kicad_pcb').decode();new=data(candidate+bid+'.kicad_pcb').decode();plan=read(a.cut_plan);cuts=reviewed_cut_scope(plan,bid,sha(old.encode()),readz(base+'dump.json'),delta(old,new)['removed'])
 try:added_copper_scope(old,new)
 except ValueError as e:assert 'additive' in str(e)
 else:raise AssertionError('Default additive-only gate accepted cuts')
 scope=added_copper_scope(old,new,4,1,reviewed_removed_uuids=cuts);cut_scope=reviewed_copper_removals(old,new,cuts);assert len(cut_scope)==3 and list(cut_scope.values()).count('via')==1
 rejected=promotion_gate(readz(base+'dump.json'),readz(candidate+'dump.json'),readz(base+'drc.json'),readz(candidate+'drc.json'));assert not rejected['adopted'];assert rejected['split_pad_groups'] and len(rejected['new_warning_identities'])==2
result={'status':'SAVED NATIVE EVIDENCE REPLAY; NO NEW NATIVE EXECUTION OR ADOPTION','jr130_complete_proof_exactly_unchanged':True,'jr130_complete_gate':gate,'jr130_complete_findings':[len(full_b['violations']),len(full_a['violations'])],'r8107_default_additive_gate_rejects':True,'r8107_exact_reviewed_cut_scope':cut_scope,'r8107_added_scope':scope,'r8107_original_promotion_gate':rejected,'new_cut_complete_native_fixture_run':'NOT RUN','implementation_sha256':{str(p):sha(p.read_bytes()) for p in Path('scripts/pcbgen').glob('*.py') if p.name in ('audit_added_mask.py','audit_zone_silk_scope.py','complete_native_warnings.py','zone_batch_evidence.py','route_shards.py')}};a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
