import copy
import sys
import unittest
import hashlib
import json
import tempfile
import shapely
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import feed_remedies as fr
import construct_access as ca

def pad(id='p', net='AGND'):
    return dict(id=id, kind='pad', ref='TP990032', pad='1', net=net, layers=['F.Cu'], center_mm=[5.,5.], polygon_mm=[[3,3],[7,3],[7,7],[3,7]])

def via(id, x, y, net='AGND'):
    return dict(id=id, kind='via', net=net, layers=list(ca.LAYERS), center_mm=[x,y], diameter_mm=.6, drill_mm=.3)

def fixture(extra=()):
    source={'board':'KA', 'objects':[pad(),via('v',5,5),*extra]}
    planes={'board':'KA','clipped_sheets':{n:[{'id':n+'-sheet', 'net':n,'layer':l,'polygon_mm':[[0,0],[10,0],[10,10],[0,10]],'holes_mm':[]}] for n,l in ca.NET_LAYER.items()}}
    plan={'targets':[dict(ref='TP990032',net='AGND',center_mm=[5.,5.],pad_id='p',parallel_via_centers_mm=[[4.,5.],[6.,5.]])]}
    return source,planes,plan

class Remedies(unittest.TestCase):
    def test_keeps_old_copper_and_adds_each_identity_once(self):
        src,pl,plan=fixture(); saved=copy.deepcopy(src)
        out,rep=fr.assess(src,pl,plan,'parallel-vias')
        self.assertEqual(src,saved);self.assertEqual(out['objects'][:2],saved['objects']);self.assertEqual(rep['added_count'],2)
        self.assertEqual(len({o['id'] for o in out['objects']}),len(out['objects']))
        self.assertFalse(rep['accepted']);self.assertTrue(all(not r['complete_path_credit'] for r in rep['results']))

    def test_all_foreign_obstacle_identities_retained(self):
        a=via('foreign-a',4,5,'SIG');b=via('foreign-b',4.1,5,'OTHER')
        src,pl,plan=fixture([a,b]);_,rep=fr.assess(src,pl,plan,'parallel-vias')
        r=rep['results'][0];self.assertEqual(r['status'],'REJECTED')
        self.assertEqual({w['object']['id'] for w in r['obstruction_witnesses']},{'foreign-a','foreign-b'})
        self.assertEqual(len([w for w in r['obstruction_witnesses'] if w['reason']=='copper']),12)

    def test_same_net_existing_drill_blocks(self):
        src,pl,plan=fixture([via('same-drill',4.2,5)]);_,rep=fr.assess(src,pl,plan,'parallel-vias')
        self.assertTrue(any(w['reason']=='drill' and w['object']['id']=='same-drill' for w in rep['results'][0]['obstruction_witnesses']))

    def test_sheet_ring_is_required_without_nearest_snap(self):
        src,pl,plan=fixture();pl['clipped_sheets']['AGND'][0]['polygon_mm']=[[0,0],[3.9,0],[3.9,10],[0,10]]
        _,rep=fr.assess(src,pl,plan,'parallel-vias')
        self.assertTrue(all('NO_FULL_RING_IN_SAME_NET_SHEET' in r['reasons'] for r in rep['results']))

    def test_fixed_geometry_change_stops(self):
        src,pl,plan=fixture();src['objects'][0]['center_mm']=[5.1,5]
        with self.assertRaisesRegex(ValueError,'fixed land identity'):fr.assess(src,pl,plan,'combined')

    def test_face_endpoint_contact_and_foreign_clearance(self):
        src,pl,plan=fixture([via('target',5,8)])
        plan['targets'][0]['face_target']={'object_id':'target','center_mm':[5,8]}
        plan['targets'][0]['intentional_face_drill_ids']=['v','target']
        out,rep=fr.assess(src,pl,plan,'wider-face');self.assertEqual(rep['added_count'],1)
        self.assertEqual({w['object_id'] for w in rep['results'][0]['contact_witnesses']},{'p','target'})
        self.assertTrue(all(w['positive_area_mm2']>0 for w in rep['results'][0]['contact_witnesses']))
        self.assertEqual(out['objects'][-1]['width_mm'],1.)
        self.assertEqual({w['object']['id'] for w in rep['results'][0]['intentional_drill_contact_witnesses']},{'v','target'})
        plan['targets'][0]['intentional_face_drill_ids']=[]
        _,blocked=fr.assess(src,pl,plan,'wider-face');self.assertEqual(blocked['added_count'],0)

    def test_compact_sheet_witness_binds_complete_record_and_local_geometry(self):
        src,pl,plan=fixture();_,rep=fr.assess(src,pl,plan,'parallel-vias')
        witness=rep['results'][0]['ring_support_sheets'][0]
        full=pl['clipped_sheets']['AGND'][0]
        expected=hashlib.sha256(json.dumps(full,sort_keys=True,separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(witness['sheet_id'],full['id']);self.assertEqual(witness['canonical_record_sha256'],expected)
        self.assertNotIn('polygon_mm',witness);self.assertNotIn('holes_mm',witness)
        local=shapely.from_wkb(witness['local_sheet_wkb']);window=shapely.from_wkb(witness['window_wkb'])
        self.assertEqual(local.area,16.);self.assertTrue(window.covers(local))
        self.assertTrue(all('polygon_mm' not in r['sheet'] for r in rep['results'][0]['severance_guard_witnesses']))

    def test_streamed_json_and_upfront_seals_detect_plan_and_method_mutations(self):
        with tempfile.TemporaryDirectory() as folder:
            paths={name:Path(folder)/name for name in ('plan','method','source')}
            for name,path in paths.items():fr.write_json(path,{'name':name})
            seals={name:fr.sha(path) for name,path in paths.items()};fr.check_seals(paths,seals)
            for key in ('plan','method'):
                saved=paths[key].read_bytes();paths[key].write_text('changed')
                with self.assertRaisesRegex(ValueError,'predeclaration or method changed'):fr.check_seals(paths,seals)
                paths[key].write_bytes(saved)
            self.assertEqual(json.loads(paths['source'].read_text()),{'name':'source'})

    def test_source_gap_cannot_be_promoted_by_branch_lands(self):
        src,_,_=fixture();c={'external_boundary':{'no_physical_bridge':True,'abstract_parts':[{'ref':r,'footprint':'','in_bom':False} for r in ('CN301','XB301')]},'existing_main_wires':[{'id':'POWER-P-'+str(k),'terminal_refs':['A'+str(k),'B'+str(k)]} for k in range(6)],'existing_main_lands':[{'reference':p+str(k),'candidate_owner':owner} for k in range(6) for p,owner in [('A','P'),('B','KA')]]}
        dep=fr.source_dependency(c,src);self.assertEqual(dep['status'],'SOURCE_DEPENDENCY_NEGATIVE');self.assertEqual(len(dep['p_receiving_lands']),6)
        src['objects'].append(dict(id='raw',ref='CN301'))
        self.assertEqual(fr.source_dependency(c,src)['status'],'SOURCE_INTERFACE_CHANGED_REVIEW_REQUIRED')

if __name__=='__main__':unittest.main()
