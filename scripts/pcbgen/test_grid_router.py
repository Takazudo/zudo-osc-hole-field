"""Synthetic tests for the grid router and the cut-line capacity bound."""
import math
import unittest
import numpy as np
from scripts.pcbgen.grid_router import FillGuard,plateaued,negotiate,astar,astar_py,copper_rows,fill_partition,fill_region_count,native_astar,route,splits
from scripts.pcbgen.cut_capacity import scan,summarize

MM=1_000_000


def square(x,y,half=0.3):
    return [[int((x-half)*MM),int((y-half)*MM)],[int((x+half)*MM),int((y-half)*MM)],[int((x+half)*MM),int((y+half)*MM)],[int((x-half)*MM),int((y+half)*MM)]]


def board(walls=(),ring=False):
    edges=[[0,0,12*MM,0],[12*MM,0,12*MM,8*MM],[12*MM,8*MM,0,8*MM],[0,8*MM,0,0]]
    pads=[{'uuid':f'p{i}','ref':f'R{i}','pad':'1','net':'A','xy':[int(x*MM),4*MM],'layers':['B.Cu'],'poly':square(x,4),'drill':0,'npth':False,'locked':False}
          for i,x in enumerate((2,10))]
    tracks=[{'uuid':f'w{i}','net':'B','a':[int(x*MM),int(1*MM)],'b':[int(x*MM),int(7*MM)],'width':int(0.3*MM),'layer':layer} for i,(x,layer) in enumerate(walls)]
    if ring:
        pts=[(1,3),(3,3),(3,5),(1,5),(1,3)]
        for k,((ax,ay),(bx,by)) in enumerate(zip(pts,pts[1:])):
            for layer in ('F.Cu','In1.Cu','In2.Cu','B.Cu'):
                tracks.append({'uuid':f'r{k}{layer}','net':'B','a':[ax*MM,ay*MM],'b':[bx*MM,by*MM],'width':int(0.3*MM),'layer':layer})
    return {'board_sha256':'0','pads':pads,'tracks':tracks,'vias':[],'keepouts':[],'edges':edges,'islands':{'A':[['p0'],['p1']]}}


def seg_distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];length=dx*dx+dy*dy or 1
    u=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length));return math.hypot(a[0]+u*dx-p[0],a[1]+u*dy-p[1])


class GridRouterTests(unittest.TestCase):
    def route(self,dump,layer_cost=(3,1,1.3,3)):
        return route(dump,res=0.1,clearance=0.2,signal_width=0.2,layer_cost=layer_cost,log=lambda m:None)[0]

    def test_open_layer_routes_without_via(self):
        rows,_=copper_rows(self.route(board(),layer_cost=(1,1,1,1)),'fixture','t')
        self.assertTrue(rows)
        self.assertFalse([r for r in rows if r['kind']=='via'])

    def test_wall_forces_inner_layer_and_keeps_clearance(self):
        results=self.route(board(walls=((6,'B.Cu'),)))
        rows,_=copper_rows(results,'fixture','t')
        self.assertTrue([r for r in rows if r['kind']=='via'])
        wall=((6*MM,1*MM),(6*MM,7*MM))
        for r in rows:
            if r['kind']=='segment' and r['layer']=='B.Cu':
                for t in (i/20 for i in range(21)):
                    p=(r['start_nm'][0]+t*(r['end_nm'][0]-r['start_nm'][0]),r['start_nm'][1]+t*(r['end_nm'][1]-r['start_nm'][1]))
                    self.assertGreaterEqual(seg_distance(p,*wall)-0.15*MM-0.1*MM,0.2*MM)

    def test_stranded_island_joins_its_nearest_island_not_only_the_largest(self):
        dump=board();pad=lambda i,x:{'uuid':f'p{i}','ref':f'R{i}','pad':'1','net':'A','xy':[int(x*MM),4*MM],'layers':['B.Cu'],'poly':square(x,4),'drill':0,'npth':False,'locked':False}
        dump['pads']=[pad(0,1.5),pad(1,2.5),pad(2,9.5),pad(3,10.5)]
        dump['islands']={'A':[['p0'],['p1'],['p2','p3']]}
        results=self.route(dump,layer_cost=(1,1,1,1))
        self.assertTrue(all(r['path'] for r in results))
        first=next(r for r in results if r['island']==['R0.1'])
        self.assertLess(max(x for _,x,_,*_ in first['path']),3.2*MM)

    def test_boxed_pad_reports_no_path(self):
        results=self.route(board(ring=True))
        self.assertIsNone(results[0]['path'])

    def test_six_layer_board_uses_only_allowed_layers(self):
        dump=board(walls=((6,'B.Cu'),));dump['layers']=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
        results=route(dump,res=0.1,clearance=0.2,signal_width=0.2,allowed_layers=['F.Cu','In2.Cu','B.Cu'],log=lambda m:None)[0]
        rows,_=copper_rows(results,'fixture','t')
        self.assertTrue(rows)
        self.assertLessEqual({r['layer'] for r in rows if r['kind']=='segment'},{'F.Cu','In2.Cu','B.Cu'})

    def test_rows_have_stable_uuids(self):
        a,_=copper_rows(self.route(board(walls=((6,'B.Cu'),))),'fixture','t')
        b,_=copper_rows(self.route(board(walls=((6,'B.Cu'),))),'fixture','t')
        self.assertEqual(a,b)

    def test_repeated_stage_different_geometry_has_different_uuids(self):
        result={'net':'A','island':['P.1'],'path':[['B.Cu',1000000,1000000,0],['B.Cu',2000000,1000000,0]],'width_nm':200000}
        first=copper_rows([result],'fixture','repeated-stage')[0][0]['uuid']
        for changed in ({**result,'width_nm':300000},
                        {**result,'path':[['B.Cu',1000000,2000000,0],['B.Cu',2000000,2000000,0]]}):
            self.assertNotEqual(first,copper_rows([changed],'fixture','repeated-stage')[0][0]['uuid'])


