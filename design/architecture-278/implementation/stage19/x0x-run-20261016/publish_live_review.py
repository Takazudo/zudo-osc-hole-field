import json,time,os,hashlib
from pathlib import Path
run=Path('/home/takazudo/osc-stage18-native-001')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected={'capability.json':'327dcc69e2685da7627fddd765567f42f48f7303294102f390a809a3d154f868','docker-argv.json':'29afd2c6bde381691bb2859d128fbff0abe851a2926d0e3537bcdc18cafe1ced','docker-inspect.json':'410098dbdde83dbae77d24edcaa7c8baafb6cbe0e9c666ec744fc5745fca5766','input-binding.json':'181a392ac1ac86a64c4366029be0c22eed5ec693d61c3dc226e7d1c9d7926b6d','owner-approval.json':'e8a8143e2720a8f59d2db14837d020dc5d871667ca78d7439c316a67a5bdf1a3','proposal.json':'449fa05d099c5c259431dd69eb4d4eeb0e627a781b36595e062cba2861af7e96','request.json':'a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1','stage17_retain.py':'7d64fd158a0151dbe1337041dd0d2e64b9d254b4134773e6e3c3f5cf713c5211','stage19_container.py':'b32dce4774b790a23d21b9bb5e5fc0fe017a9ce636a202698fb8edee4e831273','stage19_host.py':'f0ec92ab6535e18ee4a594ebdc00e016ce99b2a64f610742f90b24d05c9ab4e3','stage19_protocol.py':'a31f1f22a7049d06b68068e9adaa16d0826fff2ea0bfe4333bf71c6a215f1906','stage19_retention.py':'0d703a3cb8cab9f62c60fb113ebde2b8af1bb990c1cadc082075e9f501df233a'}
for name,sha in expected.items():assert digest(run/name)==sha
proposal=json.loads((run/'proposal.json').read_bytes())
assert proposal['nonce']=='9c288f95f704df39f8dd46ea704688b433dbe6c8bdc714f18979d5376488bd74'
now=time.time()
assert now<1792178302+280
review={k:proposal[k] for k in ('run_id','nonce','source_commit','verification_commit','request_sha256')}
review.update(approved=True,reviewer='Codex session 01a14620-af99-7435-90c6-ebcb3b6900e5, independent Stage19 reviewer on x0x',independent_of_implementation=True,issued_at_unix=now,expires_at_unix=min(now+240,1792178302+295),capability_sha256=expected['capability.json'],docker_inspect_sha256=expected['docker-inspect.json'],authorship_exclusion='This fresh session authored neither bound implementation nor prior preparation; independently read all five runtime files and request/source contracts, reconstructed complete bindings and inspected actual nonce-bound live proofs. Review helpers and this receipt are my own work.',assessment='PASS for one exact version/XML opportunity only. Actual cgroup, identity, mounts, network, timeout, image and 12 pre-review file hashes inspected. Retention and full 118/561/154 logical parity remain separate gates; no electrical acceptance.',reviewed_pre_review_sha256=expected)
payload=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode()
assert len(payload)<1048576 and not (run/'live-review.json').exists()
tmp=run/'live-review.json.pending'
with tmp.open('xb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
os.rename(tmp,run/'live-review.json')
fd=os.open(run,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
print((run/'live-review.json').read_text());print('SHA256',digest(run/'live-review.json'))
