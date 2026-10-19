"""Source geometry checks only; neither native DRC nor physical validation."""
import json
from pathlib import Path
import unittest

D = json.loads(Path(__file__).with_name('design.json').read_text())

class DesignChecks(unittest.TestCase):
    def test_rails_and_marks(self):
        w, h = D['board']['overall']
        cuts = D['board']['v_cuts_y']
        self.assertGreaterEqual(min(w, cuts[1]-cuts[0]), 70)
        self.assertGreaterEqual(min(cuts[0], h-cuts[1]), 5)
        for x, y in D['fiducials']['centres']:
            clearance = min(x, w-x, y, h-y, *(abs(y-c) for c in cuts))-D['fiducials']['mask_diameter']/2
            self.assertGreaterEqual(clearance, 3.35)
        for x, y in D['tooling']['centres']:
            self.assertGreaterEqual(min(x,w-x,y,h-y,*(abs(y-c) for c in cuts))-D['tooling']['diameter']/2, 1)

    def test_mapping_and_land_clearance(self):
        pads = D['header']['pads']
        tps = D['testpads']
        self.assertEqual([p['number'] for p in pads], [1,2,3,4])
        self.assertEqual([p['net'] for p in pads], [p['net'] for p in tps])
        self.assertEqual(len(set(p['net'] for p in pads)), 4)
        self.assertTrue(all(p['net'] is None for p in D['header']['mechanical_pads']))
        for a,b in zip(pads,pads[1:]):
            self.assertAlmostEqual(b['at'][0]-a['at'][0],1.25)
            self.assertGreaterEqual(b['at'][0]-a['at'][0]-(a['size'][0]+b['size'][0])/2,D['clearance_min'])
        self.assertTrue(all(not p['paste'] for p in tps))

    def test_header_and_testpad_reservations(self):
        ox,oy = D['header']['origin']
        x0,y0,x1,y1 = D['header']['body_relative']
        body = [x0+ox,y0+oy,x1+ox,y1+oy]
        self.assertGreaterEqual(min(body[0],80-body[2],body[1]-10,90-body[3]),2.5)
        boxes = [body]
        for p in D['header']['pads']+D['header']['mechanical_pads']:
            x,y = p['at']; w,h = p['size']
            boxes.append([ox+x-w/2,oy+y-h/2,ox+x+w/2,oy+y+h/2])
        for p in D['testpads']:
            x,y = p['at']; r=p['diameter']/2
            boxes.append([x-r,y-r,x+r,y+r])
        for a,b,c,d in boxes:
            self.assertGreaterEqual(min(a,80-c,b-10,90-d),1)
            for k,l,m,n in D['clamp_keepouts_both_faces']:
                self.assertTrue(c<=k or a>=m or d<=l or b>=n)
        # Monotone fan-out is possible: endpoint order is identical.
        self.assertEqual(sorted(p['at'][0] for p in D['header']['pads']),[p['at'][0] for p in D['header']['pads']])
        self.assertEqual(sorted(p['at'][0] for p in D['testpads']),[p['at'][0] for p in D['testpads']])

if __name__ == '__main__':
    unittest.main()