def crossing_board():
    edges=[[0,0,12*MM,0],[12*MM,0,12*MM,8*MM],[12*MM,8*MM,0,8*MM],[0,8*MM,0,0]]
    spots={'a0':('A',1.2,4),'a1':('A',10.8,4),'b0':('B',6,2),'b1':('B',6,6)}
    pads=[{'uuid':u,'ref':'R'+u,'pad':'1','net':n,'xy':[int(x*MM),int(y*MM)],'layers':['B.Cu'],'poly':square(x,y),'drill':0,'npth':False,'locked':False}
          for u,(n,x,y) in spots.items()]
    return {'board_sha256':'0','layers':['B.Cu'],'pads':pads,'tracks':[],'vias':[],'keepouts':[],'edges':edges,
            'islands':{'A':[['a0'],['a1']],'B':[['b0'],['b1']]}}


class RipUpTests(unittest.TestCase):
    def test_rip_up_reroutes_a_blocking_net(self):
        common=dict(res=0.1,clearance=0.2,signal_width=0.2,layer_cost=[1.0],log=lambda m:None)
        greedy=route(crossing_board(),['A','B'],**common)[0]
        self.assertEqual({r['net'] for r in greedy if not r['path']},{'B'})
        repaired=route(crossing_board(),['A','B'],rrr_rounds=2,**common)[0]
        self.assertEqual({r['net'] for r in repaired if r['path']},{'A','B'})
        self.assertFalse([r for r in repaired if not r['path']])

    def test_rip_up_reads_neck_flagged_paths(self):
        # B gets a third pad, so one B link is already routed (neck-flagged 5-element points)
        # when its blocked link is retried by rip-up.
        dump=crossing_board()
        dump['pads'].append({'uuid':'b2','ref':'Rb2','pad':'1','net':'B','xy':[6*MM,int(7.2*MM)],'layers':['B.Cu'],'poly':square(6,7.2),'drill':0,'npth':False,'locked':False})
        dump['islands']['B']=[['b0'],['b1'],['b2']]
        dump['keepouts']=[{'name':'NECKDOWN','layers':['B.Cu'],'poly':[[0,0],[12*MM,0],[12*MM,8*MM],[0,8*MM]],'tracks':False,'vias':False}]
        results=route(dump,['A','B'],rrr_rounds=2,res=0.1,clearance=0.2,signal_width=0.2,layer_cost=[1.0],
                      neck_width=0.15,neck_clearance=0.15,log=lambda m:None)[0]
        self.assertTrue(any(len(p)==5 for r in results if r['path'] for p in r['path']))
        self.assertFalse([r for r in results if not r['path']])

    def test_rip_only_protects_nets_outside_the_shard(self):
        common=dict(res=0.1,clearance=0.2,signal_width=0.2,layer_cost=[1.0],log=lambda m:None,rrr_rounds=2)
        guarded=route(crossing_board(),['A','B'],rip_only={'B'},**common)[0]
        self.assertEqual({r['net'] for r in guarded if not r['path']},{'B'})
        allowed=route(crossing_board(),['A','B'],rip_only={'A','B'},**common)[0]
        self.assertFalse([r for r in allowed if not r['path']])

    def test_rip_up_runs_with_a_plane_fill_guard(self):
        # The guard's state is saved, reset after the rip and restored on undo.
        dump=crossing_board()
        dump['pads'].append({'uuid':'pp','ref':'RP','pad':'1','net':'P','xy':[int(0.8*MM),int(0.8*MM)],'layers':['B.Cu'],
                             'poly':square(0.8,0.8),'drill':0,'npth':False,'locked':False})
        repaired=route(dump,['A','B'],rrr_rounds=2,fill_guards={'P':'B.Cu'},fill_clearance=0.2,
                       res=0.1,clearance=0.2,signal_width=0.2,layer_cost=[1.0],log=lambda m:None)[0]
        self.assertEqual({r['net'] for r in repaired if r['path']},{'A','B'})


