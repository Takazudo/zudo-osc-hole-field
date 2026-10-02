"""Portable source/deck drift regressions; native failure fixture stays separate."""
import copy
from dataclasses import replace
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from contextlib import ExitStack, redirect_stdout
import io
from unittest.mock import patch
from design.spec import model_contracts as contracts
from design.spec.cells import _builder as source
from design.spec.cells import sweep_precision_vendor as precision
from design.spec.modules import mix4_vca, run_mixer_spice as mixer


class PrecisionSourceContract(unittest.TestCase):
    def template(self, cell):
        return contracts.precision_contract(cell, source.STANDARD['roles'], source.SHORTLIST, source.AMP)

    def test_feedback_identities_do_not_inherit_generic_representatives(self):
        projection = contracts.current_precision_contract()
        identities = {p['role'].split(':')[1]: p['mpn'] for p in projection['compiled_parts']}
        self.assertEqual(identities['R_FB'], 'RC0603FR-07100RL')
        self.assertEqual(identities['C_FAST'], 'C0603C102J5GACTU')
        self.assertEqual(source.SHORTLIST['r_general']['mpn'], 'RC0603FR-07100KL')
        self.assertEqual(source.SHORTLIST['c_small']['mpn'], 'C0603C101J5GACTU')
        for role, value, unit in [('r_feedback',100,'ohm'),('c_feedback',1e-9,'F')]:
            with self.subTest(role=role):
                self.assertTrue(source._exact_value({'value':value,'unit':unit}, source.SHORTLIST[role]))
                self.assertFalse(source._exact_value({'value':value*2,'unit':unit}, source.SHORTLIST[role]))
                self.assertFalse(source._exact_value({'value':value,'unit':'V'}, source.SHORTLIST[role]))

    def test_all_amplifier_terminals_are_bound(self):
        for pin in ('IN+', 'IN-', 'OUT', 'V+', 'V-'):
            cell = copy.deepcopy(source.CELLS['precision_output'])
            next(p for p in cell['parts'] if p['ref']=='A')['terminals'][pin]='AGND'
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                self.template(cell)

    def test_missing_duplicate_extra_and_dnp_parts_rejected(self):
        for change in ('missing','duplicate','extra','dnp'):
            cell=copy.deepcopy(source.CELLS['precision_output'])
            if change=='missing':cell['parts'].pop()
            if change=='duplicate':cell['parts'][-1]=copy.deepcopy(cell['parts'][0])
            if change=='extra':cell['parts'].append({**cell['parts'][-1], 'ref':'EXTRA'})
            if change=='dnp':cell['parts'][0]['dnp']=True
            with self.subTest(change=change), self.assertRaises(ValueError):self.template(cell)

    def test_value_changes_propagate_and_invalid_domains_fail(self):
        cell=copy.deepcopy(source.CELLS['precision_output'])
        cap=next(p for p in cell['parts'] if p['ref']=='C_FAST')
        cap['value']=2e-9
        self.assertEqual(self.template(cell)['values']['C_FAST'],2e-9)
        for value in (0,-1,float('nan'),float('inf'),True):
            cap['value']=value
            with self.subTest(value=value), self.assertRaises(ValueError):self.template(cell)
        cap['value']=1e-9;cap['unit']='ohm'
        with self.assertRaises(ValueError):self.template(cell)

    def test_compiled_primitive_mapping_cannot_drift(self):
        for key, value in [('r_power','C'),('r_feedback','C'),('c_feedback','R')]:
            with self.subTest(key=key), patch.dict(source.PREFIX,{key:value}), self.assertRaises(ValueError):
                contracts.current_precision_contract()
        with patch.dict(source.PIN_ALIASES,{'r_power':{'1':'2','2':'1'}}), self.assertRaises(ValueError):
            contracts.current_precision_contract()
        # A shortlist substitution must fail, even when the template IDs stay fixed.
        for role in ('r_power','r_feedback','c_feedback'):
            shortlist=copy.deepcopy(source.SHORTLIST)
            shortlist[role]['mpn']=source.SHORTLIST['c_feedback' if role!='c_feedback' else 'r_feedback']['mpn']
            with self.subTest(role=role), patch.object(contracts,'require_current_builder'), patch.object(source,'SHORTLIST',shortlist), self.assertRaises(ValueError):
                contracts.current_precision_contract()

    def test_exact_selected_amplifier_and_compiled_supply_required(self):
        shortlist=copy.deepcopy(source.SHORTLIST)
        shortlist[source.STANDARD['roles']['precision']['part_id']]['mpn']='OPA4196IDR'
        with self.assertRaises(ValueError):
            contracts.precision_contract(source.CELLS['precision_output'],source.STANDARD['roles'],shortlist,source.AMP)
        projection=self.template(source.CELLS['precision_output'])
        parts=list(source.cell_parts('precision_output','J:H1.OUT',{n:n for n in ('SIGNAL','FB','DRIVE','ISO_MID','JACK')}))
        for i,p in enumerate(parts):
            if p.unit==5:parts[i]=replace(p,pins={'4':'+5V','11':'-12V'})
        with self.assertRaises(ValueError):contracts.compiled_precision_contract(parts,projection)

    def test_unused_outputs_split_package_and_role_namespace_rejected(self):
        projection=self.template(source.CELLS['precision_output'])
        original=list(source.cell_parts('precision_output','J:H1.OUT',{n:n for n in ('SIGNAL','FB','DRIVE','ISO_MID','JACK')}))
        shared=next(p.pins['7'] for p in original if p.unit==2)
        for mode in ('shared','split','namespace','ordinal'):
            parts=list(original)
            for i,p in enumerate(parts):
                if p.unit==3:
                    if mode=='shared':parts[i]=replace(p,pins={'8':shared,'9':shared,'10':'AGND'})
                    if mode=='split':parts[i]=replace(p,key='OTHER_PACKAGE.3')
                    if mode=='ordinal':parts[i]=replace(p,ordinal=p.ordinal+10)
                    if mode=='namespace':parts[i]=replace(p,attributes={**p.attributes,'Role':'A'})
            with self.subTest(mode=mode),self.assertRaises(ValueError):contracts.compiled_precision_contract(parts,projection)

    def test_actual_deck_rejects_grounded_input_but_old_failure_fixture_survives(self):
        cells=copy.deepcopy(source.CELLS)
        next(p for p in cells['precision_output']['parts'] if p['ref']=='A')['terminals']['IN+']='AGND'
        with patch.object(source,'CELLS',cells):
            with self.assertRaises(ValueError):precision.deck('10k','5n')
            old=precision.deck('1e12','5n',original=True)
            self.assertIn('Rfb jack fb 10000',old)
            self.assertIn('Cfast drive fb 1e-10',old)

    def test_imported_source_cannot_bind_new_json(self):
        changed=copy.deepcopy(source.STANDARD);changed['roles']['precision']['part_id']='op_audio'
        with patch.object(source,'STANDARD',changed),self.assertRaises(ValueError):contracts.require_current_builder()

    def test_source_lifecycle_mutation_rejected(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/'source.py';p.write_text('old source')
            snapshot={p:p.read_bytes()};contracts.verify_snapshot(snapshot)
            p.write_text('new source')
            with self.assertRaises(ValueError):contracts.verify_snapshot(snapshot)

    def test_nonfinite_measurements_fail(self):
        output='\n'.join(f'{k} = 1e999' for k in precision.METRICS)
        with self.assertRaises(RuntimeError):precision.measure(output)
        row={k:0 for k in ('overshoot_percent','positive_error_mV','negative_error_mV','positive_late_ripple_mV','negative_late_ripple_mV')}
        row['positive_error_mV']=float('nan')
        self.assertTrue(precision.verdict(row))

    def test_zero_exit_error_cannot_publish_precision_metrics(self):
        for error in ('Error: failed control command', 'run simulation(s) aborted'):
            with TemporaryDirectory() as folder, ExitStack() as stack:
                root=Path(folder)
                for name,value in [('ROOT',root),('DECK',root/'case.cir'),('OUT',root/'report.json')]:
                    stack.enter_context(patch.object(precision,name,value))
                stack.enter_context(patch.object(precision,'model'))
                output='\n'.join(f'{name} = 0' for name in precision.METRICS)
                stack.enter_context(patch.object(precision.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=output,stderr=error)))
                with self.subTest(error=error),self.assertRaises(RuntimeError):precision.run(fixture_original=True,offline=True)
                self.assertFalse((root/'report.json').exists())

    def test_retained_precision_source_and_decks(self):
        report=json.loads(precision.OUT.read_text());precision.check_retained(report)
        report['cases'][0]['deck_sha256']='0'*64
        with self.assertRaises(ValueError):precision.check_retained(report)


class MixerSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.family=mix4_vca.family()

    def change(self,role,**kwargs):
        return tuple(replace(p,**kwargs) if p.attributes.get('Role')=='mix4_vca:'+role else p for p in self.family.parts)

    def test_tia_source_change_is_no_longer_ignored(self):
        parts=self.change('R_TIA_FIXED',value='200 kΩ')
        with patch.object(mix4_vca,'family',return_value=replace(self.family,parts=parts)),self.assertRaises(ValueError):mixer.mixer4(5,5)

    def test_ota_signal_polarity_supply_identity_and_extra_internal_branch(self):
        for kind in ('polarity','supply','identity','extra'):
            parts=list(self.family.parts)
            if kind=='extra':
                r=next(p for p in parts if p.attributes.get('Role')=='mix4_vca:R_TIA_FIXED')
                parts.append(replace(r,key='EXTRA.0',attributes={'Role':'extra'},pins={'1':'OTA_SIGNAL','2':'AGND'}))
            else:
                for i,p in enumerate(parts):
                    if p.attributes.get('Role')!='mix4_vca:VCA_OTA':continue
                    if kind=='polarity' and '3' in p.pins:parts[i]=replace(p,pins={**p.pins,'3':'OTA_OFFSET','4':'OTA_SIGNAL'})
                    if kind=='supply' and '11' in p.pins:parts[i]=replace(p,pins={**p.pins,'11':'+5V'})
                    if kind=='identity':parts[i]=replace(p,attributes={**p.attributes,'MPN':'LM13700N/NOPB'})
            with self.subTest(kind=kind),self.assertRaises(ValueError):contracts.mix4_contract(parts)

    def test_trim_strap_amplifier_and_population_changes(self):
        for role,change in [('TIA_CAL',{'pins':{'1':'TIA_TRIM','2':'OTA_CURRENT','3':None}}),
                            ('FEEDTHROUGH',{'value':'100 kΩ'}),('R_OFFSET_FEED',{'dnp':True}),
                            ('SUMMER',{'pins':{'1':'SUM_PRELEVEL','2':'AGND','3':'SUM_NODE'}})]:
            with self.subTest(role=role),self.assertRaises(ValueError):contracts.mix4_contract(self.change(role,**change))

    def test_physical_package_reference_must_match_key_group(self):
        parts=list(self.family.parts)
        amp=next(p for p in parts if p.attributes.get('Role')=='mix4_vca:SUMMER')
        for i,p in enumerate(parts):
            if p.key==amp.key.rsplit('.',1)[0]+'.5':parts[i]=replace(p,ordinal=p.ordinal+10)
        with self.assertRaises(ValueError):contracts.mix4_contract(parts)

    def test_native_decks_stay_identical_to_retained_inputs(self):
        for command in (-5,0,2.5,5):
            for amplitude in (0,1,5):
                name=f'mix4-vendor-{str(command).replace("-","n").replace(".","p")}-{amplitude}v.cir'
                self.assertEqual(mixer.mixer4(command,amplitude),(mixer.DIR/name).read_text())

    def test_nonfinite_incomplete_or_duplicate_measurement_vectors_fail(self):
        rows=json.loads(mixer.OUT.read_text())['runs'][1:]
        self.assertEqual(mixer.model_failures(rows,complete=True),[])
        for changed in (rows[:-1],rows+[rows[0]]):self.assertTrue(mixer.model_failures(changed,complete=True))
        bad=copy.deepcopy(rows);bad[0]['output_extrema_V']['out_max']=float('inf')
        self.assertTrue(mixer.model_failures(bad,complete=True))
        with self.assertRaises(ValueError):mixer.mixer4(float('nan'),5)

    def test_zero_exit_mixer_errors_are_not_measurements(self):
        with TemporaryDirectory() as folder:
            root=Path(folder);deck=root/'case.cir';deck.write_text('fixture')
            result=SimpleNamespace(returncode=0,stdout='out_max = 1\nout_min = -1\n',stderr='run simulation(s) aborted')
            with patch.object(mixer,'ROOT',root),patch.object(mixer.subprocess,'run',return_value=result),self.assertRaises(RuntimeError):mixer.run(deck)

    def test_later_case_cannot_bind_unevaluated_earlier_deck(self):
        with TemporaryDirectory() as folder,ExitStack() as stack:
            root=Path(folder);directory=root/'spice'
            for name,value in [('ROOT',root),('DIR',directory),('OUT',root/'report.json')]:
                stack.enter_context(patch.object(mixer,name,value))
            calls=[]
            def oracle(*args,**kwargs):
                calls.append(args[0][-1])
                if len(calls)==3:(root/calls[0]).write_text('unevaluated replacement')
                return SimpleNamespace(returncode=0,stdout='0 -10 5\nout_max = 0\nout_min = 0\n',stderr='')
            stack.enter_context(patch.object(mixer.subprocess,'run',side_effect=oracle))
            with self.assertRaisesRegex(ValueError,'previously evaluated mixer deck changed'),redirect_stdout(io.StringIO()):mixer.main()
            self.assertFalse((root/'report.json').exists())

    def test_mixer5_result_validation_keeps_existing_targets(self):
        mixer.check_mix5_result({'sum_prelevel':-10,'sum_out':5})
        for bad in ({'sum_prelevel':float('nan'),'sum_out':5},{'sum_prelevel':-10,'sum_out':50},{}):
            with self.assertRaises(ValueError):mixer.check_mix5_result(bad)

    def test_retained_source_model_and_deck_binding(self):
        report=json.loads(mixer.OUT.read_text());mixer.check_retained(report)
        report['runs'][-1]['deck_sha256']='0'*64
        with self.assertRaises(ValueError):mixer.check_retained(report)
        with patch.object(mixer,'MODEL_SHA256','0'*64),self.assertRaises(ValueError):mixer.verify_model()


if __name__=='__main__':unittest.main()
