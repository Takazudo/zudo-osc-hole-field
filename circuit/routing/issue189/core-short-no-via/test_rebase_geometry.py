"""Check the future rebase guard against an actual native replay and mutations."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('rebase_guard',HERE/'rebase_proposal.py')
guard=importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class RebaseGeometryTests(unittest.TestCase):
    def setUp(self):
        self.proposal=json.loads((ROOT/'circuit/routing/issue189/jl-u2204-endpoints/proposal.json').read_text())['copper']
        self.replay=json.loads((ROOT/'boards/osc-jack-left/reports/grid-routing/shards-issue189-u2204-endpoints-copper.json').read_text())['added']

    def test_real_native_geometry(self):
        self.assertEqual(len(self.replay),53)
        guard.require_known_geometry(self.replay,self.proposal)

    def test_same_uuid_width_changed(self):
        row=next(r for r in self.proposal if r['kind']=='segment');row['width_nm']+=1
        with self.assertRaises(AssertionError):guard.require_known_geometry(self.replay,self.proposal)

    def test_same_uuid_coordinate_changed(self):
        row=next(r for r in self.proposal if r['kind']=='segment');row['start_nm'][0]+=1
        with self.assertRaises(AssertionError):guard.require_known_geometry(self.replay,self.proposal)

    def test_same_uuid_net_changed(self):
        self.proposal[0]['net']='UNEXPECTED_NET'
        with self.assertRaises(AssertionError):guard.require_known_geometry(self.replay,self.proposal)

if __name__=='__main__':unittest.main()
