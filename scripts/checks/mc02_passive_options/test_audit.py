"""Offline source-only option inventory tests; never selects a part."""
import copy
import builtins
import contextlib
import io
import sys
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import audit
from design.spec.instrument import specification
from scripts.checks import passive_candidates


class PassiveOptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.io = json.loads((audit.ROOT/'design/reports/io-partition.json').read_text())
        cls.threading = json.loads((audit.ROOT/'design/stack/fixings/threading-procedure.json').read_text())
        cls.candidates = json.loads((audit.ROOT/'design/readiness/bom-cost-evidence.json').read_text())
        cls.families, cls.instances = specification()

    def report(self, candidates=None, io=None):
        return audit.build(io or self.io, self.threading, self.families, self.instances,
                           candidates or self.candidates, passive_candidates)

    def test_complete_inventory_without_promotion(self):
        before = copy.deepcopy(self.io)
        result = self.report()
        self.assertEqual(result['counts'], {'references':27,'with_existing_options':26,'without_existing_options':1})
        self.assertEqual(self.io, before)
        self.assertTrue(all(r['selected_mpn'] is None and r['physical_access_verdict']=='NOT SHOWN' for r in result['rows']))
        self.assertTrue(all(r['requirement']['required_tolerance_percent'] is None for r in result['rows']))
        self.assertTrue(all(o['adoption']=='UNADOPTED' and o['tolerance_compliance']=='NOT ESTABLISHED'
                            for r in result['rows'] for o in r['options']))
        missing=[r['requirement']['ref'] for r in result['rows'] if not r['options']]
        self.assertEqual(missing,['RB1227'])

    def test_cli_reports_exact_current_and_engineering_provenance(self):
        pins=json.loads((audit.HERE/'source-pins.json').read_text())
        stdout=io.StringIO()
        with patch.object(sys,'argv',['audit.py']),contextlib.redirect_stdout(stdout):
            audit.main()
        result=json.loads(stdout.getvalue())
        for key in ('source_commit','engineering_commit','procedure_amendment'):
            self.assertEqual(result[key],pins[key])

    def test_wrong_value_is_not_an_option(self):
        c=copy.deepcopy(self.candidates['value_only_candidates'][0])
        req={'series':c['series'],'family':c['family'],'value_si':c['value']*2}
        self.assertEqual(audit.options_for(req,[c]),[])

    def test_wrong_tolerance_family_is_not_an_option(self):
        c=copy.deepcopy(self.candidates['value_only_candidates'][0])
        req={'series':c['series'],'family':c['family'],'value_si':c['value']}
        c['family']=c['family'].replace('1%', '0.1%')
        self.assertEqual(audit.options_for(req,[c]),[])

    def test_cross_series_is_not_an_option(self):
        c=copy.deepcopy(self.candidates['value_only_candidates'][0])
        req={'series':'RT0603BRD07','family':c['family'],'value_si':c['value']}
        self.assertEqual(audit.options_for(req,[c]),[])

    def test_candidate_mpn_cannot_disagree_with_value(self):
        report=copy.deepcopy(self.candidates)
        for c in report['value_only_candidates']:
            if c['series']=='RC0603FR-07' and c['value']==1000:
                c['candidate_mpn']='RC0603FR-0710KL'
        with self.assertRaisesRegex(ValueError,'MPN/value conflict'):
            self.report(candidates=report)

    def test_instance_identity_cannot_be_borrowed(self):
        io=copy.deepcopy(self.io)
        next(p for p in io['physical_packages'] if p['ref']=='R1317')['instance']='O2'
        with self.assertRaisesRegex(ValueError,'instance/ref mapping mismatch'):
            self.report(io=io)

    def test_candidate_status_must_remain_unadopted(self):
        report=copy.deepcopy(self.candidates);report['status']='ADOPTED'
        with self.assertRaisesRegex(ValueError,'not UNADOPTED'):
            self.report(candidates=report)

    def test_new_explicit_tolerance_requires_review(self):
        families = tuple(replace(f, parts=tuple(
            replace(p, attributes={**p.attributes, 'Tolerance': '0.1%'})
            if f.name == 'oscillator' and p.key == 'remote_buffer_J_O1_1V_FM__R_ISO.0'
            else p for p in f.parts)) for f in self.families)
        with self.assertRaisesRegex(ValueError, 'explicit tolerance needs reviewed parser'):
            audit.build(self.io, self.threading, families, self.instances,
                        self.candidates, passive_candidates)

    def test_executable_dependency_drift_rejected_before_project_import(self):
        original_read = Path.read_bytes
        original_import = builtins.__import__
        for relative in ('scripts/libgen/build_symbol_lib.py',
                         'design/__init__.py', 'scripts/schgen/__init__.py'):
            with self.subTest(dependency=relative):
                target = audit.ROOT / relative
                attempted = []
                def changed(path):
                    data = original_read(path)
                    return data + b'\n# drift\n' if path == target else data
                def record_import(name, *args, **kwargs):
                    if name == 'design' or name == 'scripts' or name.startswith(('design.', 'scripts.')):
                        attempted.append(name)
                    return original_import(name, *args, **kwargs)
                stderr = io.StringIO()
                with patch.object(Path, 'read_bytes', changed), \
                     patch.object(builtins, '__import__', record_import), \
                     patch.object(sys, 'argv', ['audit.py']), contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as outcome:
                        audit.main()
                self.assertEqual(outcome.exception.code, 1)
                self.assertIn('source drift: ' + relative, stderr.getvalue())
                self.assertEqual(attempted, [], 'project import ran before source rejection')

    def test_pinned_inputs_and_modified_source_rejected(self):
        pins=audit.verify_sources(audit.ROOT)
        original = Path.read_bytes
        target = audit.ROOT / 'design/readiness/bom-cost-evidence.json'
        def changed(path):
            data = original(path)
            return data + b' ' if path == target else data
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError,'source drift'):
                audit.verify_sources(audit.ROOT)



if __name__=='__main__':
    unittest.main()
