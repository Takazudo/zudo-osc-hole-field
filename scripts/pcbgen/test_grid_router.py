"""Synthetic tests for the grid router and the cut-line capacity bound."""
import math
import unittest
from scripts.pcbgen.grid_router import copper_rows,route
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

    def test_rows_have_stable_uuids(self):
        a,_=copper_rows(self.route(board(walls=((6,'B.Cu'),))),'fixture','t')
        b,_=copper_rows(self.route(board(walls=((6,'B.Cu'),))),'fixture','t')
        self.assertEqual(a,b)


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
