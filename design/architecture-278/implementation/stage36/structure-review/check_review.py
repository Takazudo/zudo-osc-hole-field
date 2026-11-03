from pathlib import Path
from playwright.sync_api import sync_playwright
import json
P=Path(__file__).resolve().parent
import os
OUT=Path(os.environ.get('OSC_REVIEW_OUTPUT','/tmp/osc-review-render'));OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader','--disable-gpu-sandbox'])
 page=b.new_page(viewport={'width':1500,'height':1050},device_scale_factor=1);errors=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
 page.set_content((P/'osc-structure-review.html').read_text(),wait_until='load');page.wait_for_function('window.REVIEW_READY===true');page.wait_for_timeout(500)
 page.screenshot(path=str(OUT/'current-whole.png'))
 page.locator('[data-camera="front"]').click()
 axes=page.evaluate('[[0,0,0],[318,0,0],[0,298,0]].map(p=>ReviewView.project(p))')
 if not (axes[1][0]>axes[0][0] and axes[2][1]<axes[0][1]):raise RuntimeError('Panel XY mirrored')
 page.locator('[data-camera="a01"]').click();page.wait_for_timeout(300);page.screenshot(path=str(OUT/'current-a01.png'))
 page.locator('#explode').check();page.wait_for_timeout(300);page.screenshot(path=str(OUT/'current-exploded.png'))
 exploded=page.evaluate('ReviewView.state()');assert exploded['exploded'] and 'routes' not in exploded['visible']
 page.locator('#explode').uncheck();page.locator('[data-layer="earlier"]').check();page.wait_for_timeout(300);page.screenshot(path=str(OUT/'earlier-card-context.png'))
 page.locator('[data-layer="earlier"]').uncheck();page.locator('[data-layer="panel"]').uncheck();assert 'panel' not in page.evaluate('ReviewView.state().visible')
 assert not errors,errors
 network=[x for x in requests if x.startswith(('http:','https:'))];assert not network,network
 result={'status':'PASS_RENDER_ONLY','browser':'system Chromium / software WebGL','errors':errors,'external_requests':network,'state':page.evaluate('ReviewView.state()'),'checked':['whole panel render','A01 close-up','exploded hides connected geometry','layer visibility','earlier card context opt-in','offline module embedding','Panel XY x-right/y-down projection'],'source':'02e83bb6955d97958248946bd11d2e3f14014ad3','not_checked':['native CAD','fit/collision','physical','manufacturing','ordering']}
 (OUT/'render-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));b.close()
