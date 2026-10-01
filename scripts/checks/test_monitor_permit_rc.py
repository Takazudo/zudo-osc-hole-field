import tempfile
import math
from unittest.mock import patch
import unittest
from pathlib import Path
from scripts.checks import monitor_permit_rc as model


class MonitorRCInputTests(unittest.TestCase):
    def test_source_capacitance_and_case_initial_conditions(self):
        parameters,_=model.source_parameters()
        self.assertAlmostEqual(parameters['cap'],1e-8)
        self.assertAlmostEqual(parameters['pin_cap'],1e-11)
        for case in model.cases(parameters):
            deck=model.deck(case,parameters,model.STEPS[0])
            self.assertIn(' uic\n',deck)
            self.assertIn('.ic v(delay_cap)=',deck)
            if case['mode']=='forced_clamp':
                self.assertNotIn('Cpin ',deck)
                self.assertIn('Vclamp delay_in 0 0',deck)

    def test_reject_malformed_waveform(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'wave.dat'
            path.write_text('time v(delay_cap) v(delay_in) i(vdrive)\n'+''.join('0 5 5 0\n' for _ in range(12)))
            with self.assertRaisesRegex(ValueError,'strictly increasing'):model.read_waveform(path,4)
            path.write_text('time wrong v(delay_in) i(vdrive)\n')
            with self.assertRaisesRegex(ValueError,'header'):model.read_waveform(path,4)

    def test_zero_waveform_cannot_stand_in_for_charged_run(self):
        p,_=model.source_parameters()
        case=next(c for c in model.cases(p) if c['name']=='forced_zero_endpoints')
        rows=[(i*model.STEPS[0],0,0,0,0) for i in range(2001)]
        with self.assertRaisesRegex(ValueError,'initial condition'):model.inspect(case,p,rows,model.STEPS[0])

    def test_coarse_samples_cannot_be_labeled_fine(self):
        p,_=model.source_parameters()
        case=next(c for c in model.cases(p) if c['name']=='forced_zero_endpoints')
        rows=[]
        for i in range(1001):
            time=i*1e-6;voltage=5*math.exp(-time/5e-5)
            rows.append((time,voltage,0,voltage/10000,voltage/10000))
        with self.assertRaisesRegex(ValueError,'maximum timestep'):
            model.inspect(case,p,rows,model.STEPS[1])

    def test_frozen_sources_cannot_bind_to_later_bytes(self):
        snapshot=model.snapshot_sources()
        original=Path.read_bytes
        def changed(path):
            return b'{}' if path==model.SPEC else original(path)
        with patch.object(Path,'read_bytes',changed):
            p,_=model.source_parameters(snapshot)
            self.assertAlmostEqual(p['cap'],1e-8)
            with self.assertRaisesRegex(ValueError,'source changed'):model.verify_unchanged(snapshot)

    def test_summed_current_cannot_hide_wrong_branch_labels(self):
        p,_=model.source_parameters()
        case=next(c for c in model.cases(p) if c['name']=='forced_zero_endpoints')
        rows=[]
        for i in range(2001):
            time=i*model.STEPS[0];voltage=5*math.exp(-time/5e-5)
            rows.append((time,voltage,0,2*voltage/10000,0))
        with self.assertRaisesRegex(ValueError,'Ohm law'):model.inspect(case,p,rows,model.STEPS[0])
