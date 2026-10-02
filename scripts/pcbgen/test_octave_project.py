import copy
import json
import subprocess
import unittest
from pathlib import Path
from scripts.pcbgen.octave_project import TEMPLATE,BASE_COMMIT,BASE_PATH,verify_project

class OctaveProjectTests(unittest.TestCase):
    def test_retained_native_base_is_exact(self):
        self.assertEqual(TEMPLATE.read_bytes(),subprocess.check_output(['git','show',BASE_COMMIT+':'+BASE_PATH]))
    def test_actual_configuration_and_rule_mutations(self):
        original=json.loads(Path('boards/osc-octave-1/osc-octave-1.kicad_pro').read_bytes())
        routing=json.loads(Path('design/partition/octave-routing.json').read_bytes())
        verify_project(original,TEMPLATE.read_bytes(),routing)
        for case in ('ignored-short','clearance','exclusion','assignment','pattern','extra-class'):
            changed=copy.deepcopy(original)
            if case=='ignored-short':changed['board']['design_settings']['rule_severities']['shorting_items']='ignore'
            elif case=='clearance':changed['board']['design_settings']['rules']['min_copper_edge_clearance']=.1
            elif case=='exclusion':changed['board']['design_settings']['drc_exclusions']=['invented']
            elif case=='assignment':changed['net_settings']['netclass_assignments']={'AGND':'Default'}
            elif case=='pattern':changed['net_settings']['netclass_patterns'].append({'netclass':'Default','pattern':'*'})
            else:changed['net_settings']['classes'].append({**changed['net_settings']['classes'][0],'name':'Override'})
            with self.subTest(case=case),self.assertRaisesRegex(ValueError,'complete adapter'):
                verify_project(changed,TEMPLATE.read_bytes(),routing)

if __name__=='__main__':unittest.main()
