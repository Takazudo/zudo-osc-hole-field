from pathlib import Path
import json,os
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parent
O=Path(os.environ.get('REVIEW_OUTPUT_DIR','/tmp/osc-whole-layout-render'));O.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,condition):
 checks.append({'name':name,'pass':bool(condition)})
 if not condition:raise RuntimeError(name)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader','--disable-gpu-sandbox'])
 page=b.new_page(viewport={'width':1640,'height':1080},device_scale_factor=1);errors=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
 page.set_content((P/'osc-structure-review.html').read_text(),wait_until='load');page.wait_for_function('window.REVIEW_READY===true')
 check('complete coverage',page.locator('#coverage tr').count()==33)
 check('fixed438',page.evaluate('ReviewView.state().markers===438'))
 def shot(name):page.screenshot(path=str(O/name))
 shot('whole.png')
 page.locator('#explode').check();shot('exploded.png');check('cover hidden when exploded',page.evaluate('!ReviewView.groups.cover.visible'))
 page.locator('[data-camera="side"]').click();shot('side-stack.png')
 page.locator('#explode').uncheck();page.locator('#panelOnly').click();shot('panel.png')
 check('xy orientation',page.evaluate('ReviewView.project([0,0,0])[0]<ReviewView.project([318,0,0])[0] && ReviewView.project([0,0,0])[1]>ReviewView.project([0,298,0])[1]'))
 page.locator('#reset').click()
 for face in ['front','rear']:
  page.locator('[data-camera="'+face+'"]').click();check(face+' orientation',page.evaluate('(ReviewView.project([0,0,0])[0]<ReviewView.project([318,0,0])[0])')==(face=='rear'))
 for x in ['O1','E6','A01','X2','N1']:
  page.select_option('#focus',x);check('focus '+x,page.evaluate('ReviewView.state().focus')==x)
 page.select_option('#focus','A01');check('A01 overlap markers retained',page.evaluate('ReviewView.state().visibleOverlaps>0'));page.locator('[data-camera="iso"]').click();shot('a01-context.png')
 page.select_option('#focus','all');page.locator('#incumbent').check();check('historical visibility',page.evaluate('ReviewView.state().incumbent'))
 for layer in ['panel','led','control','selector','jack','middle','rear','cover']:
  page.locator('[data-layer="'+layer+'"]').uncheck();check('hide '+layer,page.evaluate('ReviewView.groups.'+layer+'.visible') is False)
 page.locator('#reset').click();page.locator('#incumbent').uncheck()
 with page.expect_download() as download:page.locator('#save').click()
 check('png download',download.value.suggested_filename=='osc-whole-layout.png')
 check('no errors',not errors);external=[u for u in requests if u.startswith(('http:','https:'))];check('offline',not external)
 (O/'render-checks.json').write_text(json.dumps({'status':'PASS_RENDER_ONLY','checks':checks,'errors':errors,'external_requests':external,'browser':'system Chromium / software WebGL'},indent=2)+'\n');b.close()
print('PASS',len(checks),'browser checks')
