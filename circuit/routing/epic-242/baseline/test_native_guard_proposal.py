"""Non-native tests of proposed fail-closed boundaries. No systemd/Docker execution."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('guard', Path(__file__).with_name('native_guard_proposal.py'))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

class GuardTests(unittest.TestCase):
    def test_identity_rejects_injection_and_paths(self):
        for value in ('../x', 'x;sudo', 'x y', '', 'UPPER', 'a'*62):
            with self.subTest(value=value), self.assertRaises(ValueError):g.identity(value)
        self.assertEqual(g.identity('run-251-a1'),'run-251-a1')
    def test_free_floor_and_early_abort(self):
        for free in (0,g.FLOOR,g.ABORT_FREE):
            self.assertIsNotNone(g.stop_reason(free,{}, {},0,300))
        self.assertIsNone(g.stop_reason(g.CAP+g.FLOOR,{}, {},0,300))
    def test_oom_delta_not_historical_event(self):
        self.assertIsNone(g.stop_reason(9*g.GIB,{'oom':1},{'oom':1},1,300))
        for key in ('oom','oom_kill'):
            self.assertIn('OOM',g.stop_reason(9*g.GIB,{key:2},{key:1},1,300))
    def test_whole_command_deadline(self):
        self.assertEqual(g.stop_reason(9*g.GIB,{}, {},300,300),'whole-command deadline')
    def test_shared_container_caps_and_ancestry(self):
        item={'HostConfig':{'Memory':g.CAP,'MemorySwap':g.CAP,'CgroupParent':'epic242-a.slice'}}
        g.docker_membership(item,'0::/epic242.slice/epic242-a.slice/docker-abc.scope','/epic242.slice/epic242-a.slice')
        for key in ('Memory','MemorySwap','CgroupParent'):
            broken={'HostConfig':item['HostConfig']|{key:0}}
            with self.assertRaises(ValueError):g.docker_membership(broken,'0::/bad','/epic242.slice/epic242-a.slice')
        with self.assertRaises(ValueError):g.docker_membership(item,'0::/other.slice/docker-abc.scope','/epic242.slice/epic242-a.slice')
    def test_targeted_cleanup_only(self):
        calls=[]
        with patch.object(g,'worker_containers',return_value=['owned123']),patch.object(g,'run',side_effect=lambda args, **kwargs:calls.append(args) or ''):
            self.assertEqual(g.cleanup('a',['owned.service']),[])
        self.assertIn(['docker','rm','-f','owned123'],calls)
        self.assertFalse(any('prune' in c for c in calls))
    def test_cleanup_errors_block(self):
        with patch.object(g,'worker_containers',return_value=[]),patch.object(g,'run',side_effect=RuntimeError('stop failed')):
            self.assertTrue(g.cleanup('a',['owned.service']))
    def test_remote_context_refused(self):
        with patch.dict(g.os.environ,{'DOCKER_HOST':'tcp://remote'}),patch.object(g,'run') as command:
            with self.assertRaises(ValueError):g.local_docker()
            command.assert_not_called()

if __name__=='__main__':unittest.main()
