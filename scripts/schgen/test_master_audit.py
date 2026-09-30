"""Fault injection for physical package unit completeness."""
import unittest
from scripts.schgen.audit_master import unit_coverage_error,coverage_errors,active_unit_termination_error
from scripts.schgen.core import LibrarySymbol,Pin


class UnitCoverage(unittest.TestCase):
    def test_missing_and_duplicate_panel_uids_are_listed(self):
        placements={f'J:T.{i}':{} for i in range(438)}
        bound={k:['J1'] for k in placements}
        self.assertEqual(coverage_errors(bound,placements,438),[])
        del bound['J:T.17']
        bound['J:T.18'].append('J2')
        faults=coverage_errors(bound,placements,438)
        self.assertTrue(any('J:T.17' in x for x in faults),faults)
        self.assertTrue(any('J:T.18' in x for x in faults),faults)

    def test_rejects_all_nc_active_unit(self):
        self.assertIn('all-NC active units',active_unit_termination_error('U100',
                      [{'unit':2,'pins':{'5':None,'6':None,'7':None}}]))
        self.assertIsNone(active_unit_termination_error('U100',
                          [{'unit':2,'pins':{'5':'AGND','6':'+5V','7':None}}]))

    def test_rejects_single_represented_unit_of_dual_package(self):
        pin=Pin('1',0,0,0,'input')
        lib={'Example:Dual':LibrarySymbol('Example:Dual','',{1:(pin,),2:(pin,)})}
        represented=[('TEST','U.1',1,'Example:Dual')]
        self.assertIn('expected [1, 2]',unit_coverage_error('U100',represented,lib))
        self.assertIsNone(unit_coverage_error('U100',represented+[('TEST','U.2',2,'Example:Dual')],lib))

if __name__=='__main__':unittest.main()
