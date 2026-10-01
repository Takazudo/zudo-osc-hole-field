"""Reject direct-source loading, overfanout and weakened trim topology."""
from dataclasses import replace
import unittest
import json,tempfile
from pathlib import Path
from unittest.mock import patch
from design.spec.modules.oscillator import family
from design.spec.modules.check_oscillator_reference import build

class ReferenceFanout(unittest.TestCase):
    def test_rejects_bias_bound_below_exact_pw_package_fact(self):
        import design.spec.modules.check_oscillator_reference as check
        config=json.loads(check.CONFIG.read_text());config['input_bias_bound_A']=5e-9
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'reference.json';path.write_text(json.dumps(config))
            with patch.object(check,'CONFIG',path),self.assertRaisesRegex(AssertionError,'exact-package maximum'):
                check.build()

    def test_powered_bounds_and_complete_packages(self):
        r=build()
        self.assertEqual(len(r['local_outputs_per_oscillator']),6)
        self.assertEqual(len(r['precision_package_supply_and_bypass']),20)
        self.assertTrue(r['rail_planning_check'])
        self.assertGreater(r['minimum_driver_rail_headroom_V'],6)

    def test_old_direct_source_fixture_rejected(self):
        f=family()
        def old(p):
            pins={k:('OSC_REFN5' if v and v.endswith('REFN5') else 'OSC_REF5' if v and v.endswith('REF5') else v) for k,v in p.pins.items()}
            return replace(p,pins=pins)
        with self.assertRaisesRegex(AssertionError,'missing local fanout'):
            build(replace(f,parts=tuple(old(p) for p in f.parts if not any(p.key.startswith(x) for x in ('R_LOCAL_REF','C_LOCAL_REF','R_BASE_REF','C_BASE_REF','R_SINE_REF','C_SINE_REF')))))

    def test_extra_raw_trim_is_rejected(self):
        f=family();trim=next(p for p in f.parts if p.key=='BASE_TRIM.0')
        extra=replace(trim,key='UNBOUNDED.0',pins={**trim.pins,'1':'OSC_REFN5','3':'OSC_REF5'})
        with self.assertRaisesRegex(AssertionError,'raw source loaded'):
            build(replace(f,parts=(*f.parts,extra)))

    def test_seven_panel_pots_rejected(self):
        f=family();pot=next(p for p in f.parts if p.attributes.get('PanelUid')=='C:${SHEETNAME}.TUNE')
        extra=tuple(replace(pot,key=f'EXTRA{i}.0') for i in range(4))
        with self.assertRaisesRegex(AssertionError,'panel fanout exceeded'):
            build(replace(f,parts=(*f.parts,*extra)))

    def test_double_trim_pair_rejected(self):
        f=family();trim=next(p for p in f.parts if p.key=='BASE_TRIM.0')
        with self.assertRaisesRegex(AssertionError,'overload'):
            build(replace(f,parts=(*f.parts,replace(trim,key='EXTRA_TRIM.0'))))
if __name__=='__main__':unittest.main()
