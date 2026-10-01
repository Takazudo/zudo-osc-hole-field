"""Exact new ownership must never mask changed prior copper or source sizes."""
import copy
import unittest
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.verify_parallel_source import verify_items


class ParallelSourceTests(unittest.TestCase):
    def fixture(self):
        row={'net':'+12V','cluster':'branch-1','via_xy_mm':[1,2],'via_diameter_mm':.7,'via_drill_mm':.3,
             'points_mm':[[0,2],[1,2]],'layer':'B.Cu','width_mm':.4,'pad':{'uuid':'pad-uuid','ref':'C1','pad':'1'}}
        spec={'board_id':'test','added':[row]};identity='+12V:branch-1'
        via=stable_uuid('test','rail-transfer-via',identity);track=stable_uuid('test','rail-transfer-track',identity+':0')
        native={'items':[{'uuid':via,'net':'+12V','analytic_primitives':{l:{'kind':'circle','centre_nm':[1000000,2000000],'half_size_nm':[350000,350000]} for l in ('F.Cu','In1.Cu','In2.Cu','B.Cu')}},
            {'uuid':track,'net':'+12V','analytic_primitives':{'B.Cu':{'kind':'segment','start_nm':[0,2000000],'end_nm':[1000000,2000000],'radius_nm':200000}}},
            {'uuid':'pad-uuid','ref':'C1','pad':'1','net':'+12V','xy_mm':[0,2]}],
            'holes':[{'uuid':via,'net':'+12V','plated':True,'size_mm':[.3,.3],'xy_mm':[1,2]}]}
        old={'footprint':{'U1':'original style'},'segment':{'old':'locked original copper'},'via':{},'arc':{}}
        new=copy.deepcopy(old);new['via'][via]='added';new['segment'][track]='added'
        return spec,native,old,new

    def test_prior_copper_and_source_dimensions_fail_closed(self):
        spec,native,old,new=self.fixture();self.assertEqual(verify_items(spec,native,old,new)['exact_source_new_uuid_counts']['via'],1)
        for defect in ('prior','extra','net','width','position','footprint'):
            n=copy.deepcopy(native);after=copy.deepcopy(new)
            if defect=='prior':after['segment']['old']='moved'
            elif defect=='extra':after['via']['unowned']='unexpected'
            elif defect=='net':n['items'][1]['net']='AGND'
            elif defect=='width':n['items'][1]['analytic_primitives']['B.Cu']['radius_nm']=150000
            elif defect=='position':n['items'][0]['analytic_primitives']['F.Cu']['centre_nm'][0]+=2
            else:after['footprint']['U1']='restyled'
            with self.subTest(defect=defect),self.assertRaises(ValueError):verify_items(spec,n,old,after)

class ParallelInventoryTests(unittest.TestCase):
    def test_shared_branch_needs_unique_full_height_cut(self):
        from scripts.pcbgen.parallel_feed_source import inventory
        def shape(x0,y0,x1,y1):
            return [{'shell':[[x0,y0],[x1,y0],[x1,y1],[x0,y1]],'holes':[]}]
        via={'uuid':'v','net':'+12V','copper':{l:shape(1.3,-.2,1.7,.2) for l in ('F.Cu','In1.Cu','In2.Cu','B.Cu')}}
        data={'items':[{'uuid':'p1','net':'+12V','ref':'U1','pad':'4','xy_mm':[0,0],'copper':{'B.Cu':shape(-.2,-.2,.2,.2)}},
            {'uuid':'p2','net':'+12V','ref':'C1','pad':'1','xy_mm':[1,0],'copper':{'B.Cu':shape(.8,-.2,1.2,.2)}},
            {'uuid':'t','net':'+12V','copper':{'B.Cu':shape(0,-.1,2,.1)}},via],
            'zones':[],'holes':[{'uuid':'v','net':'+12V','plated':True,'size_mm':[.3,.3],'xy_mm':[1.5,0]}]}
        rows=inventory(data);self.assertEqual(len(rows),1);self.assertTrue(rows[0]['sole_full_height_transfer_proved'])
        data['items'].append({'uuid':'inner-exit','net':'+12V','copper':{'In1.Cu':shape(1.5,-.1,2,.1)}})
        self.assertFalse(inventory(data)[0]['sole_full_height_transfer_proved'])
        data['items'].pop();second=copy.deepcopy(via);second['uuid']='v2'
        second['copper']={l:shape(1.7,-.2,2.1,.2) for l in via['copper']};data['items'].append(second)
        data['holes'].append({'uuid':'v2','net':'+12V','plated':True,'size_mm':[.3,.3],'xy_mm':[1.9,0]})
        self.assertEqual(inventory(data),[])


if __name__=='__main__':unittest.main()
