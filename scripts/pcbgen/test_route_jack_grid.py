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
        driver.signal_chunk=lambda dump,chunk,max_span_mm=None,skip=():[n for n in ('a','b','c') if n not in skip][:2]
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


if __name__=='__main__':
    unittest.main()
