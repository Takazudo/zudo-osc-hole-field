"""Deterministic offline browser bundle. Never modifies native or manufacturing data."""
from pathlib import Path
import base64,hashlib,json,sys
P=Path(__file__).resolve().parent
R=P.parents[3]
sys.path.insert(0,str(R))
from scripts.panel.audit_current import circuit_bindings
V=P.parent/'vendor'
paths={'lock':'design/grid/placements.lock.json','params':'design/panel/panel-params.json','selector':'design/mechanical/selector-assembly.json'}
data={k:json.loads((R/v).read_text()) for k,v in paths.items()}
data['electrical']=circuit_bindings()
data['artwork']=(R/'design/panel/current-audit/current-panel.svg').read_text()
if set(data['electrical'])!={q['uid'] for q in data['lock']['placements']}:
    raise ValueError('Electrical UID binding differs from fixed geometry')
receipt=json.loads((P/'models/receipt.json').read_text())
for name,digest in receipt['sha256'].items():
    if hashlib.sha256((P/'models'/name).read_bytes()).hexdigest()!=digest:raise ValueError('Model receipt mismatch: '+name)
data['meshes']=json.loads((P/'models/meshes.json').read_text())
for name,m in data['meshes'].items():
    if hashlib.sha256((P/'models'/f'{name}.step').read_bytes()).hexdigest()!=m['sourceSHA256']:
        raise ValueError('STEP/mesh binding differs')
data['sourceHashes']={k:hashlib.sha256((R/v).read_bytes()).hexdigest() for k,v in paths.items()}
boot='''<script type="module">
const decode=s=>new TextDecoder().decode(Uint8Array.from(atob(s),c=>c.charCodeAt(0)));
const blob=s=>URL.createObjectURL(new Blob([s],{type:'text/javascript'}));
const core=blob(decode('__CORE__'));
const three=blob(decode('__MOD__').replaceAll('./three.core.js',core));
const orbit=blob(decode('__ORB__').replaceAll("'three'",JSON.stringify(three)));
const app=blob(decode('__APP__').replaceAll('__THREE__',three).replaceAll('__ORBIT__',orbit));
try{await import(app);}catch(e){document.getElementById('inspect').textContent='Render unavailable: '+e.message;console.error(e);}
</script>'''
for key,path in [('__CORE__',V/'three.core.js'),('__MOD__',V/'three.module.js'),('__ORB__',V/'OrbitControls.js'),('__APP__',P/'viewer.js')]:
    boot=boot.replace(key,base64.b64encode(path.read_bytes()).decode())
html=(P/'shell.html').read_text().replace('__DATA__',json.dumps(data,separators=(',',':')).replace('<','\\u003c')).replace('__BOOT__',boot)
out=P/'index.html'
if '--check' in sys.argv:
    if out.read_text()!=html:raise SystemExit('FAIL stale component preview')
    print('PASS deterministic component preview')
else:out.write_text(html)
print(len(html),'bytes; 438 locked features; source-only preview')
