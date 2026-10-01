import tempfile
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
        rows=[(0,0,0,0,0),(.001,0,0,0,0)]
        with self.assertRaisesRegex(ValueError,'initial condition'):model.inspect(case,p,rows,model.STEPS[0])
