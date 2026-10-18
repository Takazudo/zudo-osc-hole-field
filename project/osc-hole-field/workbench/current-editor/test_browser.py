"""Real Chromium checks for the offline appearance editor; no physical/native claims."""
import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
NS = {'s': 'http://www.w3.org/2000/svg'}

class EditorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=os.environ.get('CHROME_BIN', '/usr/bin/chromium'), args=['--no-sandbox'])
        cls.context = cls.browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        cls.page = cls.context.new_page()
        cls.errors, cls.requests = [], []
        cls.page.on('pageerror', lambda e: cls.errors.append(str(e)))
        cls.page.on('request', lambda r: cls.requests.append(r.url) if not r.url.startswith('blob:') else None)
        # No server or file permission needed: exercise the entire self-contained document offline.
        cls.page.set_content((HERE/'index.html').read_text(), wait_until='load')
        cls.page.wait_for_function('window.PanelAppearance !== undefined')
        cls.lock = json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']
        cls.params = json.loads((ROOT/'design/panel/panel-params.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page.locator('#reset').click()

    def geometry(self):
        return self.page.evaluate('PanelAppearance.geometry()')

    def settings(self):
        return self.page.evaluate('PanelAppearance.settings()')

    def download(self, button):
        with self.page.expect_download() as got:
            self.page.locator(button).click()
        return Path(got.value.path()).read_bytes()

    def test_01_baseline_exact_lock_and_desktop(self):
        expected = [{'data-uid': q['uid'], 'data-kind': q['kind'], 'cx': str(float(q['x_mm'])), 'cy': str(float(q['y_mm'])), 'r': str((self.params['indicator_window']['diameter_mm'] if q['kind']=='led' else q['hole_d_mm'])/2)} for q in self.lock]
        actual = self.geometry()
        self.assertEqual(len(actual), 438)
        for a,e in zip(actual,expected):
            for k in ['data-uid','data-kind']: self.assertEqual(a[k],e[k])
            for k in ['cx','cy','r']: self.assertEqual(float(a[k]),float(e[k]))
        self.assertEqual(sum(q['kind']=='octave' and q['hole_d_mm']==7 for q in self.lock),5)
        s=self.settings()['appearance']
        self.assertEqual((s['labelSwitch'],s['separatorGap']),(1,2.5))
        box=self.page.locator('#panel').bounding_box();vp=self.page.locator('#viewport').bounding_box()
        self.assertGreaterEqual(box['x'],vp['x']);self.assertLessEqual(box['x']+box['width'],vp['x']+vp['width']+1)
        self.assertLessEqual(box['height'],vp['height'])
        self.assertFalse(self.errors);self.assertFalse(self.requests)
        self.page.screenshot(path=str(HERE/'editor-full.png'))

    def test_02_every_appearance_control_and_import_preserves_geometry(self):
        before=self.geometry()
        item_circles=self.page.evaluate("Array.from(document.querySelectorAll('#panel .item circle')).map(e=>['cx','cy','r'].map(k=>e.getAttribute(k)))")
        cfg=self.settings();a=cfg['appearance']
        a.update(labelModule=2.6,labelKnob=.8,labelJack=2.2,labelSwitch=1.6,separatorGap=5,lineWeight=2,font='Georgia',whiteVisible=False,goldVisible=False,whiteColor='#aaccee',goldColor='#ffcc77',relations=False,ledStyle='bracket',icons={'OSC':3},offsets={'label-0000':{'x':4,'y':-4}})
        self.page.evaluate('(v)=>PanelAppearance.load(v)',cfg)
        self.assertEqual(before,self.geometry())
        self.assertEqual(item_circles,self.page.evaluate("Array.from(document.querySelectorAll('#panel .item circle')).map(e=>['cx','cy','r'].map(k=>e.getAttribute(k)))"))
        self.assertEqual(self.settings(),cfg)
        svg=ET.fromstring(self.page.evaluate('PanelAppearance.svg()'))
        self.assertEqual(svg.attrib['viewBox'],'0 0 318 298')
        self.assertEqual(svg.find('.//s:g[@id="locked-features"]',NS).attrib,{'id':'locked-features'})
        self.page.locator('#reset').click()
        self.assertEqual(self.geometry(),before)
        self.assertEqual(self.settings()['appearance'],self.page.evaluate('PanelAppearance.baseline()'))

    def test_03_reject_geometry_and_malformed_presets_atomically(self):
        before=self.settings();geometry=self.geometry()
        cases=[]
        for k,v in [('px',20),('py',17),('placements',[]),('values',{}),('diameters',{}),('labels',{'x':'new text'}),('__proto__',{'px':9})]:
            cfg=json.loads(json.dumps(before));cfg['appearance'][k]=v;cases.append(cfg)
        for key,value in [('schema','zudo-grid-review-v1'),('geometrySHA256','wrong')]:
            cfg=json.loads(json.dumps(before));cfg[key]=value;cases.append(cfg)
        for field,value in [('icons',{'OSC':999}),('icons',{'fake':1}),('offsets',{'label-9999':{'x':0,'y':0}}),('offsets',{'label-0000':{'x':0,'y':0,'r':8}}),('hardwareVisible','yes'),('exportMode','silk'),('labelJack',None),('labelJack','2'),('lineWeight',100),('goldColor','url(https://invalid.example)')]:
            cfg=json.loads(json.dumps(before));cfg['appearance'][field]=value;cases.append(cfg)
        for cfg in cases:
            rejected=self.page.evaluate('(text)=>{try{PanelAppearance.load(JSON.parse(text));return false}catch(e){return true}}',json.dumps(cfg))
            self.assertTrue(rejected,cfg)
            self.assertEqual(before,self.settings());self.assertEqual(geometry,self.geometry())
        bad=json.dumps(cases[0]).encode()
        self.page.locator('#loadfile').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':bad})
        self.assertIn('Settings rejected',self.page.locator('#status').inner_text())
        self.assertEqual(before,self.settings())

    def test_04_ui_save_load_roundtrip_and_svg(self):
        geometry=self.geometry()
        self.page.locator('#labelModule').fill('2');self.page.locator('#labelModule').dispatch_event('input')
        self.page.locator('#offset-x').fill('1.5');self.page.locator('#offset-x').dispatch_event('input')
        self.page.locator('#icon-choice').select_option('2')
        self.page.locator('#gold-color').fill('#d0ae66');self.page.locator('#gold-color').dispatch_event('input')
        saved=self.download('#save');cfg=json.loads(saved)
        self.page.locator('#reset').click()
        self.page.locator('#loadfile').set_input_files({'name':'settings.json','mimeType':'application/json','buffer':saved})
        self.page.wait_for_function('document.querySelector("#status").textContent.includes("settings loaded")')
        self.assertEqual(self.settings(),cfg);self.assertEqual(self.geometry(),geometry)
        svg=self.download('#svg-export').decode()
        self.assertEqual(svg,self.page.evaluate('PanelAppearance.svg()'))
        root=ET.fromstring(svg)
        meta=json.loads(root.find('s:metadata',NS).text)
        self.assertEqual(meta['appearance'],cfg['appearance']);self.assertTrue(meta['previewOnly'])
        self.assertEqual(len(root.findall('.//s:g[@id="locked-features"]/s:circle',NS)),438)
        self.assertNotIn('chosen',svg)
        self.assertEqual(self.download('#svg-export').decode(),svg)

    def test_05_pan_zoom_detail_and_png_consistency(self):
        geometry=self.geometry()
        self.page.locator('#label-select').select_option('label-0200')
        self.page.locator('#detail').click()
        self.assertEqual(self.page.locator('#zoom-value').inner_text(),'300%')
        self.page.locator('aside').evaluate('(e)=>e.scrollTop=e.scrollHeight');self.page.screenshot(path=str(HERE/'editor-detail.png'))
        self.page.locator('#viewport').focus();before=self.page.locator('#panel').get_attribute('style')
        self.page.keyboard.press('ArrowRight');self.assertNotEqual(before,self.page.locator('#panel').get_attribute('style'))
        self.page.locator('#zoom-in').click();self.page.locator('#fit').click()
        self.assertEqual(self.geometry(),geometry)
        self.assertEqual(self.page.locator('#zoom-value').inner_text(),'100%')
        png=self.download('#png-export')
        self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(int.from_bytes(png[16:20],'big'),1590)
        self.assertEqual(int.from_bytes(png[20:24],'big'),1490)
        # Independent rasterization of the exported SVG, same browser and explicit dimensions.
        other=self.page.evaluate('''async()=>{await document.fonts.ready;const d=new DOMParser().parseFromString(PanelAppearance.svg(),'image/svg+xml');const s=d.documentElement;s.setAttribute('width','1590');s.setAttribute('height','1490');const u=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(s)],{type:'image/svg+xml'}));const i=new Image();await new Promise((r,j)=>{i.onload=r;i.onerror=j;i.src=u});const c=document.createElement('canvas');c.width=1590;c.height=1490;c.getContext('2d').drawImage(i,0,0);URL.revokeObjectURL(u);return c.toDataURL('image/png').split(',')[1]}''')
        self.assertEqual(hashlib.sha256(png).digest(),hashlib.sha256(base64.b64decode(other)).digest())
        self.assertFalse(self.errors);self.assertFalse(self.requests)

    def test_06_hardware_types_toggles_presets_and_export_separation(self):
        before=self.geometry()
        legacy=self.settings()
        for k in list(legacy['appearance']):
            if k.startswith('hardware') or k=='exportMode':del legacy['appearance'][k]
        self.page.evaluate('(v)=>PanelAppearance.load(v)',legacy)
        self.assertTrue(self.settings()['appearance']['hardwareVisible'])
        self.assertEqual(self.settings()['appearance']['exportMode'],'artwork')
        self.assertEqual(before,self.geometry())
        expected={'jack':180,'knob':101,'toggle':30,'rotary':5,'button':8,'led':114}
        for kind,count in expected.items():
            self.assertEqual(self.page.locator(f'#panel [data-hardware-type="{kind}"]').count(),count)
        items=self.page.locator('#panel [data-hardware-uid]').evaluate_all("es=>es.map(e=>[e.dataset.hardwareUid,e.getAttribute('transform')])")
        self.assertEqual(dict(items),{q['uid']:f"translate({q['x_mm']:g} {q['y_mm']:g})" for q in self.lock})
        self.assertNotIn('id="hardware-preview"',self.download('#svg-export').decode())
        for control,kinds in [('Jacks',['jack']),('Knobs',['knob']),('Switches',['toggle','rotary','button']),('LEDs',['led'])]:
            self.page.locator('#hardware'+control).uncheck()
            for kind in kinds:self.assertEqual(self.page.locator(f'#panel [data-hardware-type="{kind}"]').count(),0)
            self.page.locator('#hardware'+control).check()
        self.page.locator('#hardwareVisible').uncheck()
        self.assertEqual(self.page.locator('#panel [data-hardware-uid]').count(),0)
        self.assertEqual(before,self.geometry())
        self.page.locator('#hardwareVisible').check()
        self.page.locator('#export-mode').select_option('assembled')
        self.page.locator('#hardwareJacks').uncheck()
        saved=self.download('#save');self.page.locator('#reset').click()
        self.page.locator('#loadfile').set_input_files({'name':'hardware.json','mimeType':'application/json','buffer':saved})
        self.page.wait_for_function('!PanelAppearance.settings().appearance.hardwareJacks')
        self.assertEqual(self.settings(),json.loads(saved))
        svg=ET.fromstring(self.download('#svg-export'))
        hardware=svg.find('.//s:g[@id="hardware-preview"]',NS)
        self.assertEqual(len(hardware),258)
        self.assertEqual(json.loads(svg.find('s:metadata',NS).text)['exportMode'],'assembled')
        assembled=self.download('#png-export')
        self.page.locator('#export-mode').select_option('artwork')
        self.assertNotEqual(assembled,self.download('#png-export'))
        # Deliberately place a label over a knob: visual warning must detect it.
        self.page.locator('#hardwareJacks').check()
        # Re-render with real appearance offsets; choose a knob label and shift toward its centre.
        label=self.page.locator('#panel [data-label-kind="knob"]').first.get_attribute('data-editor-label')
        self.page.locator('#label-select').select_option(label)
        self.page.locator('#offset-y').fill('-4');self.page.locator('#offset-y').dispatch_event('input')
        self.assertGreater(int(self.page.locator('#occlusion').inner_text().split()[0]),0)
        self.assertEqual(before,self.geometry())
        self.assertFalse(self.errors);self.assertFalse(self.requests)

if __name__=='__main__':
    unittest.main(verbosity=2)
