import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import audit as a


def fixture():
    triples = [
        [('STAGE_FALL','FALL','L055'),('STAGE_FALL','STAGE_FALL','L057'),('L057','RISE','L058'),('L055','L058','STAGE_HIGH')],
        [('RISE','TOP_RAW','L066'),('HOLD_N','L066','HOLD_ENABLE'),('CURVED','CURVED','L069'),('READY','RISE','L070')],
        [('L070','L070','L071'),('L071','L069','L072'),('L072','L072','RISE_LINEAR'),('L071','CURVED','L074')]]
    units=[]
    for ref, group in zip(a.REFS,triples):
        for unit,nets in enumerate(group,1):
            units.append({'ref':ref,'unit':unit,'role':'envelope:NAND'+str(a.ROLES[ref][unit-1]),
                          'pins':dict(zip(a.PINS[unit-1],('/E5/'+n for n in nets)))})
        units.append({'ref':ref,'unit':5,'role':'supply','pins':{'7':'AGND','14':'+5V'}})
    for ref,unit,pin,net in [('U4528',2,'5','L069'),('U4528',1,'1','L074'),('D4535',1,'2','HOLD_ENABLE'),('D4527',1,'2','RISE_LINEAR'),('U4547',3,'10','STAGE_HIGH')]:
        units.append({'ref':ref,'unit':unit,'role':'fixture external','pins':{pin:'/E5/'+net}})
    return {'package_units':units,'physical_packages':[{'ref':ref,'mpn':'SN74HC00DR','instance':'E5','units':[1,2,3,4,5]} for ref in a.REFS]}


def expressions():
    functions={'STAGE_HIGH':lambda s:(s['STAGE_FALL'] and s['FALL']) or (not s['STAGE_FALL'] and s['RISE']),
               'HOLD_ENABLE':lambda s:s['HOLD'] or (s['RISE'] and s['TOP_RAW']),
               'RISE_LINEAR':lambda s:s['READY'] and s['RISE'] and not s['CURVED'],
               'RISE_CURVE':lambda s:s['READY'] and s['RISE'] and s['CURVED']}
    return SimpleNamespace(EXPRESSIONS=functions,evaluate=lambda f,s:f(s))


