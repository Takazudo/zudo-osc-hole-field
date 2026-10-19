from pathlib import Path
import base64,sys
P=Path(__file__).resolve().parent
V=P.parents[4]/'project/osc-hole-field/workbench/vendor'
boot='''<script type="module">
const decode=s=>new TextDecoder().decode(Uint8Array.from(atob(s),c=>c.charCodeAt(0)));
const blob=s=>URL.createObjectURL(new Blob([s],{type:'text/javascript'}));
const core=blob(decode('__CORE__'));
const three=blob(decode('__MOD__').replaceAll('./three.core.js',core));
const orbit=blob(decode('__ORB__').replaceAll("'three'",JSON.stringify(three)));
const app=blob(decode('__APP__').replaceAll('__THREE__',three).replaceAll('__ORBIT__',orbit));
try{await import(app);}catch(e){document.getElementById('inspect').textContent='Render unavailable: '+e.message;console.error(e);}
</script>'''
for k,p in [('__CORE__',V/'three.core.js'),('__MOD__',V/'three.module.js'),('__ORB__',V/'OrbitControls.js'),('__APP__',P/'viewer.js')]:boot=boot.replace(k,base64.b64encode(p.read_bytes()).decode())
body=(P/'shell.html').read_text().replace('__DATA__',(P/'view-data.json').read_text()).replace('__BOOT__',boot)
if '--check' in sys.argv:
 if (P/'osc-structure-review.html').read_text()!=body:raise SystemExit('FAIL stale HTML')
 print('PASS deterministic standalone HTML')
else:(P/'osc-structure-review.html').write_text(body)
print('Built standalone HTML', (P/'osc-structure-review.html').stat().st_size)