class NativeSearchTests(unittest.TestCase):
    def test_native_and_python_search_agree_on_cost(self):
        if native_astar() is None:self.skipTest('no C compiler')
        rng=np.random.default_rng(3);free=rng.random((2,40,50))>0.25
        src=np.zeros_like(free);goal=np.zeros_like(free);src[0,2,2]=free[0,2,2]=True;goal[1,37,47]=free[1,37,47]=True
        via_ok=rng.random((40,50))>0.6
        def cost(path):
            total=0.0
            for (l,y,x),(m,v,u) in zip(path,path[1:]):total+=30 if l!=m else (1.41421356 if y!=v and x!=u else 1.0)*(1,2)[m]
            return total
        a,_=astar(free,via_ok,src,goal,(1,2),30,10**7);b,_=astar_py(free,via_ok,src,goal,(1,2),30,10**7)
        self.assertEqual(a is None,b is None)
        if a:self.assertAlmostEqual(cost(a),cost(b),places=3)


class NegotiationTests(unittest.TestCase):
    def test_negotiation_resolves_a_greedy_block(self):
        results,removed=negotiate(crossing_board(),['A','B'],res=0.1,clearance=0.2,width=0.2,layer_cost=[1.0],log=lambda m:None)
        self.assertEqual({r['net'] for r in results if r['path']},{'A','B'})
        self.assertFalse([r for r in results if not r['path']])

    def test_parallel_waves_match_the_serial_outcome(self):
        results,_=negotiate(crossing_board(),['A','B'],res=0.1,clearance=0.2,width=0.2,layer_cost=[1.0],log=lambda m:None,workers=2)
        self.assertEqual({r['net'] for r in results if r['path']},{'A','B'})


def detour_board(wall_half_mm):
    # A on two pads 16 mm apart; a B wall across all of the board's single layer except its ends.
    edges=[[0,0,30*MM,0],[30*MM,0,30*MM,40*MM],[30*MM,40*MM,0,40*MM],[0,40*MM,0,0]]
    pads=[{'uuid':f'a{i}','ref':f'R{i}','pad':'1','net':'A','xy':[int(x*MM),20*MM],'layers':['B.Cu'],'poly':square(x,20),'drill':0,'npth':False,'locked':False}
          for i,x in enumerate((7,23))]
    wall=[{'uuid':'w','net':'B','a':[15*MM,int((20-wall_half_mm)*MM)],'b':[15*MM,int((20+wall_half_mm)*MM)],'width':int(0.3*MM),'layer':'B.Cu'}]
    return {'board_sha256':'0','layers':['B.Cu'],'pads':pads,'tracks':wall,'vias':[],'keepouts':[],'edges':edges,'islands':{'A':[['a0'],['a1']]}}


