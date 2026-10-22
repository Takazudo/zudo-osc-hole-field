import collections
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import osc_synthetic_zone as q
import osc_synthetic_check as c

class Synthetic(unittest.TestCase):
    def test_fixture_small_and_duplicate_preserved(self):
        data=q.fixture();self.assertLess(len(data),10000)
        tracks=q.source_tracks(data);self.assertEqual(sum(tracks.values()),2)
        self.assertEqual(len({x[0] for x in tracks}),1)
        self.assertEqual(len(tracks),2)
        self.assertNotEqual(tracks,collections.Counter([next(iter(tracks))]))
    def test_fixture_is_not_product(self):
        data=q.fixture().decode()
        self.assertNotIn('U1105',data);self.assertNotIn('265b1369',data)
        self.assertEqual(len(q.nodes(q.parse(data.encode()),'zone')),5)
    def test_missing_or_ambiguous_target(self):
        with self.assertRaises(ValueError):q.select(SimpleNamespace(Zones=lambda:[]))
        z=SimpleNamespace(m_Uuid=SimpleNamespace(AsString=lambda:q.uid('target')))
        with self.assertRaises(ValueError):q.select(SimpleNamespace(Zones=lambda:[z,z]))
    def test_nonselected_change_rejected(self):
        a=q.fixture();b=a.replace(b'(xy 28 10)',b'(xy 27 10)')
        self.assertNotEqual(q.zones_serialized(a),q.zones_serialized(b))
        self.assertNotEqual(q.persistent(a),q.persistent(b))
    def test_track_change_rejected(self):
        a=q.fixture();b=a.replace(b'(width 0.25)',b'(width 0.35)',1)
        self.assertNotEqual(q.persistent(a),q.persistent(b))
        self.assertNotEqual(q.source_tracks(a),q.source_tracks(b))
    def test_pad_change_rejected(self):
        a=q.fixture();b=a.replace(b'(drill 0.8)',b'(drill 0.9)',1)
        self.assertNotEqual(q.persistent(a),q.persistent(b))
    def test_parse_fails_closed(self):
        for x in (b'',b')',b'(kicad_pcb',b'(other)',b'(kicad_pcb)(kicad_pcb)'):
            with self.assertRaises(ValueError):q.parse(x)
    def test_deadline_refusal(self):
        with patch.object(c.c,'DEADLINE',100),patch.object(c.time,'monotonic',return_value=80):
            self.assertEqual(c.remaining(19),20)
            with self.assertRaises(TimeoutError):c.remaining(21)
    def test_partial_receipt(self):
        self.assertEqual(c.parse_output('noise\n'+json.dumps({'events':[],'status':'FAILED'}))['status'],'FAILED')
        with self.assertRaises(ValueError):c.parse_output('no result')
    def observation(self,layer='In4.Cu',v=0):
        return {'flashing':[{'uuid':'p','net':'+12V','position':[1,2],'layers':[[layer,v]]}],'fills':[]}
    def test_selected_flash_change(self):
        a=self.observation();b=self.observation(v=1)
        self.assertEqual(len(q.qualify_flashing(a,b,b)),1)
    def test_collateral_flash_rejected(self):
        with self.assertRaises(ValueError):q.qualify_flashing(self.observation('B.Cu'),self.observation('B.Cu',1),self.observation('B.Cu',1))
    def test_reload_flash_change_rejected(self):
        with self.assertRaises(ValueError):q.qualify_flashing(self.observation(),self.observation(v=1),self.observation())
    def test_reload_nonselected_fill_rejected(self):
        a=self.observation();b=self.observation();b['fills']=[{'uuid':'sentinel','filled':True}]
        with self.assertRaises(ValueError):q.qualify_flashing(a,a,b)
    def test_workflow(self):
        w=json.loads((Path(__file__).resolve().parents[2]/'.github/workflows/osc-candidate-check.yml').read_text())
        self.assertEqual(w['permissions'],{'contents':'read'})
        self.assertIn('synthetic',w['on']['workflow_dispatch']['inputs']['mode']['options'])
        job=next(iter(w['jobs'].values()))
        self.assertEqual(len(w['jobs']),1)
        self.assertIn('osc_synthetic_check.py frozen synthetic-receipts',job['steps'][4]['run'])
        self.assertIn('test_osc_synthetic.py',job['steps'][1]['with']['sparse-checkout'])
        self.assertIn('upload-safe/synthetic.json',job['steps'][-1]['with']['path'])
        self.assertEqual(c.TOTAL,120)
        self.assertEqual(job['steps'][4]['timeout-minutes'],"${{ inputs.mode == 'synthetic' && 2 || 10 }}")

if __name__=='__main__':unittest.main()
