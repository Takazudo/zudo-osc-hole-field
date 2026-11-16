import unittest
from test_osc_topology import fixture, Item
import osc_frozen_topology as t

class MismatchInventory(unittest.TestCase):
    def test_resolves_pad_and_track_without_claiming_path(self):
        b,p,pads=fixture(); conn=b.GetConnectivity(); a='C1129.1'
        track=b.GetTracks()[0]
        conn.GetConnectedItems=lambda pad: [track,pads['U1105.16']] if pad is pads[a] else []
        r=t.observe(b,p);t.validate(r)
        rows=r['mismatch_member_inventory']['objects']
        self.assertEqual(rows[t.uid(track)]['kind'],'track_or_via')
        self.assertEqual(rows[t.uid(pads['U1105.16'])]['pad'],'U1105.16')
        self.assertFalse(r['board_acceptance'])
        self.assertTrue(all(not x['shared_layer'] for x in r['mismatch_member_inventory']['pad_member_shape_contacts']))
    def test_same_layer_native_shape_observation(self):
        b,p,pads=fixture();track=b.GetTracks()[0];track.layers=('F.Cu',)
        b.GetConnectivity().GetConnectedItems=lambda pad:[track]
        r=t.observe(b,p);t.validate(r)
        contacts=r['mismatch_member_inventory']['pad_member_shape_contacts']
        self.assertTrue(any(c['shape_intersection'] and c['shared_layer'] for c in contacts))
        contacts.pop()
        with self.assertRaises(ValueError):t.validate(r)
    def test_unknown_native_member_fails(self):
        b,p,_=fixture();b.GetConnectivity().GetConnectedItems=lambda pad:[Item('unknown','AGND')]
        with self.assertRaisesRegex(ValueError,'Unresolved'):t.observe(b,p)
    def test_duplicate_native_member_identity_fails(self):
        b,p,pads=fixture();track=b.GetTracks()[0];b.GetTracks=lambda:[track,track]
        members={n:[t.uid(track)] for pair in t.MISMATCH_PAIRS for n in pair}
        with self.assertRaisesRegex(ValueError,'Duplicate'):t.member_inventory(b,p,members)
    def test_growth_bound(self):
        b,p,_=fixture();b.GetConnectivity().GetConnectedItems=lambda pad:[Item(str(i),'AGND') for i in range(129)]
        with self.assertRaisesRegex(ValueError,'bound'):t.observe(b,p)
    def test_missing_inventory_fails(self):
        b,p,_=fixture();r=t.observe(b,p);r.pop('mismatch_member_inventory')
        with self.assertRaises(ValueError):t.validate(r)
    def test_missing_neighbor_evidence_fails(self):
        b,p,_=fixture();r=t.observe(b,p)
        r['mismatch_member_inventory'].pop('member_reported_neighbors')
        with self.assertRaises(ValueError):t.validate(r)
    def test_neighbor_growth_fails(self):
        b,p,pads=fixture();track=b.GetTracks()[0]
        b.GetConnectivity().GetConnectedItems=lambda item: [Item(str(i),'AGND') for i in range(129)] if item is track else [track]
        with self.assertRaisesRegex(ValueError,'neighbor bound'):t.observe(b,p)
    def test_shared_members_tampering_fails(self):
        b,p,_=fixture();r=t.observe(b,p);r['mismatch_member_inventory']['pairs'][0]['shared_members']=['invented']
        with self.assertRaises(ValueError):t.validate(r)

if __name__=='__main__':unittest.main()
