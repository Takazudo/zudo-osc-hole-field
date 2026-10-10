"""Read-only eligibility check using exact terminal and full paired native evidence."""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path,PurePosixPath
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.zone_batch_evidence import BEFORE,AFTER,verify_result
from scripts.pcbgen.complete_native_warnings import complete_reports
from scripts.pcbgen.route_jack_grid import promotion_gate
sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser()
for name in ('archive','terminal_root','before','after','zone_destination','output'):p.add_argument(name,type=Path)
p.add_argument('--sha256',required=True)
a=p.parse_args()
manifest=json.loads(Path('circuit/routing/issue189/core-complete-terminal/reconciled.json').read_text())
assert manifest['artifact_sha256']=='b5c112a5c9336a27cb08369ec42a11b7cc51a39bb569215d24075ccd3ab11567'
assert not manifest['adopted'] and manifest['retained_prior_copper']==133169 and manifest['removed_copper']==0
assert sha(a.before.read_bytes())==BEFORE and sha(a.after.read_bytes())==AFTER
for f in manifest['extracted_files']:
 data=(a.terminal_root/f['path']).read_bytes()
 assert len(data)==f['size'] and sha(data)==f['sha256'],f['path']
with a.archive.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==a.sha256
with zipfile.ZipFile(a.archive) as z:
 names=[n for n in z.namelist() if n.endswith('/result.json') and 'paired-zone-batches/' in n]
 assert len(names)==1
 prefix=names[0][:-len('result.json')]
 proof=verify_result(lambda n:z.read(prefix+n),a.before,a.after)
 assert proof['full_paired_zone_coverage'] and not proof['new_zone_silk_identities']
 a.zone_destination.mkdir(parents=True,exist_ok=False)
 for info in z.infolist():
  if not info.filename.startswith(prefix) or info.is_dir():continue
  rel=PurePosixPath(info.filename[len(prefix):])
  assert not rel.is_absolute() and '..' not in rel.parts and (info.external_attr>>16)&0o170000!=0o120000
  dest=a.zone_destination/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(info))
root=a.terminal_root/'.circuit-cache'
read=lambda p:json.loads(p.read_text())
start=root/'osc-core-grid-shards-start';fresh=root/'osc-core-grid-shards-fresh'
audits=root/'osc-core-grid-shards-complete-warnings/native-audits'
before_drc,after_drc,complete=complete_reports(a.before,a.after,read(start/'drc.json'),read(fresh/'drc.json'),audits/'holes-before',audits/'holes-after',audits/'silk',a.zone_destination)
gate=promotion_gate(read(start/'dump.json'),read(fresh/'dump.json'),before_drc,after_drc)
assert gate['adopted'],gate
result=dict(status='EXACT SAVED NATIVE EVIDENCE ELIGIBLE; NOT ADOPTED',adopted=False,
 before_sha256=BEFORE,after_sha256=AFTER,paired_artifact_sha256=a.sha256,
 terminal_artifact_sha256=manifest['artifact_sha256'],complete_warning_proof=complete,
 promotion_gate_with_complete_observations=gate,
 original_before_findings=len(read(start/'drc.json')['violations']),
 original_after_findings=len(read(fresh/'drc.json')['violations']),
 completed_before_findings=len(before_drc['violations']),completed_after_findings=len(after_drc['violations']),
 next_gate='Fresh bounded replay with all native, retention and publication checks; no canonical board changed')
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
