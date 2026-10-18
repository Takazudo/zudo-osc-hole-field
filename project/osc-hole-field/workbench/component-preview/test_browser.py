"""Offline WebGL rendering and immutable geometry checks; no hardware qualification."""
import json,os,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parent
R=P.parents[3]
class PreviewTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start()
  cls.browser=cls.pw.chromium.launch(executable_path=os.environ.get('CHROME_BIN','/usr/bin/chromium'),args=['--no-sandbox','--enable-unsafe-swiftshader'])
  cls.page=cls.browser.new_page(viewport={'width':1440,'height':1000})
  cls.errors=[];cls.requests=[]
  cls.page.on('pageerror',lambda e:cls.errors.append(str(e)))
  cls.page.on('request',lambda r:cls.requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
  cls.page.set_content((P/'index.html').read_text(),wait_until='load')
  cls.page.wait_for_function('window.ComponentPreview && ComponentPreview.state().frames>=2',timeout=60000)
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def test_01_geometry_identity_render(self):
  expected=json.loads((R/'design/grid/placements.lock.json').read_text())['placements']
  actual=self.page.evaluate('ComponentPreview.features()')
  self.assertEqual(len(actual),438)
  for a,e in zip(actual,expected):
   self.assertEqual((a['uid'],a['x'],a['y'],a['kind']),(e['uid'],e['x_mm'],e['y_mm'],e['kind']))
   self.assertEqual((a['worldX'],a['worldY']),(e['x_mm']-159,149-e['y_mm']))
  from collections import Counter
  self.assertEqual(Counter(a['mpn'] for a in actual if a['kind']=='pot'),{'PTV09A-4020F-B103':51,'PTV09A-4020F-B104':48,'PTV09A-4020F-B504':2})
  self.assertGreater(self.page.evaluate('ComponentPreview.state().triangles'),100000)
  self.assertEqual(self.page.evaluate('ComponentPreview.state().caps'),0)
  self.assertFalse(self.errors);self.assertFalse(self.requests)
 def test_02_canvas_selection_respects_opaque_panel(self):
  import math
  self.page.locator('#front').click()
  bounds=self.page.locator('canvas').bounding_box()
  scale=bounds['height']/(2*540*math.tan(math.radians(20)))
  def click(x,y,z=0):
   f=540/(540-z)
   self.page.mouse.click(bounds['x']+bounds['width']/2+(x-159)*scale*f,bounds['y']+bounds['height']/2+(y-149)*scale*f)
  pots=[q for q in self.page.evaluate('ComponentPreview.features()') if q['kind']=='pot']
  first,second=pots[:2]
  click(first['x'],first['y'],10)
  self.assertIn(first['uid'],self.page.locator('#inspect').inner_text())
  before=self.page.locator('#inspect').inner_text()
  click(second['x']+4.5,second['y'])
  self.assertEqual(self.page.locator('#inspect').inner_text(),before)
  self.page.locator('#panel').uncheck()
  click(second['x']+4.5,second['y'])
  self.assertIn(second['uid'],self.page.locator('#inspect').inner_text())
  self.page.locator('#panel').check()
 def test_03_controls_and_screenshots(self):
  before=self.page.evaluate('ComponentPreview.features()')
  for name in ['front','back','orbit','pot-detail']:
   self.page.locator('#'+name).click();self.page.wait_for_timeout(800)
   self.page.screenshot(path=str(P/(name+'.png')))
  self.assertIn('PTV09A',self.page.locator('#inspect').inner_text())
  for d in ['8','10','12','0']:
   self.page.locator('#caps').select_option(d)
   self.assertEqual(self.page.evaluate('ComponentPreview.state().caps'),0 if d=='0' else 101)
  for field in ['panel','components']:
   self.page.locator('#'+field).uncheck();self.assertFalse(self.page.evaluate('ComponentPreview.state().'+field));self.page.locator('#'+field).check()
  self.page.locator('#pots').uncheck();self.assertEqual(self.page.evaluate('ComponentPreview.state().visible'),337);self.page.locator('#pots').check()
  self.assertEqual(before,self.page.evaluate('ComponentPreview.features()'));self.assertFalse(self.errors)
if __name__=='__main__':unittest.main()
