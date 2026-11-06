"""Regressions against the immutable, actually exported 10.0.6 XML (no native runs)."""
import copy
import hashlib
import unittest
from pathlib import Path
import stage18_observation as old
import stage20_observation as subject

XML = old.source.ROOT/'design/architecture-278/implementation/stage19/x0x-run-20261016/run/retained/netlist.xml'
RAW = XML.read_bytes()
OBSERVED = old.parse_xml(RAW.decode())
EXPECTED = subject.expected_from_source()


class RetainedObservationTests(unittest.TestCase):
    def test_retained_hash(self):
        self.assertEqual(hashlib.sha256(RAW).hexdigest(), '289f7771d87b81dafec5178dc42d1889a9671997c333dc42f51660f047ebc238')

    def test_complete_retained_export(self):
        result = subject.compare(OBSERVED, EXPECTED)
        self.assertEqual((result['references'], result['physical_pins'], result['unit_UUIDs'], result['native_net_nodes']), (118,561,154,561))
        self.assertEqual(len(result['explicit_singleton_NCs']),196)
        self.assertFalse(result['hardware_acceptance'])

    def test_historical_failure_retained(self):
        with self.assertRaisesRegex(ValueError, 'unit slot roster mismatch C7101'):
            old.compare(OBSERVED, old.expected_from_source())

    def test_original_unit_zero_metadata_retained(self):
        result = subject.compare(OBSERVED, EXPECTED)
        zeros = [ref for ref,units in result['unit_metadata'].items() if '0' in units]
        self.assertEqual(len(zeros),61)
        for ref in zeros:
            self.assertEqual(set(EXPECTED[ref]['units']), {'A'})

    def test_both_source_nc_representations(self):
        for representation in ('no_connect', 'no_connect+no_connect'):
            obs=copy.deepcopy(OBSERVED)
            for net in obs['nets'].values():
                for node in net['nodes']:
                    if node['ref']=='U7101' and node['pin'] in ('1','7','8'):
                        node['pintype']=representation
            subject.compare(obs, EXPECTED)

    def test_reversible_name_collision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'collision'):
            old.net_names(['a b', 'a{space}b'])

    def test_representative_property_not_other_unit(self):
        obs=copy.deepcopy(OBSERVED)
        obs['components']['U7106']['properties']['Role']=EXPECTED['U7106']['unit_metadata']['1']['properties']['Role']
        with self.assertRaisesRegex(ValueError, 'properties mismatch U7106'):
            subject.compare(obs,EXPECTED)

    def test_library_slots_reject_unsupported_shapes(self):
        for sub in (['symbol','Part_1_1',['unit_name','Custom']], ['symbol','Part_1_2']):
            with self.assertRaises(ValueError): subject.library_slots(['symbol','Part',sub])

    def test_correlated_fields_not_arbitrary_unit_mix(self):
        obs=copy.deepcopy(OBSERVED)
        obs['components']['U7106']['fields']['Role']='offset:RESTORE'
        obs['components']['U7106']['fields']['LogicalCellKey']='precision_output_J_A01_IN_OUT__A.1'
        with self.assertRaisesRegex(ValueError, 'aggregate fields mismatch U7106'):
            subject.compare(obs,EXPECTED)


def endpoint(obs, connected):
    for name,net in obs['nets'].items():
        for node in net['nodes']:
            if (EXPECTED[node['ref']]['pins'][node['pin']] is not None)==connected:
                return name,net,node
    raise AssertionError('fixture missing endpoint')


