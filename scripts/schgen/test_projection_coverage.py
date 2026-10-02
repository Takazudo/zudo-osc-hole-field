"""Independent native-export coverage, without invoking KiCad or a generator."""
from copy import deepcopy
import json
import unittest
from scripts.schgen.project_boards import net_token
from scripts.schgen.verify_cross_board import verify, native_component, ROOT


def export(parts, pins):
    def quote(value):return json.dumps(value)
    components=[]
    for ref,attrs in parts.items():
        footprint=attrs.get('footprint','F')
        properties=''.join(f'(property (name {quote(k)}) (value {quote(v)}))'
                           for k,v in attrs.get('properties',{}).items())
        libsource=attrs.get('libsource')
        libtext='' if libsource is None else f'(libsource (lib {quote(libsource[0])}) (part {quote(libsource[1])}))'
        components.append(f'(comp (ref {quote(ref)}) (value {quote(attrs.get("value","R"))}) '
                          +(f'(footprint {quote(footprint)})' if footprint else '')+properties+libtext+')')
    nets={}
    for (ref,pin),net in pins.items():
        name=net if net is not None else f'unconnected-({ref}-Pad{pin})'
        nets.setdefault(name,[]).append(f'(node (ref {quote(ref)}) (pin {quote(pin)}))')
    return '(export (components '+''.join(components)+') (nets '+''.join(
        f'(net (code {i}) (name {quote(net)}) '+''.join(nodes)+')'
        for i,(net,nodes) in enumerate(nets.items(),1))+'))'


