#!/usr/bin/env python3
"""Build a standalone, offline HTML; no external runtime requests or CDNs."""
from pathlib import Path
import json,base64,hashlib
R=Path(__file__).resolve().parents[1]
def text(path): return (R/path).read_text()
def jsjson(obj): return json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
def b64(path):return base64.b64encode((R/path).read_bytes()).decode()
shell=text('src/shell.html')
data='<script>window.GRID_DATA='+jsjson(json.loads(text('layout/grid.json')))+';window.GRID_ICONS='+jsjson(json.loads(text('reference/icons.json')))+';window.GRID_PARTS='+jsjson(json.loads(text('parts/components.json')))+';</script>'
boot="""<script type="module">
const decode=s=>new TextDecoder().decode(Uint8Array.from(atob(s),c=>c.charCodeAt(0)));
const blob=s=>URL.createObjectURL(new Blob([s],{type:'text/javascript'}));
const core=blob(decode('__CORE__'));
const three=blob(decode('__MOD__').replaceAll('./three.core.js',core));
const orbit=blob(decode('%%ORBIT_BYTES%%').replaceAll("'three'",JSON.stringify(three)));
const app=blob(decode('__APP3D__').replaceAll('__THREE__',three).replaceAll('__ORBIT__',orbit));
try{await import(app);}catch(e){document.getElementById('render-message').textContent='3D failed to initialize: '+e.message;console.error(e);}
</script>"""
for key,path in [('__CORE__','vendor/three.core.js'),('__MOD__','vendor/three.module.js'),('%%ORBIT_BYTES%%','vendor/OrbitControls.js'),('__APP3D__','src/three.js')]:boot=boot.replace(key,b64(path))
# Replacement order avoids accidentally processing placeholder-looking source bytes.
for key,v in [('<!--CSS-->',text('src/style.css')),('<!--DATA-->',data),('<!--ENGINE-->',text('src/ar-engine.js')+'\n'+text('src/sh-slew-engine.js')),('<!--RENDER-->',text('src/render.js')),('<!--APP-->',text('src/app.js')),('<!--BOOT-->',boot)]:shell=shell.replace(key,v)
(R/'index.html').write_text(shell)
print('Built',R/'index.html',len(shell.encode()),'bytes')
