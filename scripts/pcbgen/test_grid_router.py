"""Synthetic tests for the grid router and the cut-line capacity bound."""
import math
import unittest
import numpy as np
from scripts.pcbgen.grid_router import negotiate,astar,astar_py,copper_rows,fill_partition,fill_region_count,native_astar,route,splits
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
        results,_=negotiate(crossing_board(),['A','B'],res=0.1,clearance=0.2,width=0.2,layer_cost=[1.0],log=lambda m:None,workers=2,waves=2)
        self.assertEqual({r['net'] for r in results if r['path']},{'A','B'})


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
