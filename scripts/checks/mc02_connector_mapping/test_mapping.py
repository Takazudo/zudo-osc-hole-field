import copy
import json
from pathlib import Path
import tempfile
import unittest

import mapping as m


def link(direction='+y'):
    return {'id':'fixture','front_board':'P','direction':direction,'circuits':2,'connector':'fixtureFH12',
            'cable':'fixture','positions':[{'pos':1,'kind':'signal','net':'N'},{'pos':2,'kind':'ground'}],
            'geometry':{'front_connector':[0,0,2,1],'K_connector':[0,3,2,4]}}


class MappingTests(unittest.TestCase):
    def test_logical_position_never_becomes_physical_pad(self):
        rows=m.endpoint_rows(link())
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['logical_position_1']['net'],'N')
        for row in rows:
            for field in ('physical_reference','footprint_rotation_deg','pad1_local_mm','pad1_panel_mm','numbered_pad_coordinates'):
                self.assertIsNone(row[field])
            self.assertEqual(row['physical_mapping_status'],'NOT_ESTABLISHED')
            self.assertEqual(row['board_face'],'B')

    def test_each_direction_preserves_distinct_endpoint_sense(self):
        for name,direction in m.DIRECTIONS.items():
            front,back=m.endpoint_rows(link(name))
            self.assertEqual(front['direction_from_field_toward_slot'],list(direction))
            self.assertEqual(back['direction_from_field_toward_slot'],[-v for v in direction])
            self.assertEqual(front['field_center_panel_mm'],[1,.5])

    def test_duplicate_or_missing_logical_position(self):
        record=link();record['positions'][1]['pos']=1
        with self.assertRaises(ValueError):m.endpoint_rows(record)

    def test_invalid_rectangle_rejected(self):
        for rect in ([0,0,0,1],[0,0,float('nan'),1]):
            record=link();record['geometry']['front_connector']=rect
            with self.assertRaises(ValueError):m.endpoint_rows(record)

    def test_named_physical_source_is_not_silently_virtual(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'board').write_text('(footprint "FH12-8S")\n')
            self.assertEqual(m.scan_board_names(root,{'K':'board'})[0]['line'],1)
            (root/'board').write_text('(footprint "other")\n')
            self.assertEqual(m.scan_board_names(root,{'K':'board'}),[])

    def test_stale_pin_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'board').write_text('different')
            with self.assertRaises(ValueError):m.verify_pins(root,{'sha256':{'board':'0'*64}})

    def test_actual61_virtual_geometry_reproduces_and_tamper_rejected(self):
        import sys
        sys.path.insert(0,str(m.ROOT/'scripts/stack/geometry'))
        import links_gate as kernel
        gate,gopts,opts=[json.loads((m.ROOT/p).read_text()) for p in (m.GATE,m.GOPTS,m.OPTS)]
        rows=m.build(gate,gopts,opts,kernel)
        self.assertEqual(len(rows),122)
        self.assertEqual(len({r['endpoint_id'] for r in rows}),122)
        self.assertTrue(all(r['pad1_panel_mm'] is None for r in rows))
        altered=copy.deepcopy(gate)
        row=next(r for r in altered['links'] if not r.get('gone'))
        row['geometry']['front_connector'][0]+=.1
        with self.assertRaisesRegex(ValueError,'geometry does not reproduce'):m.build(altered,gopts,opts,kernel)


if __name__=='__main__':unittest.main()
