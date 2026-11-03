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

    def test_open_nets_are_reoffered_with_every_larger_budget_even_after_a_round_adopts_nothing(self):
        for _ in range(12):self.batch(False)
        budgets=[(4,12.0),(8,16.0),(12,20.0),(20,24.0)]
        self.assertEqual(self.calls,[(nets,rip,window) for rip,window in budgets for nets in (['a','b'],['c'])])
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


class SettledRefillTests(unittest.TestCase):
    def passes(self,counts,memberships=None):
        """check() against a fake oracle whose successive refills report these AGND island counts."""
        files={};seq=iter(counts);groups=iter(memberships) if memberships is not None else None
        class Path_:
            def __init__(self,name):self.name=name
            def with_name(self,name):return Path_(name)
            def read_text(self):return files[self.name]
        def run(*args):
            if any(a.endswith('grid_dump.py') for a in args):
                n=next(seq);files['dump.json']=json.dumps({'open_edges':n-1,'islands':{'AGND':next(groups) if groups is not None else [[i] for i in range(n)]}})
            else:files['drc.json']=json.dumps({'violations':[],'schematic_parity':[]})
        saved=driver.run,driver.rel;driver.run,driver.rel=run,lambda p:p.name
        try:return driver.check(Path_('board.kicad_pcb'))[1]['open_edges']
        finally:driver.run,driver.rel=saved

    def test_two_equal_passes_are_not_settled(self):
        self.assertEqual(self.passes([30,24,24,30,30,30]),29)

    def test_refills_that_never_hold_raise(self):
        with self.assertRaises(driver.FillUnsettled):self.passes([24,30,24,30,24,30])

    def test_equal_counts_with_changing_memberships_are_not_settled(self):
        a=[['a','b'],['c']];b=[['a'],['b','c']]
        with self.assertRaises(driver.FillUnsettled):self.passes([2]*6,[a,b,a,b,a,b])

    def test_island_enumeration_does_not_prevent_convergence(self):
        self.assertEqual(self.passes([2]*3,[[['a','b'],['c']],[['c'],['b','a']],[['a','b'],['c']]]),1)


class StitchedCandidateTests(unittest.TestCase):
    def judge(self,stitch_after):
        current=type('B',(),{'with_name':lambda self,n:self,'read_text':lambda self:json.dumps({'open_edges':150,'islands':{'AGND':[[0]]*21}})})()
        receipt={'open_edges_before':150,'open_edges_after':150,'open_by_net_after':{'AGND':27},'links_added':9}
        saved=driver.run_stage,driver.RUN['shard'];driver.RUN['shard']=None
        driver.run_stage=lambda *a:('stitched-board',{'open_edges_after':stitch_after,'open_by_net_after':{'AGND':stitch_after-123},'links_added':6,'links_dropped_for_drc':0,'copper_rows':12})
        try:return driver.stitched('fixture',current,'signal-board',receipt,{'name':'region-02'},{},lambda m:None)
        finally:driver.run_stage,driver.RUN['shard']=saved

    def test_signal_gain_hidden_by_cut_pours_is_kept_after_stitching(self):
        board,receipt=self.judge(144)
        self.assertEqual(board,'stitched-board')
        self.assertEqual((receipt['open_edges_before'],receipt['open_edges_after']),(150,144))

    def test_stitching_that_does_not_lower_the_total_keeps_the_signal_verdict(self):
        board,receipt=self.judge(150)
        self.assertEqual((board,receipt['open_edges_after']),('signal-board',150))


class HoleSpacingTests(unittest.TestCase):
    def via(self,uid,x,y):return {'kind':'via','uuid':uid,'net':'n','at_nm':[x,y],'drill_nm':300_000}

    def test_new_vias_below_the_hole_minimum_drop_their_link_only(self):
        dump={'pads':[{'xy':[0,0],'drill':1_000_000}],'vias':[{'uuid':'old','xy':[5_000_000,0],'drill':300_000}]}
        rows=[self.via('a',600_000,0),self.via('b',5_400_000,0),self.via('c',9_000_000,0),self.via('d',9_100_000,0),self.via('e',20e6,0)]
        links=[{'net':'n','copper_uuids':[u]} for u in 'abcde']
        bad=driver.hole_spacing_culprits(rows,links,dump)
        # a: 0.6-0.65=-0.05 mm to the pad drill; b: 0.1 mm to the old via; d yields to c (0.1-0.3 mm edge gap).
        self.assertEqual([l['copper_uuids'] for l in bad],[['a'],['b'],['d']])
        self.assertEqual(driver.hole_spacing_culprits(rows,links,dump,removed=['old'])[1]['copper_uuids'],['d'])

    def test_vias_at_the_minimum_are_kept(self):
        rows=[self.via('a',0,0),self.via('b',550_000,0)]
        self.assertEqual(driver.hole_spacing_culprits(rows,[{'net':'n','copper_uuids':['a','b']}],{'pads':[],'vias':[]}),[])

    def test_dropping_a_ripped_net_link_restores_its_old_copper(self):
        dump={'tracks':[{'uuid':'t','net':'s'}],'vias':[]}
        links=[{'net':'s','copper_uuids':['x']},{'net':'s','copper_uuids':['y']},{'net':'r','copper_uuids':['z']}]
        rows=[{'uuid':u} for u in 'xyz']
        culprits,rows,links,removed=driver.drop_links([links[0]],rows,links,['t'],dump)
        self.assertEqual((len(culprits),[r['uuid'] for r in rows],removed),(2,['z'],[]))

    def test_rail_links_guard_every_agnd_pour_layer(self):
        for name in ('rail-links','rail-escapes'):self.assertTrue(next(s for s in driver.STAGES if s['name']==name)['agnd_guard'])
        self.assertEqual(driver.AGND_POUR_LAYERS,['F.Cu','B.Cu','In1.Cu'])


class CompleteGateTests(unittest.TestCase):
    def files(self,folder,name,drc,dump):
        import pathlib
        d=pathlib.Path(folder)/name;d.mkdir();(d/'drc.json').write_text(json.dumps(drc));(d/'dump.json').write_text(json.dumps(dump));return d/'b.kicad_pcb'

    def test_uncapped_reports_keep_the_raw_verdict_without_audits(self):
        import tempfile
        with tempfile.TemporaryDirectory() as f:
            cur=self.files(f,'a',{'violations':[]},{});cand=self.files(f,'b',{'violations':[]},{})
            receipt={'adopted':True}
            self.assertIs(driver.complete_gate('x',cur,cand,receipt,{'name':'s'}),receipt);self.assertEqual(receipt,{'adopted':True})

    def test_capped_reports_without_prerequisites_skip_audits_and_keep_the_rejection(self):
        import tempfile
        row={'type':'silk_overlap','severity':'warning','items':[]}
        with tempfile.TemporaryDirectory() as f:
            cur=self.files(f,'a',{'violations':[row]*199},{});cand=self.files(f,'b',{'violations':[row]*199},{})
            r=driver.complete_gate('x',cur,cand,{'adopted':False,'split_pad_groups':[{'net':'AGND'}],'new_warning_identities':[],'native_errors':False,
                                              'open_edges_before':2,'open_edges_after':1},{'name':'s'})
            self.assertEqual((r['adopted'],r['capped_warning_types'],r['complete_native_warning_evidence_status']),(False,['silk_overlap'],'NOT RUN: native prerequisites failed'))


if __name__=='__main__':
    unittest.main()