def mutate(obs, case):
    c=obs['components']['C7101']
    if case=='missing_reference': del obs['components']['C7101']
    elif case=='extra_reference': obs['components']['C9999']=copy.deepcopy(c)
    elif case=='missing_uuid': c['tstamps'].clear()
    elif case=='changed_uuid': c['tstamps'][0]='00000000-0000-0000-0000-000000000000'
    elif case=='duplicate_uuid': c['tstamps']*=2
    elif case=='missing_multiunit_uuid': obs['components']['U7102']['tstamps'].pop()
    elif case=='missing_unit': obs['components']['U7102']['units'].pop('A')
    elif case=='unit_zero_alias': c['units']['@']=c['units'].pop('A')
    elif case=='extra_unit': c['units']['B']=c['units']['A'][:]
    elif case=='missing_unit_pin': c['units']['A'].pop()
    elif case=='duplicate_unit_pin': c['units']['A']*=2
    elif case=='unit_pin_substitution': c['units']['A'][0]='999'
    elif case=='missing_property': del obs['components']['U7101']['properties']['ki_keywords']
    elif case=='changed_keywords': obs['components']['U7101']['properties']['ki_keywords']='substitute'
    elif case=='changed_filters': obs['components']['U7101']['properties']['ki_fp_filters']='substitute'
    elif case=='invented_property': c['properties']['ki_keywords']='invented'
    elif case=='field_substitution': c['fields']['Manufacturer']='substitute'
    elif case=='property_substitution': c['properties']['Manufacturer']='substitute'
    elif case=='changed_value': c['value']='substitute'
    elif case=='changed_footprint': c['footprint']='substitute'
    elif case=='changed_library': c['library']='substitute'
    elif case=='annotation_flag':
        annotation=next(x for x in obs['components'].values() if 'exclude_from_board' in x['properties'])
        del annotation['properties']['exclude_from_board']
    elif case=='missing_library_pin': next(iter(obs['libraries'].values())).pop()
    elif case in ('missing_endpoint','duplicate_endpoint','changed_pin','rewire','changed_connected_type','connected_nc_type'):
        name,net,node=endpoint(obs,True)
        if case=='missing_endpoint': net['nodes'].remove(node)
        elif case=='duplicate_endpoint': net['nodes'].append(copy.deepcopy(node))
        elif case=='changed_pin': node['pin']='999'
        elif case=='rewire':
            other=next(n for key,n in obs['nets'].items() if key!=name and not key.startswith('unconnected-'))
            net['nodes'].remove(node);other['nodes'].append(node)
        elif case=='changed_connected_type': node['pintype']='invalid'
        else: node['pintype']='no_connect'
    elif case in ('nc_to_signal','nc_to_nc','nc_marker_missing','ordinary_nc_bare_type','source_nc_wrong_type'):
        name,net,node=endpoint(obs,False)
        if case in ('nc_to_signal','nc_to_nc'):
            other=next(n for key,n in obs['nets'].items() if key!=name and key.startswith('unconnected-')==(case=='nc_to_nc'))
            del obs['nets'][name];other['nodes'].append(node)
        elif case=='nc_marker_missing': node['pintype']=node['pintype'].split('+')[0]
        elif case=='ordinary_nc_bare_type': node['pintype']='no_connect'
        else:
            target=next(n for net in obs['nets'].values() for n in net['nodes'] if n['ref']=='U7101' and n['pin']=='1')
            target['pintype']='passive+no_connect'
    else: raise AssertionError(case)


CASES='missing_reference extra_reference missing_uuid changed_uuid duplicate_uuid missing_multiunit_uuid missing_unit unit_zero_alias extra_unit missing_unit_pin duplicate_unit_pin unit_pin_substitution missing_property changed_keywords changed_filters invented_property field_substitution property_substitution changed_value changed_footprint changed_library annotation_flag missing_library_pin missing_endpoint duplicate_endpoint changed_pin rewire changed_connected_type connected_nc_type nc_to_signal nc_to_nc nc_marker_missing ordinary_nc_bare_type source_nc_wrong_type'.split()
for case in CASES:
    def test(self, case=case):
        obs=copy.deepcopy(OBSERVED);mutate(obs,case)
        with self.assertRaises(ValueError):subject.compare(obs,EXPECTED)
    setattr(RetainedObservationTests,'test_reject_'+case,test)

if __name__=='__main__': unittest.main()
