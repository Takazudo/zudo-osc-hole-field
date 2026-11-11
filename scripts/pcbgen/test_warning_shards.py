"""Host-only failing-closed controls 1-11 for the sharded silk audit; pcbnew, kicad-cli and the oracle are faked.

Native controls 12-14 run on the pinned image only (scripts/pcbgen/fixtures/warning-shards/README.md).
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import unittest.mock

import scripts.pcbgen.audit_added_mask as audit
import scripts.pcbgen.warning_shards as shards
from scripts.pcbgen.complete_native_warnings import audit_current_reports, complete_reports, resumable_audits
from scripts.pcbgen.test_audit_added_mask import board, item
from scripts.pcbgen.test_audit_added_mask_probe import Board, Track, fake

ROOT=Path(__file__).resolve().parents[2]
UUID=re.compile(r'uuid "([^"]+)"')
DIGEST=shards.pinned_image(ROOT).split('@',1)[1]
SILK_UUID='00000000-0000-4000-8000-text00000001'
EMPTY={'violations':[]}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def kinds(text):
    return [(m[1],'via' if block.startswith('(via') else 'segment')
            for block in re.findall(r'\((?:via|segment)[^()]*(?:\([^()]*\)[^()]*)*\)',text) for m in [UUID.search(block)]]


class Harness(unittest.TestCase):
    """80 added objects (10 vias) so the planned silk ranges are 32/32/16."""
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(dir=ROOT));self.addCleanup(shutil.rmtree,self.tmp)
        self.before=self.make('src','before',board(item(0)))
        self.added=[item(i,'via' if i%8==0 else 'segment') for i in range(1,81)]
        self.after=self.make('src','after',board(item(0),*self.added))
        self.planted=None;self.kill_at=None;self.drc_calls=0
        fake.LoadBoard=lambda path:Board([Track(u,k) for u,k in kinds(Path(path).read_text())])
        patch=unittest.mock.patch.dict(sys.modules,{'pcbnew':fake});patch.start();self.addCleanup(patch.stop)
        self.units=self.tmp/'units';self.units.mkdir()

    def make(self,folder,name,text,dru='(version 1)\n'):
        path=self.tmp/folder/f'{name}.kicad_pcb';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        path.with_suffix('.kicad_pro').write_text(json.dumps({'board':{'design_settings':{'rules':{'min_silk_clearance':0.1,'min_hole_to_hole':0.25}}}}))
        path.with_suffix('.kicad_dru').write_text(dru)
        return path

    # Fake native layer: the real audit_added_mask.main with faked pcbnew/kicad-cli; hole and zone scripts as their result shapes.
    def native(self,argv,root):
        self.assertEqual(argv[:3],['bash','scripts/kicad/run.sh','python3'])
        script,args=argv[3],argv[4:];path=lambda p:Path(root)/p
        if script=='scripts/pcbgen/audit_added_mask.py':
            rng=audit.parse_fixture_range(args[args.index('--fixture-range')+1])
            cuts=(audit.read_stage_removals(path(args[args.index('--stage-removal-scope')+1]),path(args[0]),path(args[1]))
                  if '--stage-removal-scope' in args else [args[i+1] for i,a in enumerate(args) if a=='--reviewed-cut-uuid'])
            self.silk(path(args[0]),path(args[1]),path(args[2]),int(args[args.index('--expected-copper')+1]),int(args[args.index('--expected-vias')+1]),rng,cuts)
        elif script=='scripts/pcbgen/audit_hole_pairs.py':self.holes(path(args[0]),path(args[1]))
        elif script=='scripts/pcbgen/audit_zone_silk_scope.py':self.zones(path(args[0]),path(args[1]),path(args[2]))
        else:self.fail('unexpected native script '+script)

    def silk(self,before,after,out,copper,vias,rng=None,cuts=()):
        def run(args,**kw):
            if audit.PROBE_FLAG in args:
                return types.SimpleNamespace(stdout=''.join(audit.PROBE_PREFIX+json.dumps(audit.native_fixture_view(Path(f)))+'\n' for f in args[3:]))
            self.drc_calls+=1
            if self.kill_at==self.drc_calls:raise subprocess.CalledProcessError(137,args)
            fixture=Path(args[-1]);uid=kinds(fixture.read_text())[0][0]
            rows=[dict(type='silk_over_copper',severity='warning',items=[{'uuid':SILK_UUID},{'uuid':uid}])] if uid==self.planted else []
            Path(args[args.index('--output')+1]).write_text(json.dumps({'violations':rows}))
            return types.SimpleNamespace(stdout='')
        with unittest.mock.patch.object(audit.subprocess,'run',side_effect=run),\
             unittest.mock.patch.object(audit.subprocess,'check_output',return_value='10.0.6\n'),unittest.mock.patch('builtins.print'):
            audit.main(before,after,out,copper,vias,cuts,fixture_range=rng)

    def holes(self,board_path,out):
        holes=[]
        for uid,kind in kinds(board_path.read_text()):
            if kind!='via':continue
            row=dict(uuid=uid,xy=[int(uid[-4:])*10_000_000,0],radius=150000,drill=300000,kind='via',subtype=3,layers=[0,2],net='GND')
            row['object_key']=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest();holes.append(row)
        out.mkdir(parents=True,exist_ok=True)
        (out/'result.json').write_text(json.dumps(dict(status=shards.HOLE_STATUS,version='10.0.6',source_sha256=sha(board_path),
            project_sha256=sha(board_path.with_suffix('.kicad_pro')),rules_sha256=sha(board_path.with_suffix('.kicad_dru')),clearance_nm=250000,
            holes=holes,covered_pairs=[],identities=[],object_identities=[],fixtures=[]),indent=2)+'\n')

    def zones(self,before,after,out):
        out.mkdir(parents=True,exist_ok=True)
        (out/'result.json').write_text(json.dumps(dict(status=shards.ZONE_STATUS,version='10.0.6',before_sha256=sha(before),after_sha256=sha(after),
            zone_metadata_and_outline_unchanged=True,zones=[],all_silk_relevant_zone_shapes_are_subsets=True,zone_silk_scope_complete=True,
            new_zone_silk_identities=[]),indent=2)+'\n')

    def unit(self,name,folder=None,before=None,after=None,digest=DIGEST,commit='a'*40,from_delta=False):
        oracle=lambda root:dict(oracle_mode='docker',kicad_image=shards.pinned_image(root),inspected_image_digest=digest)
        tool=lambda root:dict(tool_commit=commit,tool_files=shards.tool_files(root))
        out=self.units/(folder or name.replace(':','-'))
        shards.run_unit(before or self.before,after or self.after,out,name,from_delta=from_delta,runner=self.native,oracle=oracle,tool=tool)
        return out

    def all_units(self,ranges=((0,32),(32,64),(64,80))):
        for a,b in ranges:self.unit(f'silk:{a}:{b}')
        for name in shards.WHOLE_UNITS:self.unit(name)

    def assemble(self,name='tree'):return shards.assemble(self.before,self.after,self.units,self.tmp/name)

    def reseal(self,folder,fixture_bytes=False):
        """A self-consistent forgery: refresh the hashes an attacker controls so the deeper check is reached."""
        if fixture_bytes:
            res=json.loads((folder/'shard-result.json').read_text())
            for i,f in enumerate(res['fixtures'],res['fixture_range'][0]):f['fixture_sha256']=sha(folder/f'fixture-{i:03d}'/self.after.name)
            (folder/'shard-result.json').write_text(json.dumps(res,indent=2)+'\n')
        receipt=json.loads((folder/shards.RECEIPT).read_text())
        receipt['files']=shards.manifest(folder);receipt['result_sha256']=sha(folder/receipt['result_file'])
        (folder/shards.RECEIPT).write_text(json.dumps(receipt,indent=2)+'\n')

    def edit_receipt(self,folder,**values):
        receipt=json.loads((folder/shards.RECEIPT).read_text());receipt.update(values)
        (folder/shards.RECEIPT).write_text(json.dumps(receipt,indent=2)+'\n')

    def rejects(self,message):
        with self.assertRaisesRegex(ValueError,message):self.assemble('rejected')
        self.assertFalse((self.tmp/'rejected').exists())

    def verify(self,tree):return complete_reports(self.before,self.after,EMPTY,EMPTY,tree/'holes-before',tree/'holes-after',tree/'silk',tree/'zones')[2]


class AssemblyTests(Harness):
    def test_plan_tiles_aligned_ranges_and_pilot_lists_only_its_ranges(self):
        plan=shards.plan(self.before,self.after,32)
        self.assertEqual(plan['units'],['silk:0:32','silk:32:64','silk:64:80','holes-before','holes-after','zones'])
        self.assertEqual(shards.plan(self.before,self.after,64,pilot_ranges=['32:64'])['units'],['silk:32:64'])
        for size in (0,16,48.0):
            with self.subTest(size=size),self.assertRaises(ValueError):shards.plan(self.before,self.after,size)
        for ranges in (['16:48'],['0:81'],['0:32','0:32']):
            with self.subTest(ranges=ranges),self.assertRaises(ValueError):shards.plan(self.before,self.after,32,pilot_ranges=ranges)

    def test_assembled_tree_equals_the_monolith_and_passes_complete_reports(self):
        self.all_units();tree=self.assemble()
        mono=self.tmp/'mono';scope=shards.source_context(self.before,self.after)
        self.silk(self.before,self.after,mono,scope['fixture_total'],scope['expected_vias'])
        self.assertEqual((tree/'silk'/'result.json').read_bytes(),(mono/'result.json').read_bytes())
        for i in range(80):
            for name in ('drc.json',self.after.name,'after.kicad_pro','after.kicad_dru'):
                self.assertEqual((tree/'silk'/f'fixture-{i:03d}'/name).read_bytes(),(mono/f'fixture-{i:03d}'/name).read_bytes())
        self.assertEqual(sorted(p.name for p in tree.iterdir()),['added-copper-scope.json','assembly-receipt.json','holes-after','holes-before','silk','zones'])
        self.assertFalse((tree/'proof.json').exists())
        self.assertFalse(any(tree.rglob(shards.RECEIPT)) or any(tree.rglob(shards.STARTED)))
        self.assertEqual(self.verify(tree)['new_silk_identities'],[])
        receipt=json.loads((tree/'assembly-receipt.json').read_text())
        self.assertEqual(receipt['silk_tiling'],[[0,32],[32,64],[64,80]]);self.assertEqual(len(receipt['units']),6)

    def test_stage_removals_from_the_delta_travel_to_silk_and_zone_units_and_verify(self):
        self.before.write_text(board(item(0),item(200),item(201)))
        for a,b in ((0,32),(32,64),(64,80)):self.unit(f'silk:{a}:{b}',from_delta=True)
        for name in shards.WHOLE_UNITS:self.unit(name,from_delta=True)
        receipts={p.name:json.loads((p/shards.RECEIPT).read_text()) for p in self.units.iterdir() if p.is_dir()}
        scope=str((self.units/'silk-0-32.stage-removal-scope.json').relative_to(ROOT))
        self.assertEqual(receipts['silk-0-32']['argv'][-2:],['--stage-removal-scope',scope])
        self.assertNotIn('--stage-removal-scope',receipts['holes-before']['argv'])
        with self.assertRaisesRegex(ValueError,'unexpected entry'):shards.assemble(self.before,self.after,self.units,self.tmp/'tree',from_delta=True)
        for path in self.units.glob('*.stage-removal-scope.json'):path.unlink()
        with self.assertRaisesRegex(ValueError,'not additive'):self.assemble()
        tree=shards.assemble(self.before,self.after,self.units,self.tmp/'tree',from_delta=True)
        self.assertEqual(json.loads((tree/'added-copper-scope.json').read_text())['copper_removal_source'],'stage')
        (self.tmp/'drc.json').write_text(json.dumps(EMPTY))
        proof=shards.verify(self.before,self.after,tree,self.tmp/'drc.json',self.tmp/'drc.json',from_delta=True)
        self.assertEqual(proof['copper_removal_source'],'stage')

    def test_planted_identity_survives_assembly_and_blocks(self):
        self.planted=f'00000000-0000-4000-8000-{40:012d}';self.all_units();tree=self.assemble()
        result=json.loads((tree/'silk'/'result.json').read_text())
        self.assertEqual(len(result['new_mask_identities']),1)
        with self.assertRaisesRegex(ValueError,'new complete native silk warning identities'):self.verify(tree)

    def test_control_01_missing_shard_or_gap(self):
        self.all_units();tree=self.assemble()
        shutil.rmtree(self.units/'silk-32-64');self.rejects('do not tile')
        result=json.loads((tree/'silk'/'result.json').read_text());del result['fixtures'][32:64]
        (tree/'silk'/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        with self.assertRaisesRegex(ValueError,'silk audit omits added copper'):self.verify(tree)

    def test_control_02_overlapping_or_duplicated_range(self):
        self.all_units();self.unit('silk:0:32','silk-0-32-again');self.rejects('second receipt for unit silk:0:32')
        shutil.rmtree(self.units/'silk-0-32-again');shutil.rmtree(self.units/'silk-32-64');self.unit('silk:0:64');self.rejects('do not tile')

    def test_control_03_unaligned_start_end_beyond_scope_or_wrong_total(self):
        with self.assertRaisesRegex(ValueError,'multiple of 32'):self.unit('silk:16:48')
        with self.assertRaisesRegex(ValueError,'multiple of 32'):self.unit('silk:64:81')
        self.assertFalse((self.units/'silk-16-48').exists())
        self.all_units()
        for forged,message in (('silk:65:80','unaligned'),('silk:64:96','out-of-scope')):
            with self.subTest(forged=forged):
                self.edit_receipt(self.units/'silk-64-80',unit=forged);self.rejects(message)
        self.edit_receipt(self.units/'silk-64-80',unit='silk:64:80')
        folder=self.units/'silk-64-80';res=json.loads((folder/'shard-result.json').read_text());res['fixture_total']=81
        (folder/'shard-result.json').write_text(json.dumps(res));self.reseal(folder);self.rejects('fixture_total')

    def test_control_04_shard_from_another_after_or_before_board(self):
        # Different bytes, same objects: only the hashes can tell these boards apart.
        other_after=self.make('other-after','after',self.after.read_text()+'\n')
        other_before=self.make('other-before','before',self.before.read_text()+'\n')
        for name,kwargs,message in (('after',dict(after=other_after),'after_sha256'),('before',dict(before=other_before),'before_sha256')):
            with self.subTest(name):
                for p in self.units.iterdir():shutil.rmtree(p)
                self.unit('silk:0:32',**kwargs);self.unit('silk:32:64');self.unit('silk:64:80')
                for unit in shards.WHOLE_UNITS:self.unit(unit)
                self.rejects('units differ in '+message)

    def test_control_05_mixed_image_digest_tool_commit_rules_or_project(self):
        self.all_units();folder=self.units/'silk-32-64'
        self.edit_receipt(folder,inspected_image_digest='sha256:'+'0'*64);self.rejects('units differ in inspected_image_digest')
        self.edit_receipt(folder,inspected_image_digest=DIGEST,tool_commit='b'*40);self.rejects('units differ in tool_commit')
        self.edit_receipt(folder,tool_commit='a'*40)
        for p in self.units.iterdir():self.edit_receipt(p,inspected_image_digest='sha256:'+'1'*64)
        self.rejects('inspected_image_digest differs from host')
        for suffix,key in (('.kicad_dru','rules_sha256'),('.kicad_pro','project_sha256')):
            with self.subTest(suffix):
                for p in self.units.iterdir():shutil.rmtree(p)
                variant=self.tmp/('variant'+suffix);shutil.copytree(self.before.parent,variant)
                path=variant/self.before.with_suffix(suffix).name;path.write_text(path.read_text()+' ')
                after_copy=variant/self.after.name;shutil.copyfile(self.after,after_copy)
                for s in ('.kicad_pro','.kicad_dru'):shutil.copyfile(path.with_suffix(s),after_copy.with_suffix(s))
                self.unit('silk:0:32',before=variant/self.before.name,after=after_copy);self.unit('silk:32:64');self.unit('silk:64:80')
                for unit in shards.WHOLE_UNITS:self.unit(unit)
                self.rejects('units differ in '+key)

    def test_control_06_tampered_drc_report(self):
        self.all_units();report=self.units/'silk-32-64'/'fixture-040'/'drc.json'
        report.write_text(json.dumps({'violations':[],'date':'forged'}));self.rejects('file manifest does not verify')
        self.reseal(self.units/'silk-32-64');self.rejects('silk fixture report hash mismatch')
        report.write_text(json.dumps(EMPTY));self.reseal(self.units/'silk-32-64');tree=self.assemble()
        (tree/'silk'/'fixture-040'/'drc.json').write_text(json.dumps({'violations':[],'date':'forged'}))
        with self.assertRaisesRegex(ValueError,'silk fixture report hash mismatch'):self.verify(tree)

    def test_control_07_swapped_fixture_folders(self):
        self.all_units();folder=self.units/'silk-0-32'
        (folder/'fixture-000').rename(folder/'swap');(folder/'fixture-001').rename(folder/'fixture-000');(folder/'swap').rename(folder/'fixture-001')
        self.reseal(folder);self.rejects('fixture board bytes differ from fixture_sha256')
        self.reseal(folder,fixture_bytes=True);self.rejects('fixture copper differs')

    def test_control_08_extra_copper_or_retained_pad_in_a_fixture_board(self):
        self.all_units();folder=self.units/'silk-0-32';path=folder/'fixture-005'/self.after.name;original=path.read_text()
        for extra,message in ((item(99),'fixture copper differs'),('(footprint "x" (pad "1" smd))','retains a pad'),('(zone (uuid "z"))','contains a zone')):
            with self.subTest(message):
                path.write_text(original[:original.rfind(')')]+extra+'\n)');self.reseal(folder,fixture_bytes=True);self.rejects(message)

    def test_control_09_shard_directory_is_never_resumable_silk(self):
        self.all_units();root=self.tmp/'resume';root.mkdir()
        (root/'added-copper-scope.json').write_text(json.dumps({'before_sha256':sha(self.before),'after_sha256':sha(self.after)}))
        shutil.copytree(self.units/'silk-0-32',root/'silk')
        self.assertNotIn('silk',resumable_audits(root,self.before,self.after))
        shutil.copyfile(root/'silk'/'shard-result.json',root/'silk'/'result.json')
        self.assertNotIn('silk',resumable_audits(root,self.before,self.after))
        shutil.copyfile(self.units/'silk-0-32'/'shard-result.json',self.units/'silk-0-32'/'result.json')
        self.reseal(self.units/'silk-0-32');self.rejects('holds result.json')
        (self.units/'silk-0-32'/'result.json').unlink();folder=self.units/'silk-0-32'
        res=json.loads((folder/'shard-result.json').read_text());res['added_copper_scope_complete']=True
        (folder/'shard-result.json').write_text(json.dumps(res));self.reseal(folder);self.rejects('claims added_copper_scope_complete')

    def test_control_10_shard_killed_before_its_receipt(self):
        self.kill_at=5
        with self.assertRaises(subprocess.CalledProcessError):self.unit('silk:32:64')
        folder=self.units/'silk-32-64'
        self.assertTrue((folder/shards.STARTED).exists());self.assertFalse((folder/shards.RECEIPT).exists())
        self.assertFalse((folder/'shard-result.json').exists())
        self.kill_at=None;self.unit('silk:0:32');self.unit('silk:64:80')
        for unit in shards.WHOLE_UNITS:self.unit(unit)
        self.rejects('unit silk-32-64 has no terminal receipt')

    def test_control_11_assembled_tree_resumes_with_zero_native_calls(self):
        self.all_units();tree=self.assemble()
        with unittest.mock.patch('scripts.pcbgen.complete_native_warnings.subprocess.run') as run,\
             unittest.mock.patch('scripts.pcbgen.complete_native_warnings.complete_reports',wraps=complete_reports) as verify:
            result=audit_current_reports(self.before,self.after,EMPTY,EMPTY,self.tmp/'resumed',zone_batch_size=16,resume_from=tree)
        self.assertEqual(run.call_count,0);self.assertEqual(verify.call_count,1)
        self.assertEqual(result[2]['new_silk_identities'],[])
        self.assertEqual((self.tmp/'resumed'/'silk'/'result.json').read_bytes(),(tree/'silk'/'result.json').read_bytes())

    def test_whole_units_must_be_the_complete_script_result_for_these_hashes(self):
        self.all_units()
        for name,key,value,message in (('holes-before','source_sha256','0'*64,'holes-before is not'),('zones','zone_silk_scope_complete',False,'zones is not'),
                                       ('holes-after','status','STARTED','holes-after is not')):
            with self.subTest(name):
                path=self.units/name/'result.json';original=path.read_bytes();row=json.loads(original);row[key]=value
                path.write_text(json.dumps(row));self.reseal(self.units/name);self.rejects(message)
                path.write_bytes(original);self.reseal(self.units/name)
        shutil.rmtree(self.units/'zones');self.rejects('missing unit zones')


class OracleTests(unittest.TestCase):
    def setUp(self):
        patch=unittest.mock.patch.dict('os.environ',{});patch.start();self.addCleanup(patch.stop)
        __import__('os').environ.pop('KICAD_CLI_BIN',None)

    def test_units_refuse_a_native_oracle_or_missing_docker(self):
        with unittest.mock.patch.dict('os.environ',{'KICAD_CLI_BIN':'/usr/bin/kicad-cli'}),self.assertRaisesRegex(ValueError,'native oracle'):
            shards.oracle_identity()
        with unittest.mock.patch.object(shards.shutil,'which',return_value=None),self.assertRaisesRegex(ValueError,'docker missing'):
            shards.oracle_identity()

    def test_inspected_digest_must_equal_pin(self):
        out=lambda digests:types.SimpleNamespace(stdout=json.dumps(digests))
        with unittest.mock.patch.object(shards.shutil,'which',return_value='/usr/bin/docker'):
            with unittest.mock.patch.object(shards.subprocess,'run',return_value=out(['kicad/kicad@sha256:'+'0'*64])),self.assertRaisesRegex(ValueError,'digest differs'):
                shards.oracle_identity()
            with unittest.mock.patch.object(shards.subprocess,'run',return_value=out([shards.pinned_image()])):
                self.assertEqual(shards.oracle_identity()['inspected_image_digest'],DIGEST)


class FixtureAndWorkflowTests(unittest.TestCase):
    def test_committed_fixture_triple_matches_its_builder_and_plans_32_32_rest(self):
        folder=ROOT/'scripts/pcbgen/fixtures/warning-shards'
        subprocess.run([sys.executable,str(folder/'build.py'),'--check'],check=True,capture_output=True)
        manifest=json.loads((folder/'manifest.json').read_text())
        self.assertEqual({name:sha(folder/name) for name in manifest},manifest)
        clean=shards.plan(folder/'before/warning-shards.kicad_pcb',folder/'after-clean/warning-shards.kicad_pcb',32)
        planted=shards.plan(folder/'before/warning-shards.kicad_pcb',folder/'after-planted/warning-shards.kicad_pcb',32)
        self.assertEqual(clean['units'][:3],['silk:0:32','silk:32:64','silk:64:80']);self.assertEqual(planted['fixture_total'],81)

    def test_workflow_is_dispatch_only_read_only_and_artifact_only(self):
        text=(ROOT/'.github/workflows/warning-audit-shards.yml').read_text()
        on=text[text.index('\non:'):text.index('\npermissions:')]
        self.assertIn('workflow_dispatch:',on);self.assertNotRegex(on,r'\n  (push|pull_request|schedule|workflow_run|pull_request_target):')
        self.assertRegex(text,r'\npermissions:\n  contents: read\n');self.assertNotRegex(text,r':\s*write\b')
        self.assertNotRegex(text,r'git\s+(push|commit)|gh\s+pr|actions/cache')
        self.assertEqual(text.count('persist-credentials: false'),text.count('uses: actions/checkout@'))
        self.assertTrue(all(re.fullmatch(r'[0-9a-f]{40}',ref) for ref in re.findall(r'uses: [^@\s]+@(\S+)',text)))
        minutes=[int(m) for m in re.findall(r'timeout-minutes: (\d+)',text)]
        self.assertTrue(minutes and max(minutes)<=330)
        self.assertIn('max-parallel: 4',text);self.assertIn('fail-fast: false',text)
        self.assertIn('CLOUD VERIFICATION; NOT AN ADOPTION',text);self.assertIn('PILOT TIMING; NOT EVIDENCE',text)


if __name__=='__main__':unittest.main()
