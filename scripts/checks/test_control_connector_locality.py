import copy
import unittest
from scripts.checks.control_connector_locality import baseline_digest, reassign, prove_partition_transition


def fixture():
    headers=[];apertures=[]
    for n in (1,2):
        for board in ('K','P'):
            headers.append({'id':f'K-P-{n}-{board}','board':board,
                'header_mpn':'BM03B-GHS-TBT(LF)(SN)','housing_mpn':'GHR-03V-S',
                'contact_mpn':'SSHL-002T-P0.2','contacts':3,
                'pin_map':{'1':f'/SIGNAL{n}','2':'AGND','3':f'/RETURN{n}'},
                'center_mm':[10*n,20],'footprint_origin_mm':[10*n,18.05],
                'rotation_deg':0,'kicad_orientation_deg':0,
                'side':'F.Cu' if board=='K' else 'B.Cu',
                'land_courtyard_mm':[10*n-3,17,10*n+3,23],
                'native_cached_courtyard_envelope_mm':[10*n-3.05,16.95,10*n+3.05,23.05]})
        apertures.append({'header_id':f'K-P-{n}-K','center_mm':[10*n+4,20],'diameter_mm':2.2})
    headers.append({**copy.deepcopy(headers[-1]),'id':'JL-P-1-P','pin_map':{'1':'/UTILITY','2':'AGND','3':'NC'}})
    proposal={'schema_version':1,'expected_pair_count':2,'baseline_headers_sha256':baseline_digest(headers),
              'destination_pair_site':{'K-P-1':'K-P-2','K-P-2':'K-P-1'}}
    return headers,apertures,proposal


class PairAssignmentTests(unittest.TestCase):
    def test_both_ends_and_service_access_move_without_pin_or_utility_changes(self):
        headers,apertures,proposal=fixture();snapshot=copy.deepcopy((headers,apertures,proposal))
        hs,aps,report=reassign(headers,apertures,proposal)
        for board in ('K','P'):
            row=next(h for h in hs if h['id']=='K-P-1-'+board)
            self.assertEqual(row['center_mm'],[20,20]);self.assertEqual(row['pin_map']['1'],'/SIGNAL1')
        self.assertEqual(aps[0]['center_mm'],[24,20]);self.assertEqual(aps[0]['header_id'],'K-P-1-K')
        self.assertEqual(hs[-1],headers[-1]);self.assertEqual(report['moved_pairs'],2)
        self.assertEqual((headers,apertures,proposal),snapshot)

    def test_full_partition_comparison_rejects_unrelated_changes(self):
        hs,aps,p=fixture()
        before={'connectors':hs,'K_service_apertures':aps,'electrical_limit':0.5}
        nh,na,_=reassign(hs,aps,p)
        after={'connectors':nh,'K_service_apertures':na,'electrical_limit':0.5}
        prove_partition_transition(before,after,p)
        for mode in ('limit','pin','other_header'):
            bad=copy.deepcopy(after)
            if mode=='limit':bad['electrical_limit']=0.6
            if mode=='pin':bad['connectors'][0]['pin_map']['1']='invented'
            if mode=='other_header':bad['connectors'][-1]['center_mm'][0]+=1
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'beyond'):
                prove_partition_transition(before,bad,p)

    def test_incomplete_duplicate_or_foreign_pair_assignment_rejected(self):
        for mapping in ({'K-P-1':'K-P-2'},{'K-P-1':'K-P-2','K-P-2':'K-P-2'},
                        {'K-P-1':'K-P-3','K-P-2':'K-P-1'}):
            hs,aps,p=fixture();p['destination_pair_site']=mapping
            with self.subTest(mapping=mapping),self.assertRaises(ValueError):reassign(hs,aps,p)

    def test_stale_geometry_missing_pair_and_missing_access_rejected(self):
        for mode in ('stale','missing_pair','missing_access','duplicate_access'):
            hs,aps,p=fixture()
            if mode=='stale':hs[0]['center_mm'][0]+=1
            if mode=='missing_pair':hs.pop(0);p['baseline_headers_sha256']=baseline_digest(hs)
            if mode=='missing_access':aps.pop()
            if mode=='duplicate_access':aps.append(copy.deepcopy(aps[0]))
            with self.subTest(mode=mode),self.assertRaises(ValueError):reassign(hs,aps,p)

    def test_wrong_exact_part_or_ground_pin_rejected_even_with_new_digest(self):
        for mode in ('part','ground'):
            hs,aps,p=fixture()
            if mode=='part':hs[0]['header_mpn']='different'
            else:hs[0]['pin_map']['2']='/SIGNAL'
            p['baseline_headers_sha256']=baseline_digest(hs)
            with self.subTest(mode=mode),self.assertRaises(ValueError):reassign(hs,aps,p)


if __name__=='__main__':unittest.main()
