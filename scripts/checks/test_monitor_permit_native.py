import copy
import json
import unittest
from unittest.mock import Mock, patch

from scripts.checks.monitor_permit_native import ERC, NETLIST, inspect
from scripts.schgen import generate_monitor_permit as generator


class MonitorPermitNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.erc = json.loads(ERC.read_text())
        cls.netlist = NETLIST.read_text()

    def test_all_physical_candidate_pins_and_identities_match(self):
        result = inspect(self.erc,self.netlist)
        self.assertEqual(result['physical_candidate_components'],42)
        self.assertEqual(result['checked_physical_and_test_pins'],113)
        self.assertEqual(result['erc_errors'],0)
        self.assertIn('Nonphysical',result['test_source_export_scope'])

    def test_unrelated_incomplete_or_suppressed_erc_is_rejected(self):
        changed=copy.deepcopy(self.erc);changed['source']='another.kicad_sch'
        with self.assertRaisesRegex(ValueError,'source differs'): inspect(changed,self.netlist)
        changed=copy.deepcopy(self.erc);changed['sheets'].pop()
        with self.assertRaisesRegex(ValueError,'coverage incomplete'): inspect(changed,self.netlist)
        changed=copy.deepcopy(self.erc);changed['ignored_checks'].append({'key':'pin_not_connected'})
        with self.assertRaisesRegex(ValueError,'suppression'): inspect(changed,self.netlist)

    def test_native_violation_cannot_keep_success(self):
        changed=copy.deepcopy(self.erc)
        changed['sheets'][1]['violations'].append({'severity':'warning','type':'endpoint_off_grid'})
        with self.assertRaisesRegex(ValueError,'violations remain'): inspect(changed,self.netlist)

    def test_stale_value_and_pin_connectivity_rejected(self):
        changed=self.netlist.replace('(value "10000 ohm")','(value "20000 ohm")',1)
        self.assertNotEqual(changed,self.netlist)
        with self.assertRaisesRegex(ValueError,'value/footprint/MPN'): inspect(self.erc,changed)
        changed=self.netlist.replace('(name "/MONITOR/SENSE")','(name "/MONITOR/WRONG_SENSE")',1)
        self.assertNotEqual(changed,self.netlist)
        with self.assertRaisesRegex(ValueError,'pin mismatch'): inspect(self.erc,changed)

    def test_missing_package_pin_and_qualification_promotion_rejected(self):
        spec=json.loads(generator.SPEC.read_text());del spec['components'][0]['pins']['3']
        with patch.object(generator,'SPEC',Mock(read_text=lambda:json.dumps(spec))):
            with self.assertRaisesRegex(ValueError,'incomplete physical pin'): generator.specification()
        spec=json.loads(generator.SPEC.read_text());spec['qualification_accepted']=True
        with patch.object(generator,'SPEC',Mock(read_text=lambda:json.dumps(spec))):
            with self.assertRaisesRegex(ValueError,'cannot admit'): generator.specification()

    def test_value_cannot_disagree_with_exact_resistor_identity(self):
        spec=json.loads(generator.SPEC.read_text())
        next(p for p in spec['components'] if p['ref']=='R114')['value']=15000
        with patch.object(generator,'SPEC',Mock(read_text=lambda:json.dumps(spec))):
            with self.assertRaisesRegex(ValueError,'exact MPN'): generator.specification()

    def test_capacitance_cannot_disagree_with_exact_identity(self):
        spec=json.loads(generator.SPEC.read_text())
        next(p for p in spec['components'] if p['ref']=='C101')['value']=2e-7
        with patch.object(generator,'SPEC',Mock(read_text=lambda:json.dumps(spec))):
            with self.assertRaisesRegex(ValueError,'capacitance differs'): generator.specification()

    def test_native_inputs_cover_consumed_existing_owner_mapping(self):
        from scripts.checks.monitor_permit_native import inputs
        paths=inputs()
        self.assertIn('.claude/skills/component-nexperia-mmbt3904-215/pin-map.json',paths)
        self.assertIn('.claude/skills/component-passives-family/manifest.json',paths)


if __name__=='__main__':
    unittest.main()
