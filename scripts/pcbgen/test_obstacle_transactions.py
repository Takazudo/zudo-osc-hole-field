"""Issue #189: probes and rip-up must describe the geometry actually removed."""
import unittest
import json
from unittest.mock import patch
import numpy as np
from scripts.pcbgen import grid_router as router
from scripts.pcbgen.test_grid_router import board, square, MM


class ObstacleTransactionTests(unittest.TestCase):
    def test_soft_probe_keeps_fixed_foreign_pad_hard(self):
        dump=board();dump['layers']=['B.Cu']
        dump['pads'].append(dict(uuid='fixed',ref='J1',pad='1',net='B',xy=[6*MM,4*MM],
            layers=['B.Cu'],poly=[[5*MM,0],[7*MM,0],[7*MM,8*MM],[5*MM,8*MM]],drill=0,npth=False))
        original=router.astar;probes=[]
        def observe(free,via,src,goal,*args):
            if args[-1] is not None:
                # window_mm covers the whole board, including the raster border.
                probes.append(bool(free[0,41,61]))
            return original(free,via,src,goal,*args)
        with patch.object(router,'astar',side_effect=observe):
            results,removed=router.route(dump,['A'],rrr_rounds=1,window_mm=50,
                res=.1,clearance=.2,signal_width=.2,log=lambda _:None)
        self.assertTrue(probes)
        self.assertFalse(any(probes),'soft search made an immovable foreign pad traversable')
        self.assertFalse(removed)
        self.assertTrue(all(r['path'] is None for r in results))

    def test_removed_via_hole_is_rebuilt_and_rollback_restores_it(self):
        dump=board(walls=((6,'B.Cu'),));dump['layers']=['B.Cu']
        dump['vias']=[dict(uuid='victim-via',net='B',xy=[6*MM,4*MM],diameter=600000,drill=300000)]
        dump['pads'].append(dict(uuid='b',ref='J1',pad='1',net='B',xy=[6*MM,MM],
            layers=['B.Cu'],poly=square(6,1),drill=0,npth=False))
        dump['pads'].append(dict(uuid='guard',ref='P',pad='1',net='P',xy=[MM,MM],
            layers=['B.Cu'],poly=square(1,1),drill=0,npth=False))
        instances=[];original=router.Raster;transaction=[];before=[];probed=False
        guards=[];guard_before=[];original_guard=router.FillGuard
        class CaptureGuard(original_guard):
            def __init__(self,*args,**kw):
                super().__init__(*args,**kw);guards.append(self)

        class Capture(original):
            def __init__(self,*args,**kw):
                super().__init__(*args,**kw);instances.append(self)
        def search(free,via,src,goal,*args):
            nonlocal probed
            r=instances[0]
            if args[-1] is not None:
                before.append((r.label.copy(),r.hole.copy(),list(r.route_holes) if hasattr(r,'route_holes') else None));probed=True
                guard_before.append((guards[0].region.copy(),guards[0].base[:],guards[0].blobs.copy(),guards[0].n))
                l,y,x=map(int,np.argwhere(src)[0]);_,gy,gx=map(int,np.argwhere(goal)[0])
                # The synthetic probe crosses B's removable track/via. Fail the real
                # transaction so the final assertions also exercise rollback.
                return [(l,y,i) for i in range(x,gx-1,-1)],0
            if probed:transaction.append(bool(r.hole[r.cell(6*MM,4*MM)]))
            return None,0
        with patch.object(router,'Raster',Capture),patch.object(router,'FillGuard',CaptureGuard),patch.object(router,'astar',side_effect=search):
            results,removed=router.route(dump,['A'],rrr_rounds=1,window_mm=50,fill_guards={'P':'B.Cu'},
                res=.1,clearance=.2,signal_width=.2,log=lambda _:None)
        self.assertTrue(transaction,'fixture did not enter a rip-up transaction')
        self.assertFalse(any(transaction),'removed via left a ghost drill exclusion')
        np.testing.assert_array_equal(instances[0].label,before[0][0])
        np.testing.assert_array_equal(instances[0].hole,before[0][1])
        self.assertEqual(removed,[])
        self.assertEqual(instances[0].route_holes,before[0][2])
        np.testing.assert_array_equal(guards[0].region,guard_before[0][0])
        self.assertEqual(guards[0].base,guard_before[0][1])
        np.testing.assert_array_equal(guards[0].blobs,guard_before[0][2])
        self.assertEqual(guards[0].n,guard_before[0][3])

    def test_rebuild_preserves_fixed_overlapping_and_new_drills(self):
        dump=board();dump['layers']=['B.Cu','F.Cu']
        for uid,x,npth in [('pth',4,False),('mount',8,True)]:
            dump['pads'].append(dict(uuid=uid,ref=uid,pad='1',net='B' if not npth else '',
                xy=[x*MM,2*MM],layers=dump['layers'],poly=square(x,2),drill=500000,npth=npth))
        dump['vias']=[dict(uuid=uid,net=net,xy=[x*MM,y*MM],diameter=600000,drill=300000)
            for uid,net,x,y in [('gone','A',4,2),('overlap','B',4,2),('survivor','B',6,2),('free','A',10,2)]]
        r=router.Raster(dump,.1)
        result=dict(net='B',path=[['B.Cu',6*MM,6*MM,0],['F.Cu',6*MM,6*MM,0]],
                    width_nm=200000,via_diameter_nm=600000)
        r.add_result(result,.3)
        r.rebuild_routes({'gone','free'},[result])
        for x,y in [(4,2),(6,2),(8,2),(6,6)]:self.assertTrue(r.hole[r.cell(x*MM,y*MM)])
        self.assertFalse(r.hole[r.cell(10*MM,2*MM)])
        clean=router.Raster(dump,.1,skip={'gone','free'});clean.add_result(result,.3)
        np.testing.assert_array_equal(r.hole,clean.hole)
        np.testing.assert_array_equal(r.label,clean.label)
        # Softening every route still cannot remove component or mounting drills.
        soft=r.holes_without(r.net_id.values())
        self.assertTrue(soft[r.cell(4*MM,2*MM)])
        self.assertTrue(soft[r.cell(8*MM,2*MM)])
        self.assertFalse(soft[r.cell(6*MM,2*MM)])
        self.assertFalse(soft[r.cell(6*MM,6*MM)])

    def test_same_net_terminal_access_and_removable_blocker_still_work(self):
        from scripts.pcbgen.test_grid_router import crossing_board
        events=[]
        results,removed=router.route(crossing_board(),['A','B'],rrr_rounds=2,
            res=.1,clearance=.2,signal_width=.2,layer_cost=[1.0],diagnostics=events,log=lambda _:None)
        self.assertEqual({r['net'] for r in results if r['path']},{'A','B'})
        self.assertFalse([r for r in results if not r['path']])
        probes=[e for e in events if e['reason']=='probe_candidate']
        self.assertTrue(probes)
        for event in probes:
            self.assertEqual(event['native_status'],'NOT RUN')
            self.assertTrue(event['probe_path_nm'])
            self.assertTrue(all(layer=='B.Cu' and isinstance(x,int) and isinstance(y,int)
                                for layer,x,y in event['probe_path_nm']))
            self.assertGreater(max(x for _,x,_ in event['probe_path_nm']),MM)

    def test_failure_diagnostics_report_limits_without_inventing_blockers(self):
        events=[]
        results,_=router.route(board(),['A'],max_expansions=1,window_mm=.5,diagnostics=events,log=lambda _:None)
        self.assertTrue(events)
        self.assertEqual(events[0]['reason'],'expansion_limit')
        self.assertTrue(events[0]['attempts'])
        json.dumps(events)  # diagnostics must survive an actual benchmark receipt
        self.assertTrue(all(r['path'] is None for r in results))

    def test_fill_guard_rejection_is_distinguished_from_search_failure(self):
        dump=board();events=[]
        dump['pads'].append(dict(uuid='guard',ref='P',pad='1',net='P',xy=[MM,MM],
            layers=['B.Cu'],poly=square(1,1),drill=0,npth=False))
        with patch.object(router.FillGuard,'keeps',return_value=False):
            router.route(dump,['A'],fill_guards={'P':'B.Cu'},diagnostics=events,log=lambda _:None)
        rejected=[e for e in events if e['reason']=='fill_guard_disconnection']
        self.assertTrue(rejected)
        self.assertEqual(rejected[0]['guard_layers'],['B.Cu'])


if __name__=='__main__':unittest.main()
