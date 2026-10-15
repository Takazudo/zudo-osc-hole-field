import copy
import json
import unittest
import stage4_power_inventory as p

class PowerInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((p.OUT/'stage4/power-inventory-report.json').read_text())
        cls.ledger=json.loads((p.ROOT/'design/architecture-278/source-ledger.json').read_text())
        cls.source=p.source_inventory(cls.ledger)
        cls.assembly=json.loads((p.OUT/'assembly-report.json').read_text())
        cls.best=json.loads((p.OUT/'direct-study-report.json').read_text())['best_by_variant']['baseline']
        cls.ctx=p.audit.context()
    def test_full_source_conservation(self):
        r=self.report
        self.assertEqual((5904,8226,20419,939),tuple(r[k] for k in ('retained_package_count','retained_unit_count','retained_pin_count','retained_NC_pin_count')))
        self.assertEqual(set(self.source),set(r['retained_packages']))
        for ref,record in r['retained_packages'].items():
            self.assertEqual(self.source[ref]['pins'],record['pins']);self.assertEqual(self.source[ref]['units'],record['units'])
            self.assertEqual({pin:u['unit'] for u in self.source[ref]['unit_records'] for pin in u['pins']},record['pin_to_unit'])
    def test_all_variants_rebind(self):
        for v in self.report['variants'].values():
            self.assertEqual((1125,1472,4779),(v['placed_package_count'],v['placed_unit_count'],v['unplaced_package_count']))
            p.validate_supply_inventory(v,self.source)
            self.assertEqual((225,240,9),(len(v['crossing_endpoint_bindings']),len(v['return_group_bindings']),len(v['shared_aggregate_capacitance'])))
            self.assertTrue(all(x is None for x in v['POWER_package_geometry'].values()))
    def test_shared_translation_moves_only_shared(self):
        a=self.report['variants']['baseline']['placed_packages'];b=self.report['variants']['baseline_shared_x6']['placed_packages']
        for ref,record in a.items():
            for pin,points in record['pads_xyz_mm'].items():
                expected=[[x+(6 if record['instance']=='OCTAVE_REF' else 0),y,z] for x,y,z in points]
                self.assertEqual(expected,b[ref]['pads_xyz_mm'][pin])
    def test_no_stale_rear_coordinates(self):
        v=self.report['variants']['baseline']
        p.validate_coordinates(v['placed_packages'],self.best,self.assembly,self.source,self.ctx,(0,0))
        points=copy.deepcopy(v['placed_packages']);points['U1105']['pads_xyz_mm']['16'][0][0]-=1
        with self.assertRaises(ValueError):p.validate_coordinates(points,self.best,self.assembly,self.source,self.ctx,(0,0))
    def test_missing_supply_and_return_rejected(self):
        for net in ('+12V','AGND'):
            v=copy.deepcopy(self.report['variants']['baseline']);v['supplies'][net]['physical_endpoints'].pop()
            with self.assertRaises(ValueError):p.validate_supply_inventory(v,self.source)
    def test_unknown_power_not_promoted(self):
        v=copy.deepcopy(self.report['variants']['baseline']);v['POWER_package_geometry'][next(iter(v['POWER_package_geometry']))]=[0,0,69.2]
        with self.assertRaises(ValueError):p.validate_supply_inventory(v,self.source)
    def test_unit_omission_rejected(self):
        ledger=copy.deepcopy(self.ledger);ledger['package_units'].pop()
        with self.assertRaises(ValueError):p.source_inventory(ledger)
    def test_crossing_duplicate_cannot_hide_omission(self):
        best=copy.deepcopy(self.best);best['paths'][-1]=copy.deepcopy(best['paths'][0])
        with self.assertRaises(ValueError):p.coverage(best,self.report['variants']['baseline']['placed_packages'],self.source,self.ctx,self.assembly)
    def test_return_endpoint_omission_rejected(self):
        best=copy.deepcopy(self.best);row=next(r for r in best['returns'] if r['endpoint_ids']);row['endpoint_ids'].pop()
        with self.assertRaises(ValueError):p.coverage(best,self.report['variants']['baseline']['placed_packages'],self.source,self.ctx,self.assembly)
    def test_return_group_duplicate_cannot_hide_omission(self):
        best=copy.deepcopy(self.best);best['returns'][-1]=copy.deepcopy(best['returns'][0])
        with self.assertRaises(ValueError):p.coverage(best,self.report['variants']['baseline']['placed_packages'],self.source,self.ctx,self.assembly)
    def test_wrong_actual_alias_rejected(self):
        best=copy.deepcopy(self.best);best['paths'][0]['actual_identity']['front']['ref']='U1105'
        with self.assertRaises(ValueError):p.coverage(best,self.report['variants']['baseline']['placed_packages'],self.source,self.ctx,self.assembly)
    def test_bypass_associations_complete(self):
        expected={(ref,r['decouples_ref']) for ref,r in self.source.items() if r['decouples_ref']}
        expected|={(r['capacitor'],r['package']) for r in self.assembly['bypass_associations'] if r['owner']=='shared-reference'}
        for v in self.report['variants'].values():self.assertEqual(expected,{(r['capacitor'],r['target']) for r in v['bypass_associations']})
    def test_unknown_routing_stays_unknown(self):
        for v in self.report['variants'].values():
            self.assertFalse(v['accepted'])
            for graph in v['supplies'].values():
                self.assertIsNone(graph['routed_edges']);self.assertIsNone(graph['parallel_current_solution']);self.assertIsNone(graph['common_distribution_resistance_mOhm'])

if __name__=='__main__':unittest.main()