class ProjectionCoverageTests(unittest.TestCase):
    def setUp(self):
        self.partition={
            'boards':[{'id':'a','board_key':'A'},{'id':'b','board_key':'B'}],
            'assignment':{'components':[{'ref':'RAAA','board':'A','fitted':True},
                                        {'ref':'RBBB','board':'B','fitted':True}],
                          'abstract_boundaries':['CN301','XB301']},
            'connectors':[{'id':board+'-j','pcb_reference':'J'+board*3,'board':board,
                           'contacts':3,'header_mpn':'BM03B-GHS-TBT(LF)(SN)',
                           'pin_map':{'1':'SIGNAL','2':'NC','3':'NC'},
                           'mechanical_pads':['MP1','MP2']} for board in ('A','B')],
            'harnesses':[{'id':'wire','header_ids':['A-j','B-j']}],
            'load_side_terminals':[{'reference':'TP'+board*3,'board':board,
                                   'net':'+12V','manufacturer_pin':'1'} for board in ('A','B')],
            'load_side_wires':[{'id':'rail','terminal_refs':['TPAAA','TPBBB'],'net':'+12V'}],
            'counts':{'load_side_copper_terminals':2,'factory_load_side_wires':1}}
        boundary={'footprint':'','properties':{'AbstractBoundary':'true','MPN':'',
                  'Implementation':'REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE'}}
        self.master_parts={'RAAA':{},'RBBB':{},'CN301':deepcopy(boundary),'XB301':deepcopy(boundary)}
        self.master_pins={('RAAA','1'):'SIGNAL',('RBBB','1'):'SIGNAL',
                          ('RAAA','2'):'+12V',('RBBB','2'):'+12V',
                          ('CN301','1'):'+12V_IN',('XB301','1'):'+12V_IN',('XB301','2'):'+12V'}
        self.parts={};self.pins={}
        for board in ('A','B'):
            suffix=board*3;key=board.lower()
            self.parts[key]={'R'+suffix:{},'TP'+suffix:{},'J'+suffix:{
                'value':'BM03B-GHS-TBT(LF)(SN)',
                'footprint':'zudo-osc-hole-field:JST_GH3_BM_TopEntry',
                'libsource':('zudo-osc-hole-field','JST_GH3_BM'),
                'properties':{'MPN':'BM03B-GHS-TBT(LF)(SN)','Manufacturer':'JST'}}}
            self.pins[key]={('R'+suffix,'1'):net_token('SIGNAL'),('R'+suffix,'2'):'+12V',
                            ('J'+suffix,'1'):net_token('SIGNAL'),('J'+suffix,'2'):None,('J'+suffix,'3'):None,
                            ('J'+suffix,'MP1'):None,('J'+suffix,'MP2'):None,('TP'+suffix,'1'):'+12V'}

    def check(self):
        return verify(self.partition,{board:export(parts,self.pins[board])
                       for board,parts in self.parts.items()},export(self.master_parts,self.master_pins))

    def test_valid_interfaces_keep_nc_mechanical_and_abstract_boundaries(self):
        result=self.check()
        self.assertEqual(result['physical_components'],2)
        self.assertEqual(result['physical_pins'],4)
        self.assertEqual(result['master_nets'],2)
        self.assertEqual(result['cross_board_nets'],2)
        self.assertEqual(result['interface_pins'],12)
        self.assertEqual(result['unconnected_interface_pins'],8)
        self.assertEqual(result['validated_abstract_exclusions'],['CN301','XB301'])
        self.assertEqual(result['verified_header_identities'],2)

    def test_omitted_electrical_nc_mechanical_and_load_terminal_pins_fail(self):
        for key in (('JBBB','1'),('JBBB','2'),('JBBB','MP1'),('TPBBB','1')):
            with self.subTest(key=key):
                value=self.pins['b'].pop(key)
                with self.assertRaisesRegex(ValueError,'interface pin set/map mismatch'):self.check()
                self.pins['b'][key]=value

    def test_extra_or_connected_mechanical_pin_fails(self):
        for key in (('JBBB','4'),('JBBB','MP1')):
            with self.subTest(key=key):
                before=dict(self.pins['b']);self.pins['b'][key]=net_token('SIGNAL')
                with self.assertRaisesRegex(ValueError,'interface pin set/map mismatch'):self.check()
                self.pins['b']=before

    def test_missing_assignment_and_projected_component_cannot_hide_master_part(self):
        self.partition['assignment']['components']=self.partition['assignment']['components'][:1]
        del self.parts['b']['RBBB']
        self.pins['b']={key:value for key,value in self.pins['b'].items() if key[0]!='RBBB'}
        with self.assertRaisesRegex(ValueError,'master physical component coverage'):self.check()

    def test_only_validated_declared_abstract_boundaries_are_excluded(self):
        for mutation in ('extra_exclusion','missing_exclusion','duplicate_exclusion',
                         'marker','footprint','mpn','implementation','forged_physical'):
            with self.subTest(mutation=mutation):
                original_partition=deepcopy(self.partition);original_parts=deepcopy(self.master_parts)
                if mutation=='extra_exclusion':self.partition['assignment']['abstract_boundaries'].append('RBBB')
                elif mutation=='missing_exclusion':self.partition['assignment']['abstract_boundaries'].pop()
                elif mutation=='duplicate_exclusion':self.partition['assignment']['abstract_boundaries'].append('CN301')
                elif mutation=='marker':del self.master_parts['CN301']['properties']['AbstractBoundary']
                elif mutation=='footprint':self.master_parts['CN301']['footprint']='F'
                elif mutation=='mpn':self.master_parts['CN301']['properties']['MPN']='ORDERABLE'
                elif mutation=='implementation':self.master_parts['CN301']['properties']['Implementation']='IMPLEMENTED'
                else:self.master_parts['RBBB']['properties']={'AbstractBoundary':'true'}
                with self.assertRaises(ValueError):self.check()
                self.partition=original_partition;self.master_parts=original_parts

    def test_duplicate_or_colliding_interface_references_fail(self):
        for ref in ('JAAA','RAAA','TPAAA'):
            with self.subTest(ref=ref):
                original=self.partition['connectors'][1]['pcb_reference']
                self.partition['connectors'][1]['pcb_reference']=ref
                with self.assertRaisesRegex(ValueError,'interface reference'):self.check()
                self.partition['connectors'][1]['pcb_reference']=original

    def test_incomplete_or_overlapping_source_pin_declarations_fail(self):
        for mutation in ('missing_electrical','extra_electrical','mechanical_overlap','mechanical_duplicate'):
            with self.subTest(mutation=mutation):
                original=deepcopy(self.partition['connectors'])
                # Both mates change consistently: mate equality alone cannot catch this.
                for connector in self.partition['connectors']:
                    if mutation=='missing_electrical':connector['pin_map'].pop('2')
                    elif mutation=='extra_electrical':connector['pin_map']['4']='NC'
                    elif mutation=='mechanical_overlap':connector['mechanical_pads'].append('1')
                    else:connector['mechanical_pads'].append('MP1')
                with self.assertRaisesRegex(ValueError,'pin declaration'):self.check()
                self.partition['connectors']=original

    def test_duplicate_board_keys_and_malformed_property_values_fail(self):
        self.partition['boards'][1]['board_key']='A'
        with self.assertRaisesRegex(ValueError,'duplicate declared board key'):self.check()
        for value in (['value'],['value','one','two']):
            node=['comp',['value','R'],['property',['name','AbstractBoundary'],value]]
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'malformed native property'):
                native_component('CN301',node)

    def test_inserted_header_identity_and_population_cannot_drift(self):
        for field,value in (('value','WRONG'),('footprint','WRONG:LAND'),
                            ('libsource',('wrong','JST_GH3_BM')),('libsource',('zudo-osc-hole-field','WRONG')),
                            ('MPN','WRONG'),('Manufacturer','WRONG'),('dnp','')):
            with self.subTest(field=field,value=value):
                original=deepcopy(self.parts['b']['JBBB'])
                if field in ('MPN','Manufacturer','dnp'):
                    self.parts['b']['JBBB']['properties'][field]=value
                else:self.parts['b']['JBBB'][field]=value
                with self.assertRaisesRegex(ValueError,'header identity'):self.check()
                self.parts['b']['JBBB']=original
        self.partition['connectors'][1]['header_mpn']='WRONG'
        with self.assertRaisesRegex(ValueError,'header identity'):self.check()

    def test_physical_dnp_master_part_remains_in_complete_coverage(self):
        self.master_parts['RBBB']['properties']={'dnp':''}
        self.parts['b']['RBBB']['properties']={'dnp':''}
        self.partition['assignment']['components'][1]['fitted']=False
        result=self.check()
        self.assertEqual(result['physical_components'],2)
        self.assertEqual(result['dnp_components'],1)
        self.assertEqual(result['fitted_components'],1)

    def test_physical_population_drift_is_rejected(self):
        for case in ('board_only','assignment_only','master_only','nonboolean_assignment'):
            with self.subTest(case=case):
                self.setUp()
                if case=='board_only':self.parts['b']['RBBB']['properties']={'dnp':''}
                elif case=='assignment_only':self.partition['assignment']['components'][1]['fitted']=False
                elif case=='master_only':self.master_parts['RBBB']['properties']={'dnp':''}
                else:self.partition['assignment']['components'][1]['fitted']=1
                with self.assertRaisesRegex(ValueError,'population'):self.check()
        # Removing a real DNP marker must fail too, not only adding one.
        self.setUp()
        self.master_parts['RBBB']['properties']={'dnp':''}
        self.partition['assignment']['components'][1]['fitted']=False
        with self.assertRaisesRegex(ValueError,'projected DNP population'):self.check()

    def add_load_pair(self, net):
        refs=[]
        for board in ('A','B'):
            ref='TPEXTRA'+board;refs.append(ref)
            self.partition['load_side_terminals'].append(
                {'reference':ref,'board':board,'net':net,'manufacturer_pin':'1'})
            self.parts[board.lower()][ref]={}
            self.pins[board.lower()][(ref,'1')]=net_token(net)
        self.partition['load_side_wires'].append(
            {'id':'extra-wire','terminal_refs':refs,'net':net})
        self.partition['counts'].update(load_side_copper_terminals=4,factory_load_side_wires=2)

    def test_load_terminals_cannot_export_a_local_sensitive_net(self):
        net='/H1/HOLD_CAP'
        self.master_pins[('RAAA','1')]=net
        self.pins['a'][('RAAA','1')]=net_token(net)
        self.add_load_pair(net)
        with self.assertRaisesRegex(ValueError,'Sensitive net on interface'):self.check()

    def test_load_terminals_cannot_bypass_raw_storage_or_summing_screen(self):
        for net in ('/NEW/RAW_TIP','/NEW/IN_TIP','/NEW/OUT_TIP','/NEW/SLEW_STORAGE','/NEW/HOLD_CAP','/NEW/SUMMING'):
            with self.subTest(net=net):
                self.setUp();self.add_load_pair(net)
                with self.assertRaisesRegex(ValueError,'raw/storage/summing'):self.check()

    def test_load_terminals_allow_only_independent_source_power_nets(self):
        for net in ('SIGNAL','+12V_IN','-12V_IN','+5V_IN'):
            with self.subTest(net=net):
                self.setUp();self.add_load_pair(net)
                # A modified generated echo must not authorize a signal or raw rail.
                self.partition['power']={'load_distribution':{'net_order':[net]}}
                with self.assertRaisesRegex(ValueError,'outside source load-distribution rails'):self.check()

    def test_all_declared_load_rails_and_return_remain_accepted(self):
        source=json.loads((ROOT/'design/partition/partition-input.json').read_text())
        for net in set(source['load_distribution']['net_order']):
            with self.subTest(net=net):
                self.setUp();self.add_load_pair(net)
                result=self.check()
                self.assertEqual(result['load_side_terminals'],4)
                self.assertEqual(result['load_side_wires'],2)

    def test_actual_tip_naming_cannot_cross_a_gh_harness(self):
        net='/A01/IN_TIP'
        self.master_pins[('RAAA','1')]=net
        self.pins['a'][('RAAA','1')]=net_token(net)
        ids=[]
        for board in ('A','B'):
            connector=deepcopy(self.partition['connectors'][0])
            connector.update(id='raw-'+board,pcb_reference='JRAW'+board,board=board,
                             pin_map={'1':net,'2':'NC','3':'NC'})
            ids.append(connector['id']);self.partition['connectors'].append(connector)
            self.parts[board.lower()][connector['pcb_reference']]=deepcopy(self.parts[board.lower()]['J'+board*3])
            for pin,value in {'1':net_token(net),'2':None,'3':None,'MP1':None,'MP2':None}.items():
                self.pins[board.lower()][(connector['pcb_reference'],pin)]=value
        self.partition['harnesses'].append({'id':'raw-wire','header_ids':ids})
        with self.assertRaisesRegex(ValueError,'raw/storage/summing'):self.check()

    def test_missing_board_export_fails(self):
        del self.parts['b']
        with self.assertRaisesRegex(ValueError,'board export set'):self.check()


if __name__=='__main__':unittest.main()