class WindowEscalationTests(unittest.TestCase):
    def negotiate(self,dump,**kw):
        log=[]
        results,_=negotiate(dump,['A'],res=0.1,clearance=0.2,width=0.2,layer_cost=[1.0],margin_mm=4.0,log=log.append,**kw)
        return results,log

    def test_path_outside_the_first_window_is_found_in_the_wide_window(self):
        # The wall reaches 8 mm past the pads: the 4 mm window has no path, the 12 mm one does.
        results,log=self.negotiate(detour_board(8))
        self.assertTrue(results[0]['path'],log)
        self.assertTrue(any(abs(y-20*MM)>4*MM for _,_,y,_ in results[0]['path']))

    def test_full_board_is_the_last_resort(self):
        # The wall reaches 15 mm past the pads: only a full-board window gets around it.
        results,log=self.negotiate(detour_board(15),wide_margin_mm=12.0)
        self.assertTrue(results[0]['path'],log)
        self.assertTrue(any('[0, 0, 0, 1]' in m for m in log),log)


class PlateauTests(unittest.TestCase):
    def test_stops_only_after_a_flat_window(self):
        self.assertFalse(plateaued([100,90,80],10,0.05))
        self.assertFalse(plateaued([100]+[60]*9+[94],10,0.05))
        self.assertTrue(plateaued([100]+[98]*10,10,0.05))
        self.assertFalse(plateaued([100]+[98]*9+[94],10,0.05))


def neck_board(neck):
    # Net A must pass a 0.6 mm copper gap between two B walls: too narrow for 0.2/0.2, enough for 0.15/0.15.
    edges=[[0,0,12*MM,0],[12*MM,0,12*MM,8*MM],[12*MM,8*MM,0,8*MM],[0,8*MM,0,0]]
    pads=[{'uuid':f'a{i}','ref':f'R{i}','pad':'1','net':'A','xy':[int(x*MM),4*MM],'layers':['B.Cu'],'poly':square(x,4),'drill':0,'npth':False,'locked':False}
          for i,x in enumerate((2,10))]
    walls=[{'uuid':'w1','net':'B','a':[6*MM,int(0.5*MM)],'b':[6*MM,int(3.6*MM)],'width':int(0.2*MM),'layer':'B.Cu'},
           {'uuid':'w2','net':'B','a':[6*MM,int(4.4*MM)],'b':[6*MM,int(7.5*MM)],'width':int(0.2*MM),'layer':'B.Cu'}]
    area=[{'name':'NECKDOWN','layers':['B.Cu'],'poly':[[4*MM,2*MM],[8*MM,2*MM],[8*MM,6*MM],[4*MM,6*MM]],'tracks':False,'vias':False}]
    return {'board_sha256':'0','layers':['B.Cu'],'pads':pads,'tracks':walls,'vias':[],'keepouts':area if neck else [],'edges':edges,'islands':{'A':[['a0'],['a1']]}}


