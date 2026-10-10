import copy,importlib.util,json,subprocess,unittest
from pathlib import Path
from unittest.mock import Mock,patch

FILE=Path('circuit/routing/issue189/core236-audit-failure/bounded_compare.py')
spec=importlib.util.spec_from_file_location('compare',FILE);compare=importlib.util.module_from_spec(spec);spec.loader.exec_module(compare)
MANIFEST=FILE.with_name('18-fixture-manifest.json')
class BoundedComparisonTests(unittest.TestCase):
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
