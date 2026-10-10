import contextlib,copy,hashlib,importlib.util,io,json,subprocess,tempfile,unittest,weakref
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch

FILE=Path('circuit/routing/issue189/core236-audit-failure/bounded_compare.py')
spec=importlib.util.spec_from_file_location('compare',FILE);compare=importlib.util.module_from_spec(spec);spec.loader.exec_module(compare)
MANIFEST=FILE.with_name('18-fixture-manifest.json')
class BoundedComparisonTests(unittest.TestCase):
    def test_real_original_leg_executes_exact_block_comprehensions_and_retains_loop_state(self):
        m=copy.deepcopy(compare.read(MANIFEST));shape=hashlib.sha256(b'exact fake filled polygons').hexdigest();fixture_bytes=b'fake native fixture'
        for c in m['cases']:c['native_geometry_sha256']=shape;c['fixture_sha256']=hashlib.sha256(fixture_bytes).hexdigest()
        all_ids={uid for c in m['cases'] for uid in c['item_uuids']};zone_ids={c['zone_uuid'] for c in m['cases']}
        uid=lambda value:SimpleNamespace(AsString=lambda:value)
        def fp(value):
            text=SimpleNamespace(m_Uuid=uid('field-'+value),GetShownText=lambda enabled:'rendered-'+value)
            return SimpleNamespace(m_Uuid=uid(value),Pads=lambda:[],GetFields=lambda:[text],GraphicalItems=lambda:[])
        class Board:
            def __init__(self,art,zones):self.art=art;self.zones=zones
            def Zones(self):return [SimpleNamespace(m_Uuid=uid(z),GetFilledPolysList=lambda layer:SimpleNamespace(ArcCount=lambda:0,Format=lambda:'exact fake filled polygons')) for z in self.zones]
            def GetTracks(self):return []
            def GetFootprints(self):return [fp(v) for v in self.art]
            # Forces the ORIGINAL drawing comprehension to resolve pcbnew;
            # fields force its rendered-text generator to resolve texts.
            def GetDrawings(self):return [SimpleNamespace(GetLayer=lambda:44)]
        previous=None;retained=[];loads=[]
        def load(path):
            nonlocal previous
            if Path(path).parent.name in ('start','fresh'):return Board(all_ids,zone_ids)
            if previous is not None:retained.append(previous() is not None)
            index=int(Path(path).parent.name.split('-')[1]);c=m['cases'][index];board=Board(c['item_uuids'],[c['zone_uuid']]);previous=weakref.ref(board);loads.append(index);return board
        native=SimpleNamespace(LoadBoard=load,F_Cu=0,B_Cu=31,Edge_Cuts=44)
        report={'kicad_version':'10.0.6','included_severities':['error','warning','exclusion'],'violations':[]}
        def drc(args,**kwargs):Path(args[args.index('--output')+1]).write_text(json.dumps(report))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'manifest.json').write_text(json.dumps(m));(root/'original-inline.py').write_text(FILE.with_name('baseline-original.py.txt').read_text())
            for name in ['start','fresh',*[f'case-{i:02d}' for i in range(18)]]:
                folder=root/'inputs'/name;folder.mkdir(parents=True)
                for suffix,data in [('.kicad_pcb',fixture_bytes),('.kicad_pro',b'project'),('.kicad_dru',b'rules')]: (folder/('osc-core'+suffix)).write_bytes(data)
                (folder/'saved-drc.json').write_text(json.dumps(report))
            with patch.object(compare,'ROOT',root),patch.dict('sys.modules',{'pcbnew':native}),patch.object(compare.subprocess,'check_output',return_value='10.0.6'),patch.object(compare.subprocess,'run',side_effect=drc) as calls,contextlib.redirect_stdout(io.StringIO()):
                compare.leg('original')
            self.assertEqual(loads,list(range(18)));self.assertEqual(retained,[True]*17);self.assertEqual(calls.call_count,2)
            self.assertEqual(len(compare.read(root/'original/complete.json')['cases']),18)
    def test_fixture_scope_keeps_original_silk_caps_and_does_not_change_full_board_gate(self):
        from scripts.pcbgen.complete_native_warnings import check_caps
        report={'kicad_version':'10.0.6','included_severities':['error','warning','exclusion'],'violations':[{'type':'isolated_copper','severity':'warning','items':[{'uuid':'zone'}]} for _ in range(199)]}
        self.assertEqual(compare.identities(report,'zone'),[])
        with self.assertRaisesRegex(ValueError,'unsupported'):check_caps(report)
        report['violations']=[{'type':'silk_overlap','severity':'warning','items':[{'uuid':'zone'}]} for _ in range(199)]
        with self.assertRaisesRegex(ValueError,'cap'):compare.identities(report,'zone')
    def test_exact_manifest_pairs_and_shared_total_budget(self):
        m=compare.validate_manifest(compare.read(MANIFEST));self.assertEqual(m['budget']['total_seconds'],900)
        for mutate in [lambda m:m['cases'].pop(),lambda m:m['cases'].__setitem__(1,m['cases'][0]),lambda m:m['budget'].__setitem__('total_seconds',1800)]:
            bad=copy.deepcopy(m);mutate(bad)
            with self.assertRaises(ValueError):compare.validate_manifest(bad)
    def test_original_baseline_is_hash_bound_inline_not_new_helper(self):
        m=compare.read(MANIFEST);source=FILE.with_name('baseline-original.py.txt').read_text();code,helper=compare.original_code(source,m['baseline_file_sha256'])
        self.assertIn('LoadBoard',code.co_names);self.assertNotIn('native_fixture_check',code.co_names);self.assertEqual(code.co_filename,'EXACT617INLINE')
        with self.assertRaises(ValueError):compare.original_code(source+'\n',m['baseline_file_sha256'])
    def test_budget_and_memory_stops_are_inconclusive(self):
        budget=compare.read(MANIFEST)['budget'];ok={'available_kib':3*1024*1024,'total_rss_kib':1}
        self.assertIsNone(compare.stop_reason(ok,0,900,budget));self.assertEqual(compare.stop_reason(ok,900,900,budget),'INCONCLUSIVE_TOTAL_BUDGET')
        self.assertEqual(compare.stop_reason(dict(ok,available_kib=1),0,900,budget),'INCONCLUSIVE_EARLY_MEMORY_STOP')
        self.assertEqual(compare.stop_reason(dict(ok,total_rss_kib=13*1024*1024),0,900,budget),'INCONCLUSIVE_EARLY_MEMORY_STOP')
    def test_cleanup_only_owned_container_and_group_even_if_container_stop_times_out(self):
        proc=Mock(pid=42);proc.poll.return_value=None
        with patch.object(compare.subprocess,'run',side_effect=subprocess.TimeoutExpired('docker',5)) as run,patch.object(compare.os,'killpg') as kill:
            compare.cleanup(proc,[('owned-id',99)]);self.assertEqual(run.call_args.args[0],['docker','kill','owned-id']);kill.assert_called_once_with(42,compare.signal.SIGTERM);proc.wait.assert_called_once_with(timeout=5)
    def test_cleanup_kills_group_after_term_timeout(self):
        proc=Mock(pid=42);proc.poll.return_value=None;proc.wait.side_effect=[subprocess.TimeoutExpired('wait',5),0]
        with patch.object(compare.os,'killpg') as kill:compare.cleanup(proc,[])
        self.assertEqual([c.args[1] for c in kill.call_args_list],[compare.signal.SIGTERM,compare.signal.SIGKILL])

if __name__=='__main__':unittest.main()
