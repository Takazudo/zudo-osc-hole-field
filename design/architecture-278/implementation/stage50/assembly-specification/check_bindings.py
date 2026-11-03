from pathlib import Path
import sys,json,hashlib
root=Path.cwd();sys.path.insert(0,str(root/'scripts/checks'))
import architecture_history as h
for commit,modules in h.CHECKPOINTS.items():h.verify_binding(root,commit,modules)
print('PASS seven historical checkpoint bindings')
for stage in range(41,51):
 for p in (root/f'design/architecture-278/implementation/stage{stage}').rglob('review-bindings.json'):
  data=json.loads(p.read_text())
  for name,sha in data.get("sha256",data).items():
   f=root/name
   if hashlib.sha256(f.read_bytes()).hexdigest()!=sha:raise ValueError(name)
  print('PASS',p.relative_to(root),len(data.get("sha256",data)))