class NeckDownTests(unittest.TestCase):
    def route(self,neck):
        return route(neck_board(neck),res=0.05,clearance=0.2,signal_width=0.2,layer_cost=[1.0],neck_width=0.15,neck_clearance=0.15,log=lambda m:None)[0]

    def test_gap_needs_the_neck_down_area(self):
        self.assertIsNone(self.route(False)[0]['path'])
        self.assertTrue(self.route(True)[0]['path'])

    def test_rail_cannot_use_signal_neckdown_even_without_grow(self):
        results,_=route(neck_board(True),res=.05,clearance=.2,signal_width=.2,
                        rail_width=.2,rail_nets=['A'],layer_cost=[1.0],
                        neck_width=.15,neck_clearance=.15,log=lambda m:None)
        self.assertIsNone(results[0]['path'])

    def test_ground_cannot_use_signal_neckdown_when_not_listed_as_rail(self):
        dump=neck_board(True)
        for pad in dump['pads']:pad['net']='AGND'
        dump['islands']={'AGND':dump['islands']['A']}
        results,_=route(dump,res=.05,clearance=.2,signal_width=.2,layer_cost=[1.0],
                        neck_width=.15,neck_clearance=.15,log=lambda m:None)
        self.assertIsNone(results[0]['path'])

    def test_negotiation_uses_the_neck_down_area(self):
        kw=dict(res=0.05,clearance=0.2,width=0.2,layer_cost=[1.0],neck_width=0.15,neck_clearance=0.15,log=lambda m:None)
        self.assertFalse(negotiate(neck_board(False),['A'],**kw)[0][0]['path'])
        results,_=negotiate(neck_board(True),['A'],**kw)
        self.assertEqual({r['width_nm'] for r in copper_rows(results,'fixture','t')[0] if r['kind']=='segment'},{150000,200000})

    def test_narrow_only_inside_the_area_and_clear_of_the_walls(self):
        rows,_=copper_rows(self.route(True),'fixture','t')
        segs=[r for r in rows if r['kind']=='segment']
        self.assertEqual({r['width_nm'] for r in segs},{150000,200000})
        walls=[((6*MM,int(0.5*MM)),(6*MM,int(3.6*MM))),((6*MM,int(4.4*MM)),(6*MM,int(7.5*MM)))]
        for r in segs:
            if r['width_nm']==150000:self.assertTrue(any(4*MM<=p[0]<=8*MM and 2*MM<=p[1]<=6*MM for p in (r['start_nm'],r['end_nm'])))
            for t in (i/40 for i in range(41)):
                p=(r['start_nm'][0]+t*(r['end_nm'][0]-r['start_nm'][0]),r['start_nm'][1]+t*(r['end_nm'][1]-r['start_nm'][1]))
                for w in walls:self.assertGreaterEqual(seg_distance(p,*w)-0.1*MM-r['width_nm']/2,0.15*MM-1)


class FillGuardTests(unittest.TestCase):
    def test_wall_across_fill_splits_plane_regions(self):
        label=np.zeros((40,80),np.int32);label[20,5]=7;label[20,75]=7
        self.assertEqual(fill_region_count(label,7,0.2,0.1),1)
        label[:,40]=3
        self.assertEqual(fill_region_count(label,7,0.2,0.1),2)
        label[18:23,40]=0
        self.assertEqual(fill_region_count(label,7,0.2,0.1),1)

    def test_partition_detects_split_even_when_count_is_unchanged(self):
        label=np.zeros((40,80),np.int32);label[10,5]=7;label[10,75]=7;label[30,5]=7;label[30,75]=7
        label[20,:]=3  # two fill regions, each holding a left and a right blob
        before=fill_partition(label,7,0.2,0.1)
        after_label=label.copy();after_label[20,:]=0;after_label[:,40]=3
        after=fill_partition(after_label,7,0.2,0.1)
        self.assertEqual(len({c for c in before}),len({c for c in after}))
        self.assertTrue(splits(before,after))

    def test_incremental_guard_matches_full_recomputation(self):
        rng=np.random.default_rng(3);label=np.zeros((60,90),np.int32)
        label[[10,10,50,50],[5,85,5,85]]=7;label[30,10:80:7]=4
        guard=FillGuard(label,7,0.2,0.1);region=guard.region;full=label.copy()
        for _ in range(12):
            y,x=int(rng.integers(0,56)),int(rng.integers(0,86));m=np.ones((4,4),bool)
            region=guard.shrunk([(m,(slice(y,y+4),slice(x,x+4)))],region);full[y:y+4,x:x+4]=-1
            self.assertEqual(guard.partition(region),fill_partition(full,7,0.2,0.1))
        wall=np.ones((60,1),bool)
        self.assertFalse(guard.keeps(guard.shrunk([(wall,(slice(0,60),slice(45,46)))])))


class CutCapacityTests(unittest.TestCase):
    def test_wall_reduces_only_its_layer(self):
        dump=board(walls=((6,'F.Cu'),))
        dump['tracks'][0].update({'a':[1*MM,4*MM],'b':[11*MM,4*MM]})
        rows=scan(dump,step_mm=1)
        line=next(r for r in rows if r['axis']=='x' and abs(r['position_mm']-6)<0.6)
        self.assertEqual(line['demand'],1)
        self.assertLess(line['capacity']['F.Cu'],line['capacity']['In1.Cu'])
        summary=summarize(rows)
        self.assertGreater(summary['worst_lines'][0]['signal_ratio'],1)


if __name__=='__main__':
    unittest.main()
