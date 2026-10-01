"""Exact 5.6k/100k values and unspecified identities remain distinct."""
import unittest
from scripts.pcbgen.netlist import Component
from scripts.pcbgen.resistor_return_caps import derive


class ResistorReturnCapsTests(unittest.TestCase):
    def test_exact_values_drive_conditions_without_mpn_inheritance(self):
        components=[Component('Rsmall','5600 Ω','','','','',(('MPN',''),)),
                    Component('Rbig','100000 Ω','','','','',(('MPN','RC0603FR-07100KL'),))]
        ledger={'pads':[{'ref':ref,'pad':'2','symbol':'RC0603FR-07100KL','category':'passive_or_other_return','possible_normal_return_basis':True}
                        for ref in ('Rsmall','Rbig')],'normal_transfer_envelope':{'aggregate_absolute_current_A':4.6}}
        nets={(ref,pad):('AGND' if pad=='2' else 'signal') for ref in ('Rsmall','Rbig') for pad in ('1','2')}
        result,caps=derive(ledger,components,nets,75,.9)
        self.assertAlmostEqual(caps['conditional_resistor_5600ohm'],75/5040)
        self.assertAlmostEqual(caps['conditional_resistor_100000ohm'],75/90000)
        contacts=result['normal_transfer_envelope']['conditional_resistor_class']['contacts']
        self.assertEqual(contacts[0]['source_MPN'],'')
        self.assertEqual(contacts[1]['source_MPN'],'RC0603FR-07100KL')
        self.assertEqual(contacts[0]['conditional_resistive_current_maximum_A'],contacts[0]['separate_unselected_total_terminal_current_requirement_A'])
        self.assertIn('SEPARATE',result['normal_transfer_envelope']['conditional_resistor_class']['total_terminal_current_condition'])
        self.assertEqual(ledger['pads'][0]['category'],'passive_or_other_return')
        self.assertEqual(result['normal_transfer_envelope']['aggregate_absolute_current_A'],4.6)
        nets['Rsmall','2']='wrong'
        with self.assertRaisesRegex(ValueError,'exact ground'):derive(ledger,components,nets,75,.9)


if __name__=='__main__':unittest.main()
