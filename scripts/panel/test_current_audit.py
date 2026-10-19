"""Source-only regressions; deliberately separate from pcbnew checks."""
import copy
import json
from pathlib import Path
import subprocess
import unittest
import xml.etree.ElementTree as ET
from scripts.panel import audit_current as audit

class CurrentPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit.build()
        cls.lock = audit.read('design/grid/placements.lock.json')
        cls.table = audit.read('boards/panel/reports/feature-table.json')
        cls.params = audit.read('design/panel/panel-params.json')

    def test_complete_binding_and_electrical_overrides(self):
        self.assertEqual(self.result['counts']['features'], 438)
        self.assertEqual(self.result['counts']['blocks'], 33)
        self.assertEqual(self.result['counts']['led_types'], {'mag':92,'clip':10,'stage':12})
        self.assertEqual(self.result['counts']['pot_mpn'], {'PTV09A-4020F-B103':51, 'PTV09A-4020F-B104':48, 'PTV09A-4020F-B504':2})
        overrides = self.result['electrical_overrides']
        self.assertEqual(len(overrides),48)
        self.assertTrue(all(r['role']=='dc_control_source:RV' and r['current_mpn']=='PTV09A-4020F-B104' for r in overrides))
        self.assertEqual(sum(b['inputs'] for b in self.result['blocks']),98)
        self.assertEqual(sum(b['outputs'] for b in self.result['blocks']),82)

    def test_retained_feature_drift_is_rejected(self):
        for key, value in [('x_mm', 0),('y_mm',0),('diameter_mm',7.1),('kind','jack'),('ref','wrong')]:
            with self.subTest(key=key):
                table=copy.deepcopy(self.table);table['rows'][0][key]=value
                with self.assertRaises(ValueError):audit.compare_features(self.lock,table,self.params)
        for action in ('missing','duplicate'):
            table=copy.deepcopy(self.table)
            if action=='missing':table['rows'].pop()
            else:table['rows'].append(table['rows'][0])
            with self.assertRaises(ValueError):audit.compare_features(self.lock,table,self.params)

    def test_perimeter_claim_uses_lock_not_grid_margin(self):
        p=self.result['perimeter_trial']
        self.assertEqual(p['outer_jack_x_mm'],[14.5,303.5])
        self.assertAlmostEqual(p['nearest_panel_edge_mm'],10.35)
        self.assertAlmostEqual(p['clearance_beyond_3mm_border_mm'],7.35)

    def test_current_document_claims_and_matrix(self):
        trial=self.result['perimeter_trial'];left,right=trial['outer_jack_x_mm']
        doc=(audit.ROOT/'doc/src/content/docs/architecture/osc-panel.mdx').read_text()
        self.assertIn(f'put the outer jack columns at x = {left} and {right} mm',doc)
        report=(audit.ROOT/'boards/panel/reports/visual-review.md').read_text()
        self.assertIn(f'outer jack columns are x = {left}/{right}',report)
        self.assertIn(f"{trial['nearest_panel_edge_mm']:.2f} mm",report)
        matrix=(audit.OUT.parent/'README.md').read_text()
        for b in self.result['blocks']:
            row=f"| {b['id']} | {b['family']} | {b['inputs']} / {b['outputs']} | {b['controls']} | {b['leds']} | {b['electrical_overrides']} | {b['owner_semantics'].replace('_',' ')} |"
            self.assertIn(row,matrix)

    def test_preview_all_apertures_from_lock(self):
        subprocess.run(['node','scripts/panel/render_current.cjs','--check'],cwd=audit.ROOT,check=True,capture_output=True)
        tree=ET.fromstring((audit.OUT.parent/'current-panel.svg').read_text())
        circles={x.attrib['data-uid']:x.attrib for x in tree.iter() if 'data-uid' in x.attrib}
        self.assertEqual(set(circles),{r['uid'] for r in self.lock['placements']})
        for row in self.lock['placements']:
            c=circles[row['uid']];d=self.params['indicator_window']['diameter_mm'] if row['kind']=='led' else row['hole_d_mm']
            self.assertEqual((float(c['cx']),float(c['cy']),float(c['r'])),(row['x_mm'],row['y_mm'],d/2))
        switch_text=[x for x in tree.iter() if x.attrib.get('data-label-kind')=='switch']
        self.assertEqual(len(switch_text),71)
        self.assertTrue(all(float(x.attrib['font-size'])==self.params['artwork']['switch_text_height_mm'] for x in switch_text))

if __name__=='__main__':unittest.main()
