#!/usr/bin/env bash
set -euo pipefail
cd /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4
# OPERATOR ACTION: separately approve two exact requests, then run them serially.
python3 - <<'PREFLIGHT'
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'scripts/kicad')
import local_native_admission as a
p=Path('.circuit-cache/e16-local-packet-093f14b-3f8e1f74/remaining-boards-batch.json')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='0b473ff4dcbbdc698e075e71e0fd34c05b5b0b1c42c10a7120c84691f9d03c33'
m=json.loads(p.read_text())
assert a.clean_head(Path.cwd())==m['source_sha']
for x in m['requests']:
 r=a.validate_request(Path.cwd(),Path.cwd()/x['request'])
 assert a.sha(x['request'])==x['sha256']
 assert not Path(x['approval']).exists(), 'Existing approval: do not rerun this batch'
 assert not Path(x['guard_evidence']).exists(), 'Existing evidence: do not rerun this batch'
 assert not (a.persistent_claim_directory()/(x['worker']+'.json')).exists(), 'Consumed request: do not rerun'
PREFLIGHT
printf 'Board 1/2: KB-t2; exact operator approval and guarded execution.
'
python3 scripts/kicad/local_native_admission.py approve --request .circuit-cache/e16-native-local-093f14b-3f8e1f74/KB-t2/local-request.json --request-sha256 dd35ff69ebe4c1f7a59a13013dc9ac84d1ef09398f39e8ecfefc8a71ab21a29d --output .circuit-cache/e16-native-local-093f14b-3f8e1f74/KB-t2/operator-approval.json --operator takazudo --reservation-reference 'Operator invocation of the remaining-boards batch reserves one global native slot serially for KB-t2 and KB-p1 and excludes all other native work.' --qualification-reference '/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/harmless-controls/qualification.json sha256=64b46e301dcae8506b52d14653ca966594374ca0f0c3b4970cb3bc403f64bc4c; /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/startup-success-guard.json.qualification.json sha256=c0a993b68a3fbea87d071a1856c98f4f4fbe7df55e75c9e39a17ec940528bbfa; /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/startup-failure-guard.json.qualification.json sha256=019215d6785ddfcb68bf8e088a830d2c0d83b3dfa44c15dc97e0caaf4270cd2e; /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/oracle-guard.json sha256=7ebdaccf4122f3d53fea29d89717c4aadf790b2fa74c5ea63f8516f45400d626'
python3 design/partition/core-split/candidates/planning/joined-feed-construction-v2/native_validation.py execute --stage .circuit-cache/e16-native-local-093f14b-3f8e1f74 --target KB-t2 </dev/tty
printf 'Board 2/2: KB-p1; exact operator approval and guarded execution.
'
python3 scripts/kicad/local_native_admission.py approve --request .circuit-cache/e16-native-local-093f14b-3f8e1f74/KB-p1/local-request.json --request-sha256 55178e0901189313010316c9e7f8ea3b9fee26a83fb0a6eb6391a778b3b9a977 --output .circuit-cache/e16-native-local-093f14b-3f8e1f74/KB-p1/operator-approval.json --operator takazudo --reservation-reference 'Operator invocation of the remaining-boards batch reserves one global native slot serially for KB-t2 and KB-p1 and excludes all other native work.' --qualification-reference '/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/harmless-controls/qualification.json sha256=64b46e301dcae8506b52d14653ca966594374ca0f0c3b4970cb3bc403f64bc4c; /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/startup-success-guard.json.qualification.json sha256=c0a993b68a3fbea87d071a1856c98f4f4fbe7df55e75c9e39a17ec940528bbfa; /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/startup-failure-guard.json.qualification.json sha256=019215d6785ddfcb68bf8e088a830d2c0d83b3dfa44c15dc97e0caaf4270cd2e; /home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-r4/.circuit-cache/e16-local-packet-093f14b-3f8e1f74/oracle-guard.json sha256=7ebdaccf4122f3d53fea29d89717c4aadf790b2fa74c5ea63f8516f45400d626'
python3 design/partition/core-split/candidates/planning/joined-feed-construction-v2/native_validation.py execute --stage .circuit-cache/e16-native-local-093f14b-3f8e1f74 --target KB-p1 </dev/tty
printf 'Both board commands completed; evidence still requires review and is not electrical acceptance.\n'
