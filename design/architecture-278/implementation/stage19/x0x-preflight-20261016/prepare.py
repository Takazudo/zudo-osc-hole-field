import sys,json,subprocess,hashlib,shutil,os,time
from pathlib import Path
base=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3'); out=base/'osc-stage19-preflight'; repo=base/'osc-stage19-verifier'
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage19_protocol as p
import stage19_request as q
req=p.load(out/'native-request.json')
assert p.digest(out/'native-request.json')=='a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1'
assert req==q.request('a57e02f6bfd770e55ebf448bc067e79fc6b08eb5')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==req['verification_commit']
actual={}
for stage in ('stage17','stage18'):
 actual.update({stage+'/generated/'+k:v for k,v in p.inventory(repo/'design/architecture-278/implementation'/stage/'generated').items()})
assert actual==req['input_files_sha256']
(out/'binding-check.json').write_bytes(p.json_bytes({'status':'PASS','source_commit':req['source_commit'],'verification_commit':req['verification_commit'],'request_sha256':p.digest(out/'native-request.json'),'inputs':len(actual),'verification_files':len(req['verification_files_sha256']),'runtime_files':len(req['runtime_sha256']),'native_executed':False}))
def call(args):
 r=subprocess.run(args,capture_output=True,text=True,timeout=30)
 return {'argv':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
info=json.loads(subprocess.check_output(['docker','info','--format','{{json .}}']))
image=json.loads(subprocess.check_output(['docker','image','inspect',p.IMAGE]))[0]
host={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':os.uname().nodename,'kernel':os.uname().release,'disk':{r:shutil.disk_usage(r)._asdict() for r in ('/','/mnt/c','/var/lib/docker')},'memory':Path('/proc/meminfo').read_text().splitlines()[:4],'docker':{k:info[k] for k in ('ServerVersion','Driver','CgroupDriver','CgroupVersion','MemoryLimit','SwapLimit','CpuCfsQuota','PidsLimit','ContainersRunning','DockerRootDir')},'image':{k:image[k] for k in ('Id','RepoDigests','Architecture','Os')},'guard_sha256':p.digest('/home/takazudo/.codex/scripts/heavy-guard.sh'),'guard_status':call(['bash','/home/takazudo/.codex/scripts/heavy-guard.sh','status']),'run_path':'/home/takazudo/osc-stage18-native-001','run_path_absent':not Path('/home/takazudo/osc-stage18-native-001').exists(),'run_parent_mode':oct(Path('/home/takazudo').stat().st_mode & 0o777),'container_name_check':call(['docker','ps','-a','--filter','name=^/'+p.RUN+'$','--format','{{.ID}}']),'native_executed':False,'live_enforcement':'NOT YET PROVEN; no new container launched; must inspect actual nonce-bound proofs after fresh owner approval'}
(out/'linux-host.json').write_bytes(p.json_bytes(host))
argv=p.docker_argv(repo,Path(host['run_path']))
(out/'docker-argv-proposal.json').write_bytes(p.json_bytes(argv))
print(json.dumps({'binding':'PASS','disk_free_bytes':host['disk']['/']['free'],'memory':host['memory'],'guard':host['guard_status'],'run_absent':host['run_path_absent']}))