class TimingContractTests(unittest.TestCase):
    def test_complete_fixture_graph_and_128_truth_cases(self):
        gates,external=a.extract(fixture());order,depths=a.order_graph(gates,a.INPUTS)
        self.assertEqual(a.compare(order,expressions()),dict(STAGE_HIGH=128,HOLD_ENABLE=128,RISE_LINEAR=128,L074=128))
        self.assertEqual(depths['STAGE_HIGH'],3);self.assertEqual(depths['HOLD_ENABLE'],2)
        self.assertEqual(depths['RISE_LINEAR'],4);self.assertEqual(depths['L074'],3)
        self.assertEqual(external['L069'][0]['ref'],'U4528')
    def test_duplicate_driver(self):
        gates,_=a.extract(fixture());gates[-1]['output']=gates[0]['output']
        with self.assertRaisesRegex(ValueError,'duplicate driver'):a.order_graph(gates,a.INPUTS)
    def test_cycle(self):
        gates=[{'inputs':['B','IN'],'output':'A'},{'inputs':['A','IN'],'output':'B'}]
        with self.assertRaisesRegex(ValueError,'cyclic'):a.order_graph(gates,['IN'])
    def test_wrong_unit_pin_mapping(self):
        report=fixture();report['package_units'][0]['pins']['99']=report['package_units'][0]['pins'].pop('1')
        with self.assertRaisesRegex(ValueError,'terminals'):a.extract(report)
    def test_wrong_package(self):
        report=fixture();report['physical_packages'][0]['mpn']='SN74HC00PW'
        with self.assertRaisesRegex(ValueError,'identity'):a.extract(report)
    def test_missing_fanout_rejected(self):
        report=fixture();report['package_units']=[x for x in report['package_units'] if x['ref']!='U4528']
        with self.assertRaisesRegex(ValueError,'external contact'):a.extract(report)
    def test_raw_input_cannot_be_replaced_by_synchronized_top(self):
        gates,_=a.extract(fixture())
        for g in gates:g['inputs']=['TOP' if n=='TOP_RAW' else n for n in g['inputs']]
        with self.assertRaisesRegex(ValueError,'boundary'):a.order_graph(gates,a.INPUTS)
    def test_ready_and_curve_are_not_fixed_test_constants(self):
        gates,_=a.extract(fixture());order,_=a.order_graph(gates,a.INPUTS)
        expr=expressions();expr.EXPRESSIONS['RISE_LINEAR']=lambda s:s['RISE']
        with self.assertRaisesRegex(ValueError,'Boolean correspondence'):a.compare(order,expr)
    def test_stale_pin(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'input').write_text('changed')
            with self.assertRaisesRegex(ValueError,'source pin'):a.verify_pins(root,{'sha256':{'input':'0'*64}})
    def test_pinmap_wrong_footprint_pad(self):
        pins=[{'symbol_pin':str(n),'footprint_pad':str(n),'function':'supply'} for n in range(1,15)]
        for unit,(i,j,o) in enumerate(a.PINS,1):
            for n,f in ((i,f'{unit}A input'),(j,f'{unit}B input'),(o,f'{unit}Y NAND output')):pins[int(n)-1]['function']=f
        owner={'pin_maps':[{'symbol':'SN74HC00DR','pins':pins}]};a.validate_pin_map(owner)
        pins[0]['footprint_pad']='2'
        with self.assertRaisesRegex(ValueError,'pin function'):a.validate_pin_map(owner)
    def test_retained_fact_never_becomes_project_timing_budget(self):
        fact={'fact_id':'conditional','source_id':'source','class':'TRANSIENT','value':44,'conditions':'4.5V CL50pF','verdict':'PASS - primary-source confirmed'}
        r=a.timing_coverage({'fixture':{'facts':{'facts':[fact]},'sources':{'sources':[{'source_id':'source','availability':'AVAILABLE'}]}}})
        self.assertEqual(r['retained_owner_observations'][0]['fact']['conditions'],'4.5V CL50pF')
        self.assertEqual(r['retained_owner_observations'][0]['project_applicability'],'NOT_ESTABLISHED')
        for k in ('physical_propagation_delay_ns','setup_slack_ns','hold_slack_ns','permitted_incremental_trace_mm','permitted_incremental_capacitance_pF'):self.assertIsNone(r[k])

    def test_all_new_table_facts_keep_physical_budgets_unknown(self):
        definitions=[('fact-nand-propagation-table-max45',23,'4.5V/-40..85C; input tt<6ns; numeric CL unspecified'),
                     ('fact-nand-output-transition-table-max45',19,'4.5V/-40..85C; 19ns output does not prove <6ns next input'),
                     ('fact-flipflop-data-setup45',25,'4.5V/-40..85C; MAX required setup; CL50pF; input tt<6ns'),
                     ('fact-flipflop-data-hold45',0,'4.5V/-40..85C; MIN required hold; no minimum CLK-to-Q')]
        facts=[{'fact_id':name,'source_id':'conditioned-source','class':'TRANSIENT','value':value,'unit':'ns',
                'conditions':conditions,'verdict':'PASS - primary-source confirmed'} for name,value,conditions in definitions]
        report=a.timing_coverage({'fixture':{'facts':{'facts':facts},'sources':{'sources':[{'source_id':'conditioned-source','availability':'AVAILABLE'}]}}})
        self.assertEqual([o['fact'] for o in report['retained_owner_observations']],facts)
        self.assertTrue(all(o['project_applicability']=='NOT_ESTABLISHED' for o in report['retained_owner_observations']))
        for key in ('physical_propagation_delay_ns','setup_slack_ns','hold_slack_ns','permitted_incremental_trace_mm','permitted_incremental_capacitance_pF'):
            self.assertIsNone(report[key])
        missing=' '.join(report['missing_project_acceptance'])
        self.assertIn('minimum CLK-to-Q',missing);self.assertIn('numeric CL remains unspecified',missing)
        self.assertIn('Cascaded HC00',missing)

    def test_existing_and_symlink_outputs_do_not_run(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); cache=root/'.circuit-cache';cache.mkdir()
            existing=cache/'existing.json';existing.write_text('preserve')
            link=cache/'dangling.json';link.symlink_to(cache/'absent.json')
            live_link=cache/'link.json';live_link.symlink_to(existing)
            for path in (existing,link,live_link):
                with mock.patch.object(a,'ROOT',root), mock.patch.object(a,'run') as run, contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):a.main(['--output',str(path)])
                    run.assert_not_called()
            self.assertEqual(existing.read_text(),'preserve')
    def test_racing_output_creator_does_not_run(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); target=root/'.circuit-cache/result.json';original=Path.open
            def racing_open(path,mode='r',*args,**kwargs):
                if path==target and mode=='x':
                    with original(path,'w') as stream:stream.write('other writer')
                return original(path,mode,*args,**kwargs)
            with mock.patch.object(a,'ROOT',root), mock.patch.object(a,'run') as run, mock.patch.object(Path,'open',racing_open):
                with self.assertRaises(FileExistsError):a.main(['--output',str(target)])
                run.assert_not_called()
            self.assertEqual(target.read_text(),'other writer')
    def test_failure_receipt_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); target=root/'.circuit-cache/result.json'
            with mock.patch.object(a,'ROOT',root), mock.patch.object(a,'run',side_effect=ValueError('stale fixture')):
                with self.assertRaisesRegex(ValueError,'stale fixture'):a.main(['--output',str(target)])
            self.assertEqual(json.loads(target.read_text()),{'status':'ADMISSION_OR_EXECUTION_FAILED','error':'stale fixture'})


if __name__=='__main__':unittest.main()
