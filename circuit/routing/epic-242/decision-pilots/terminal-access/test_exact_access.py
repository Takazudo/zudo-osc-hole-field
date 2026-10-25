"""Source geometry counterexamples; no router, KiCad or native process."""
import unittest
from exact_access import Geometry, terminal_clearance_upper_bound


def pad(uid='anchor',net='N',x=10,y=10,layer='F.Cu',half=.5):
    return {'uuid':uid,'ref':uid,'pad':'1','net':net,'xy':[x*1e6,y*1e6],'poly':[[a*1e6,b*1e6] for a,b in [(x-half,y-half),(x+half,y-half),(x+half,y+half),(x-half,y+half)]],'layers':[layer],'drill':0,'npth':False}


def fixture():
    return {'layers':['F.Cu','B.Cu'],'edges':[[0,0,30e6,0],[30e6,0,30e6,30e6],[30e6,30e6,0,30e6],[0,30e6,0,0]],'pads':[pad()],'tracks':[],'vias':[],'keepouts':[]}


class ExactAccessTests(unittest.TestCase):
    def test_full_width_valid_edge_and_via(self):
        g=Geometry(fixture())
        self.assertTrue(g.terminal_edge('anchor',[10,10],[12,10],'N','F.Cu',.5)['pass'])
        self.assertTrue(g.via([12,10],'N')['pass'])

    def test_tangent_tiny_overlap_and_wrong_named_terminal_rejected(self):
        g=Geometry(fixture())
        for start in ([10.5,10],[10.500001,10],[10.64,10]):
            self.assertFalse(g.terminal_edge('anchor',start,[12,10],'N','F.Cu',.3)['pass'])
        d=fixture();d['pads'].append(pad('other-own','N',14,10));g=Geometry(d)
        self.assertFalse(g.terminal_edge('anchor',[14,10],[16,10],'N','F.Cu',.3)['pass'])
        self.assertFalse(g.terminal_edge('anchor',[10,10],[12,10],'different','F.Cu',.3)['pass'])

    def test_inside_anchor_does_not_excuse_foreign_overlap(self):
        d=fixture();d['pads'].append(pad('foreign','X',10,10,half=.1));g=Geometry(d)
        self.assertTrue(g.contact('anchor',[10,10],'N','F.Cu')['pass'])
        self.assertFalse(g.terminal_edge('anchor',[10,10],[12,10],'N','F.Cu',.3)['pass'])

    def test_clear_end_centers_do_not_validate_crossing_segment(self):
        d=fixture();d['pads'].append(pad('blocker','X',14,10));g=Geometry(d)
        for p in ([10,10],[18,10]):self.assertTrue(g.segment(p,p,'N','F.Cu',.3)['pass'])
        self.assertFalse(g.terminal_edge('anchor',[10,10],[18,10],'N','F.Cu',.3)['pass'])

    def test_near_miss_track_uses_analytic_radius_and_full_width(self):
        d=fixture();d['tracks']=[{'uuid':'cross','net':'X','layer':'F.Cu','a':[11e6,10.49e6],'b':[13e6,10.49e6],'width':.2e6}];g=Geometry(d)
        self.assertFalse(g.segment([10,10],[14,10],'N','F.Cu',.3)['pass'])
        self.assertTrue(g.segment([10,10],[14,10],'N','F.Cu',.2)['pass'])

    def test_via_checks_other_layers_and_own_smd(self):
        d=fixture();d['pads'].append(pad('back','X',12,10,'B.Cu'));g=Geometry(d)
        self.assertTrue(g.segment([10,10],[12,10],'N','F.Cu',.3)['pass'])
        self.assertFalse(g.via([12,10],'N')['pass'])
        self.assertFalse(g.via([10,10],'N')['pass'])

    def test_existing_hole_policy_preserved_even_same_net(self):
        d=fixture();d['vias']=[{'uuid':'own-via','net':'N','xy':[12e6,10e6],'diameter':.6e6,'drill':.3e6}];g=Geometry(d)
        self.assertFalse(g.via([12.6,10],'N')['pass'])
        self.assertTrue(g.via([12.8,10],'N')['pass'])

    def test_nonplated_hole_blocks_foreign_clear_segment(self):
        d=fixture();h=pad('hole','',12,10,half=.01);h.update(poly=[],drill=1e6,npth=True,layers=[]);d['pads'].append(h)
        self.assertFalse(Geometry(d).segment([10,10],[14,10],'N','F.Cu',.3)['pass'])

    def test_board_cutout_not_filled_and_whole_segment_checked(self):
        d=fixture();d['edges'] += [[13e6,9e6,15e6,9e6],[15e6,9e6,15e6,11e6],[15e6,11e6,13e6,11e6],[13e6,11e6,13e6,9e6]];g=Geometry(d)
        for p in ([10,10],[18,10]):self.assertTrue(g.segment(p,p,'N','F.Cu',.3)['pass'])
        self.assertFalse(g.segment([10,10],[18,10],'N','F.Cu',.3)['pass'])
        self.assertFalse(g.via([14,10],'N')['pass'])

    def test_track_and_via_keepouts_respect_flags(self):
        for flag in ('tracks','vias'):
            d=fixture();d['keepouts']=[{'name':'guard','poly':[[11e6,9e6],[13e6,9e6],[13e6,11e6],[11e6,11e6]],'layers':['F.Cu'],'tracks':flag=='tracks','vias':flag=='vias'}];g=Geometry(d)
            self.assertEqual(g.segment([10,10],[14,10],'N','F.Cu',.3)['pass'],flag!='tracks')
            self.assertEqual(g.via([12,10],'N')['pass'],flag!='vias')

    def test_whole_pad_lipschitz_certificate_is_scoped_to_contact_policy(self):
        d=fixture();d['pads'][0]['poly']=[[9e6,9.8e6],[11e6,9.8e6],[11e6,10.2e6],[9e6,10.2e6]]
        for name,low,high in [('top',10.45,10.85),('bottom',9.15,9.55)]:
            p=pad(name,'X');p['poly']=[[8e6,low*1e6],[12e6,low*1e6],[12e6,high*1e6],[8e6,high*1e6]];d['pads'].append(p)
        g=Geometry(d);blocked=terminal_clearance_upper_bound(g,'anchor',.5)
        self.assertEqual(blocked['status'],'CENTER_INSIDE_CONTACT_BLOCKED_BY_FOREIGN_PADS')
        self.assertGreaterEqual(blocked['maximum_center_clearance_upper_mm'],.45)
        self.assertLess(blocked['maximum_center_clearance_upper_mm'],.451)
        permitted=terminal_clearance_upper_bound(g,'anchor',.3)
        self.assertEqual(permitted['status'],'NO_BLOCKAGE_CERTIFICATE')
        self.assertIn('off-pad',blocked['scope'])

    def test_invalid_dimensions_rejected(self):
        g=Geometry(fixture())
        with self.assertRaises(ValueError):g.via([12,10],'N',.3,.6)
        with self.assertRaises(ValueError):g.segment([10,10],[12,10],'N','F.Cu',-.3)

if __name__=='__main__':unittest.main()
