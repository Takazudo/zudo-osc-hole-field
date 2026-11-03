import json,time,hashlib,os
from pathlib import Path
run=Path('/home/takazudo/osc-stage18-native-001')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(run/'live-review.json')=='f52d537949fa27302b4c0fb10cf7ba97371494953aad7ac14539b6c60bd9378a'
review=json.loads((run/'live-review.json').read_bytes())
hashes={**review['reviewed_pre_review_sha256'],'live-review.json':digest(run/'live-review.json')}
assert set(hashes)==set(json.loads((run/'request.json').read_bytes())['admission_reviewed_files']) and len(hashes)==13
for name,sha in hashes.items():assert digest(run/name)==sha
now=time.time();assert now<review['expires_at_unix']
value={k:review[k] for k in ('run_id','nonce','source_commit','verification_commit','request_sha256')}
value.update(approved=True,issued_at_unix=now,expires_at_unix=review['expires_at_unix'],reviewed_sha256=hashes)
payload=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
assert len(payload)<1048576 and not (run/'admit.json').exists()
assert sum(p.stat().st_size for p in run.rglob('*') if p.is_file())+len(payload)<12582912
tmp=run/'admit.json.pending'
with tmp.open('xb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
os.rename(tmp,run/'admit.json')
fd=os.open(run,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
print('Published 13-file admission',digest(run/'admit.json'),'at',now)
