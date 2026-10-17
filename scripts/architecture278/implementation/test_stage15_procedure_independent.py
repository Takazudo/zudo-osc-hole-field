"""Independent source-only regressions; no actuator is adjusted or calibrated."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import stage15_procedure as m
import stage12_budget as circuit


class IndependentProcedure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=[json.loads(p.read_text()) for p in [m.ROOT/'design/standard/electrical-standard.json',m.ROOT/'design/architecture-278/implementation/stage15-completion/allocation-report.json',m.OUT/'owner-decision.json']]

    def test_independent_meter_error_must_remain_in_absolute_residual(self):
        target=2.;meter_offset=-.0012;actual_baseline=target-meter_offset;gain=1.00020001
        indicated_zero_input=actual_baseline+meter_offset
        self.assertAlmostEqual(indicated_zero_input,target)
        actual_output=actual_baseline+gain*5
        absolute=actual_output-(target+5)
        mathematically_zeroed=actual_output-actual_baseline-5
        self.assertGreater(absolute,.002)
        self.assertLess(mathematically_zeroed,.002)
        self.assertAlmostEqual(absolute-mathematically_zeroed,.0012)

    def test_offset_motion_changes_baseline_but_not_ideal_cv_slope(self):
        params={'kn':1.002,'ka':.998,'ga':1.0001,'gm':.9999,'gcv':1.0001,'gr':1.0001}
        baselines=[]
        for x in (0,.25,.5,.75,1):
            out=lambda cv:circuit.transfer(0,cv,.5,x,**params)['out_V']
            baselines.append(out(0))
            self.assertAlmostEqual((out(5)-out(-5))/10,params['gr']*params['gcv'],places=12)
        self.assertGreater(max(baselines)-min(baselines),9.9)
        self.assertNotAlmostEqual(baselines[2],0,places=3)

    def test_atten_motion_can_change_baseline_with_real_input_offsets(self):
        params={'errors':{'IN_buffer':.0001,'remote_buffer':.00005}}
        baseline=[circuit.transfer(0,0,a,.5,**params)['out_V'] for a in (0,.5,1)]
        self.assertGreater(max(baseline)-min(baseline),.0002)

    def test_approval_flags_cannot_be_promoted(self):
        for key in ('factory_protocol_approved','component_implementation_authorized','physical_execution_authorized'):
            args=copy.deepcopy(self.args);args[2][key]=True
            with self.assertRaises(ValueError):m.analyze(*args)

    def test_historical_mutable_review_hash_rejected(self):
        original=Path.read_text
        def modified(path,*args,**kwargs):
            raw=original(path,*args,**kwargs)
            if path==m.previous.OUT/'review-root.json':
                r=json.loads(raw);r['source_sha256']['scripts/architecture278/implementation/check_source.py']='0'*64
                return json.dumps(r)
            return raw
        with patch.object(m,'preserve',return_value=0),patch.object(Path,'read_text',modified):
            with self.assertRaisesRegex(ValueError,'historical review binding'):m.predecessor()

    def test_live_frozen_source_mutation_rejected(self):
        with patch.object(m.common,'digest',return_value='0'*64):
            with self.assertRaisesRegex(ValueError,'preserved'):m.preserve()


if __name__=='__main__':unittest.main()
