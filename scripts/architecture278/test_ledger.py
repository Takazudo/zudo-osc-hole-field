"""Regression tests for package coverage and the production-write boundary."""
import copy
import unittest
from unittest.mock import patch
from scripts.architecture278 import ledger
from scripts.architecture278.check_packet import validate_paths

class LedgerTests(unittest.TestCase):
    def test_complete_counts(self):
        d=ledger.build()
        self.assertEqual(d['counts'],dict(functions=33,panel_centres=438,packages=5904,units=8226,dnp=8))
    def mutated_read(self,fn):
        real=ledger.read
        def read(p):
            d=copy.deepcopy(real(p))
            if p==ledger.SOURCES[2]:fn(d)
            return d
        return read
    def test_missing_unit_rejected(self):
        with patch.object(ledger,'read',self.mutated_read(lambda d:d['package_units'].pop())):
            with self.assertRaises((AssertionError,KeyError)):ledger.build()
    def test_duplicate_unit_rejected(self):
        with patch.object(ledger,'read',self.mutated_read(lambda d:d['package_units'].append(d['package_units'][0]))):
            with self.assertRaises(AssertionError):ledger.build()
    def test_split_package_rejected(self):
        def mutate(d):
            ref=next(p['ref'] for p in d['physical_packages'] if len(p['units'])>1)
            next(u for u in d['package_units'] if u['ref']==ref)['region']='invented-card'
        with patch.object(ledger,'read',self.mutated_read(mutate)):
            with self.assertRaises(AssertionError):ledger.build()
    def test_protected_edits_rejected(self):
        for p in ['boards/osc-core/osc-core.kicad_pcb','design/grid/placements.lock.json','design/partition/decision.json','.github/workflows/check.yml']:
            with self.assertRaises(ValueError):validate_paths([p])
    def test_owned_paths_allowed(self):
        validate_paths(['design/architecture-278/WORK.md','scripts/architecture278/ledger.py'])
if __name__=='__main__':unittest.main()
