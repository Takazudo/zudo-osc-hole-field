import sys,json,hashlib,time
from pathlib import Path
repo=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-verifier')
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage19_protocol as p, stage19_retention as r
run=Path('/home/takazudo/osc-stage18-native-001')
receipt=p.load(run/'retention.json');proposal=p.load(run/'proposal.json')
raw=dict(receipt);raw['status']='VERIFIED_HASHED_COPY'
result=r.verify(run/'retained',raw,proposal,p.digest(run/'admit.json'),p.digest(run/'capability.json'))
assert result==receipt
consumed=p.load(run/'retained/consumed.json')
p.admission(run,proposal,consumed['consumed_at_unix'])
assert p.load(run/'docker-final.json')[0]['State']['Running'] is False
print(json.dumps({'status':'PASS independent post-retention disk/hash/receipt/admission verification','time':time.time(),'retained_bytes':receipt['bytes'],'retained_files':len(receipt['files']),'xml_sha256':p.digest(run/'retained/netlist.xml'),'native':receipt['native'],'admission_at_consumption':'PASS; exact 13 reviewed files','container_stopped':True},indent=2))
