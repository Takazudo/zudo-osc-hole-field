"""Controlled before/after framebuffer probe; run through heavy guard."""
import argparse,base64,json,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--before',action='store_true');parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args();before=args.before
args.output_dir.mkdir(parents=True,exist_ok=True)
def source(name):
 if before:return subprocess.check_output(['git','show','b81d0a19f18168a4da9578ef2d155b809ec40cd4:project/osc-hole-field/workbench/component-preview/'+name],cwd=root,text=True)
 return (root/name).read_text()
js=source('viewer.js');html=source('index.html')
probe='''\nwindow.__probe={sample(dx){camera.position.set(330+dx,250,390);controls.target.set(0,0,0);controls.update();renderer.render(scene,camera);const gl=renderer.getContext();return {depth:gl.getParameter(gl.DEPTH_BITS),colors:[-50,-25,0,25,50,75].map(x=>{const v=new THREE.Vector3(x,138,0).project(camera);const a=new Uint8Array(4);gl.readPixels(Math.floor((v.x+1)*.5*renderer.domElement.width),Math.floor((v.y+1)*.5*renderer.domElement.height),1,1,gl.RGBA,gl.UNSIGNED_BYTE,a);return [...a];})};}};'''
html=html.replace(base64.b64encode(js.encode()).decode(),base64.b64encode((js+probe).encode()).decode())
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1440,'height':1000});page.set_content(html);page.wait_for_function('window.__probe && ComponentPreview.state().frames>=2');page.wait_for_timeout(1000)
 values=[page.evaluate('(d)=>__probe.sample(d)',dx) for dx in [-1,-.5,0,.5,1]]
 name='before' if before else 'after';(args.output_dir/(name+'.json')).write_text(json.dumps(values,indent=2)+'\n');print(json.dumps(values));page.screenshot(path=str(args.output_dir/(name+'.png')));b.close()
