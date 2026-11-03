import json,sys,hashlib,subprocess,time
from pathlib import Path
repo=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-verifier')
run=Path('/home/takazudo/osc-stage18-native-001')
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage19_protocol as p
proposal=p.load(run/'proposal.json'); req=p.load(run/'request.json')
assert p.digest(run/'request.json')=='a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1'
assert (run/'request.json').read_bytes()==(repo.parent/'osc-stage19-preflight/native-request.json').read_bytes()
assert p.load(run/'input-binding.json')==req['input_files_sha256']
for name,sha in req['runtime_sha256'].items(): assert p.digest(run/name)==sha==p.digest(repo/'scripts/architecture278/implementation'/name)
assert p.load(run/'docker-argv.json')==p.docker_argv(repo,run,proposal['nonce'])
p.approval(p.load(run/'owner-approval.json'),proposal,time.time())
actual=json.loads(subprocess.check_output(['docker','inspect',p.RUN]))
saved=p.load(run/'docker-inspect.json')
p.inspect_container(actual,repo,run);p.inspect_container(saved,repo,run)
assert p.owned_container(actual,proposal)==p.owned_container(saved,proposal)
cap=p.load(run/'capability.json')
fresh=json.loads(subprocess.check_output(['docker','exec',actual[0]['Id'],'cat','/output/capability.json']))
assert cap==fresh
p.capability(cap,proposal)
print(json.dumps({'proposal':proposal,'owner':p.load(run/'owner-approval.json'),'capability':cap,'docker_inspection':saved,'hashes':{name:p.digest(run/name) for name in sorted(p.REVIEWED-{'live-review.json'})},'currently_running':actual[0]['State'],'time':time.time()},indent=2))
