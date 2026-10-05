"""Rip-up round bookkeeping in the staged grid-routing driver."""
import json
import unittest

import scripts.pcbgen.route_jack_grid as driver


class Board:
    def with_name(self,name):return self
    def read_text(self):return json.dumps({'pads':[],'islands':{}})


class RipUpRoundTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.saved=(driver.signal_chunk,driver.route,driver.copper_rows)
        driver.RRR_TRIED.clear();driver.RRR_ROUND.update(round=0,adopted=False,done=False)
        driver.signal_chunk=lambda dump,chunk,max_span_mm=None,skip=(),only=None:[n for n in ('a','b','c') if n not in skip][:2]
        driver.route=lambda dump,nets,**kw:(self.calls.append((list(nets),kw['rrr_max_rip'],kw['window_mm'])),([],[]))[1]
        driver.copper_rows=lambda *a:([],[])
        self.spec=next(s for s in driver.STAGES if s['name']=='rrr-01')

    def tearDown(self):
        driver.signal_chunk,driver.route,driver.copper_rows=self.saved

    def batch(self,adopted):
        try:driver.stage('fixture',Board(),self.spec,{},lambda m:None)
        except Exception:pass  # the native check after routing is not part of this fixture
        if adopted:driver.RRR_ROUND['adopted']=True

    def test_open_nets_are_reoffered_with_a_larger_budget_until_a_round_adopts_nothing(self):
        for adopted in (True,False,False,False,False):self.batch(adopted)
        self.assertEqual(self.calls,[(['a','b'],4,12.0),(['c'],4,12.0),(['a','b'],6,16.0),(['c'],6,16.0)])
        self.assertTrue(driver.RRR_ROUND['done'])


class HotspotRegionTests(unittest.TestCase):
    def test_stranded_pins_cluster_largest_first(self):
        mm=1_000_000
        pad=lambda u,net,x,y:{'uuid':u,'ref':'R'+u,'pad':'1','net':net,'xy':[x*mm,y*mm]}
        # A: main island of two pads far away, stranded pins s1/s2 near (10,10); B: one stranded pin near (80,80).
        pads=[pad('a0','A',100,0),pad('a1','A',101,0),pad('s1','A',10,10),pad('s2','A',12,11),
              pad('b0','B',0,90),pad('b1','B',1,90),pad('s3','B',80,80),pad('r0','+12V',50,50),pad('r1','+12V',60,60)]
        dump={'pads':pads,'islands':{'A':[['a0','a1'],['s1'],['s2']],'B':[['b0','b1'],['s3']],'+12V':[['r0'],['r1']]}}
        regions=driver.hotspot_regions(dump,8)
        self.assertEqual([r[2] for r in regions],[2,1])
        self.assertEqual(list(regions[0][0]/mm),[10.0,10.0])


class StageRejectionTests(unittest.TestCase):
    def test_unrepairable_candidate_is_rejected_not_fatal(self):
        saved=driver.stage
        def failing(*args,**kwargs):raise driver.StageRejected('DRC errors persist after dropping culprit links')
        driver.stage=failing
        try:
            logs=[]
            board=type('B',(),{'with_name':lambda self,n:self,'read_text':lambda self:json.dumps({'open_edges':42})})()
            candidate,receipt=driver.run_stage('fixture',board,{'name':'region-02'},{},logs.append)
        finally:driver.stage=saved
        self.assertIsNone(candidate)
        self.assertTrue(receipt['rejected'])
        self.assertEqual((receipt['open_edges_before'],receipt['open_edges_after']),(42,42))
        self.assertIn('keeping the previous board',logs[0])


if __name__=='__main__':
    unittest.main()
