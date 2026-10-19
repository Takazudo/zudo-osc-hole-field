"""Fail-closed retirement/proposal checks for the B2-specific study."""
from pathlib import Path
import copy,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('b2_specific_audit',ROOT/'design/architecture-278/implementation/stage44/b2-specific/audit.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class B2RetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        pieces=[f'(segment (start {i} 0) (end {i} 1) (width 0.2) (layer "B.Cu") (net "{net}") (uuid "{uid}"))' for i,net,uid in [(0,'P','private'),(1,'+12V','local')]]
        self.raw='(kicad_pcb '+' '.join(pieces)+')'
        rows=[{'index':i,'kind':'segment','uuid':uid,'net':net,'sha256':m.digest(p)} for i,(p,uid,net) in enumerate(zip(pieces,['private','local'],['P','+12V']))]
        plan={'candidate_B1':{'C3101':{'B2_ref':'C3201'}},'moves':[{'ref':'C3201','old':{'pads':[{'net':'P'}]}}],'NC_equivalence':[],'private_net_retire_copper':[rows[0]]}
        p=self.root/'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(plan))
        self.proof={'baseline_sha256':m.digest(self.raw),'scope_refs':['C3201'],'screened_retirements':[rows[1]]}
        self.receipt={'baseline_sha256':m.digest(self.raw),'moved':['C3201'],'retired_private_copper':[rows[0]],'retired_local_supply_copper':[rows[1]],'private_net_owners':{'P':['C3201']},'retired_hashes':[r['sha256'] for r in rows]}
        self.addCleanup(patch.stopall);patch.object(m,'ROOT',self.root).start();patch.object(m,'BASE_HASH',m.digest(self.raw)).start()
    def check(self,r=None,p=None,raw=None):return m.bound_retirements(r or self.receipt,raw or self.raw,p or self.proof)
    def test_exact_occurrences_pass(self):self.assertEqual(len(self.check()),2)
    def test_changed_baseline_rejected(self):
        with self.assertRaises(ValueError):self.check(raw=self.raw+' ')
    def test_shared_retirement_without_proof_rejected(self):
        r=copy.deepcopy(self.receipt);r['retired_local_supply_copper']=[]
        with self.assertRaises(ValueError):self.check(r)
    def test_foreign_scope_rejected(self):
        r=copy.deepcopy(self.receipt);r['moved'].append('U9999')
        with self.assertRaises(ValueError):self.check(r)
    def test_nc_or_foreign_private_target_rejected(self):
        r=copy.deepcopy(self.receipt);r['private_net_owners']['NC']=['C3201']
        with self.assertRaises(ValueError):self.check(r)
    def test_wrong_local_occurrence_index_rejected(self):
        r=copy.deepcopy(self.receipt);p=copy.deepcopy(self.proof);r['retired_local_supply_copper'][0]['index']=9;p['screened_retirements']=r['retired_local_supply_copper']
        with self.assertRaises(ValueError):self.check(r,p)
    def test_relabelled_local_net_rejected(self):
        r=copy.deepcopy(self.receipt);p=copy.deepcopy(self.proof);r['retired_local_supply_copper'][0]['net']='P';p['screened_retirements']=r['retired_local_supply_copper']
        with self.assertRaises(ValueError):self.check(r,p)
    def test_missing_hash_rejected(self):
        r=copy.deepcopy(self.receipt);r['retired_hashes'].pop()
        with self.assertRaises(ValueError):self.check(r)
    def test_duplicate_occurrence_rejected(self):
        r=copy.deepcopy(self.receipt);p=copy.deepcopy(self.proof);r['retired_local_supply_copper']*=2;p['screened_retirements']=r['retired_local_supply_copper'];r['retired_hashes'].append(r['retired_hashes'][-1])
        with self.assertRaises(ValueError):self.check(r,p)
    def test_unsupported_route_kind_rejected(self):
        with self.assertRaises(ValueError):m.contract({'kind':'arc'})
    def test_integer_copper_contract(self):
        r={'kind':'segment','uuid':'x','net':'P','start_nm':[1,2],'end_nm':[3,4],'width_nm':200000,'layer':'B.Cu'}
        self.assertEqual(m.contract(r),('segment','x',((1,2),(3,4),(200000,),'B.Cu'),'P'))
class ProofAndDependenciesTests(unittest.TestCase):
    def test_modified_ownership_proof_rejected(self):
        raw='{"screened_retirements": []}'
        with patch.object(m,'REVIEWED_BRANCH_PROOF_SHA256',m.digest(raw)):
            self.assertEqual(m.reviewed_proof(raw),{'screened_retirements':[]})
            with self.assertRaises(ValueError):m.reviewed_proof('{"screened_retirements": [{"uuid":"foreign"}]}')
    def test_nested_schematic_change_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/'a',Path(td)/'b'
            for p in (a,b):
                (p/'sheets/nested').mkdir(parents=True);(p/'sheets/nested/child.kicad_sch').write_text('original')
            self.assertTrue(m.check_auxiliary(a,b));(a/'sheets/nested/child.kicad_sch').write_text('changed')
            with self.assertRaises(ValueError):m.check_auxiliary(a,b)
    def test_library_table_change_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/'a',Path(td)/'b';a.mkdir();b.mkdir()
            for p in (a,b):(p/'fp-lib-table').write_text('original')
            (a/'fp-lib-table').write_text('changed')
            with self.assertRaises(ValueError):m.check_auxiliary(a,b)
    def test_missing_child_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/'a',Path(td)/'b';a.mkdir();(b/'sheets').mkdir(parents=True)
            (b/'sheets/child.kicad_sch').write_text('original')
            with self.assertRaises(ValueError):m.check_auxiliary(a,b)

class PackageSerializationTests(unittest.TestCase):
    def test_complete_package_fields_are_preserved(self):
        sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage44/b2-specific'))
        from packages import compare_serialized
        raw='(kicad_pcb (footprint "R:1210" (layer "B.Cu") (at 10 20) (property "Reference" "R3201") (attr smd) (pad "1" smd rect (at 1 0) (size 1 2) (layers "B.Cu")) (model "part.step")))'
        self.assertEqual(set(compare_serialized(raw,raw.replace('(attr','\n(attr'),['R3201'])),{'R3201'})
        for a,b in [('R:1210','R:0805'),('(attr smd)','(attr smd dnp exclude_from_bom)'),('(size 1 2)','(size 2 2)'),('(at 1 0)','(at 2 0)'),('part.step','other.step'),('smd rect','smd oval')]:
            with self.subTest(change=b),self.assertRaises(ValueError):compare_serialized(raw,raw.replace(a,b),['R3201'])

if __name__=='__main__':unittest.main()
