import sys,json,hashlib,subprocess,os,time
from pathlib import Path
repo=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-verifier')
reqpath=repo.parent/'osc-stage19-preflight/native-request.json'
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage19_request as r, stage19_protocol as p
req=json.loads(reqpath.read_bytes())
assert hashlib.sha256(reqpath.read_bytes()).hexdigest()=='a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1'
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==req['verification_commit']
assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'])
assert req==r.request(req['verification_commit'])
actual={}
for stage in ('stage17','stage18'):
    actual.update({stage+'/generated/'+k:v for k,v in p.inventory(repo/'design/architecture-278/implementation'/stage/'generated').items()})
assert actual==req['input_files_sha256']
assert len(actual)==72 and len(req['verification_files_sha256'])==155
assert not Path('/home/takazudo/osc-stage18-native-001').exists()
assert not subprocess.check_output(['docker','ps','-a','--filter','name=^/osc-stage18-native-001$','--format','{{.ID}}']).strip()
assert p.digest('/home/takazudo/.codex/scripts/heavy-guard.sh')=='074a463dd6b3a65b7e2168df95b200c0192c414862375bcfb95f979c34c67ee7'
assert not any(k.startswith('HEAVY_GUARD_') for k in os.environ)
image=json.loads(subprocess.check_output(['docker','image','inspect',p.IMAGE]))[0]
assert image['Os']=='linux' and image['Architecture']=='amd64'
print(json.dumps({'status':'PASS','time':time.time(),'source':req['source_commit'],'verifier':req['verification_commit'],'input_count':len(actual),'verification_count':len(req['verification_files_sha256']),'runtime_count':len(req['runtime_sha256']),'image_id':image['Id'],'image_user':image['Config']['User'],'disk':subprocess.check_output(['df','-B1','/home/takazudo'],text=True),'memory':next(x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))},indent=2))
