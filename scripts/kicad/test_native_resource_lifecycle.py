"""Replay lifecycle observations without Docker, systemd or native execution."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.kicad import native_resource_guard as guard

CID = 'a' * 64
OTHER = 'b' * 64
WORKER = 'lifecycle-a'
SLICE = '/epic242.slice/epic242-a.slice'


def container(running=True, status=None, code=0):
    return {'Id': CID, 'Config': {'Labels': {'epic242.native.worker': WORKER}},
            'HostConfig': {'Memory': guard.CAP, 'MemorySwap': guard.CAP, 'CgroupParent': SLICE.rsplit('/', 1)[1]},
            'State': {'Running': running, 'Status': status or ('running' if running else 'exited'),
                      'Pid': 123 if running else 0, 'ExitCode': code, 'OOMKilled': False, 'Error': ''}}


def missing(cid=CID):
    return subprocess.CalledProcessError(1, ['docker','inspect',cid], output='[]', stderr='Error: No such object: '+cid+'\n')


class LifecycleTests(unittest.TestCase):
    def test_previously_verified_disappearance_is_absence_not_exit_success(self):
        verified, transitions, memberships = set(), [], {}
        with patch.object(guard,'run',return_value=json.dumps([container()])), \
             patch.object(guard,'process_identity',return_value='777'), \
             patch.object(Path,'read_text',return_value='0::'+SLICE+'/docker-'+CID+'.scope\n'):
            guard.observe_container(CID,WORKER,SLICE,verified,transitions,memberships)
        self.assertEqual(verified,{CID})
        self.assertEqual(memberships[CID]['process_start'],'777')
        with patch.object(guard,'run',side_effect=[missing(),'']) as calls:
            self.assertIsNone(guard.observe_container(CID,WORKER,SLICE,verified,transitions,memberships))
        self.assertEqual(calls.call_args_list[-1].args[0],['docker','ps','-aq','--no-trunc'])
        self.assertTrue(transitions[-1]['absence_verified'])
        self.assertIn('UNKNOWN',transitions[-1]['exit_status'])
        self.assertIn('No such object',transitions[-1]['stderr'])

    def test_missing_without_prior_membership_and_generic_errors_are_fatal(self):
        errors=[missing(), subprocess.CalledProcessError(1,['docker','inspect'],stderr='permission denied'),
                subprocess.CalledProcessError(1,['docker','inspect'],stderr='Cannot connect to Docker daemon'),
                missing(OTHER), subprocess.TimeoutExpired(['docker','inspect'],20)]
        for error in errors:
            verified=set() if error is errors[0] else {CID}
            with self.subTest(error=str(error)),patch.object(guard,'run',side_effect=error) as call:
                with self.assertRaises((subprocess.CalledProcessError,subprocess.TimeoutExpired)):
                    guard.observe_container(CID,WORKER,SLICE,verified,[],{})
                self.assertEqual(call.call_count,1)

    def test_absence_requires_successful_unfiltered_listing(self):
        for listing in (CID, 'truncated', subprocess.CalledProcessError(1,['docker','ps'],stderr='denied')):
            with self.subTest(listing=str(listing)),patch.object(guard,'run',side_effect=[missing(),listing]):
                with self.assertRaises((ValueError,subprocess.CalledProcessError)):
                    guard.observe_container(CID,WORKER,SLICE,{CID},[],{})

    def test_typed_container_missing_errors_still_require_positive_absence(self):
        for prefix in ('Error: No such container: ', 'Error response from daemon: No such container: '):
            error=missing();error.stderr=prefix+CID
            with self.subTest(prefix=prefix),patch.object(guard,'run',side_effect=[error,'']):
                self.assertIsNone(guard.observe_container(CID,WORKER,SLICE,{CID},[],{}))
            with patch.object(guard,'run',side_effect=[error,CID]),self.assertRaises(ValueError):
                guard.observe_container(CID,WORKER,SLICE,{CID},[],{})

    def test_identity_caps_and_readable_wrong_cgroup_remain_fatal(self):
        for path,value in [(('Id',),OTHER),(('Config','Labels','epic242.native.worker'),'other'),
                           (('HostConfig','Memory'),0),(('HostConfig','MemorySwap'),0),
                           (('HostConfig','CgroupParent'),'wrong.slice')]:
            item=container(); target=item
            for key in path[:-1]:target=target[key]
            target[path[-1]]=value
            with self.subTest(path=path),patch.object(guard,'run',return_value=json.dumps([item])):
                with self.assertRaises(ValueError):guard.observe_container(CID,WORKER,SLICE,{CID},[],{})
        with patch.object(guard,'run',return_value=json.dumps([container()])) as call, \
             patch.object(guard,'process_identity',return_value='777'),patch.object(Path,'read_text',return_value='0::/wrong.slice/process'):
            with self.assertRaisesRegex(ValueError,'outside'):guard.observe_container(CID,WORKER,SLICE,{CID},[],{})
            self.assertEqual(call.call_count,1)  # Never reinterpret readable mismatch as a race.

    def test_proc_disappearance_requires_terminal_or_verified_absence(self):
        for second in (json.dumps([container(False)]),missing()):
            responses=[json.dumps([container()]),second]
            if isinstance(second,Exception):responses.append('')
            events=[]
            with patch.object(guard,'run',side_effect=responses),patch.object(guard,'process_identity',side_effect=FileNotFoundError('gone')):
                self.assertIsNone(guard.observe_container(CID,WORKER,SLICE,{CID},events,{}))
            self.assertEqual(events[0]['event'],'process disappeared during observation')

    def test_proc_disappearance_rechecks_once_and_does_not_loop(self):
        with patch.object(guard,'run',return_value=json.dumps([container()])) as call, \
             patch.object(guard,'process_identity',side_effect=FileNotFoundError('gone')):
            with self.assertRaisesRegex(ValueError,'indeterminate'):guard.observe_container(CID,WORKER,SLICE,{CID},[],{})
            self.assertEqual(call.call_count,2)
        with patch.object(guard,'run',return_value=json.dumps([container()])), \
             patch.object(guard,'process_identity',side_effect=[FileNotFoundError('gone'),'new','new']), \
             patch.object(Path,'read_text',return_value='0::'+SLICE+'/docker.scope'):
            self.assertIsNotNone(guard.observe_container(CID,WORKER,SLICE,{CID},[],{}))

    def test_nonzero_container_exit_and_pid_reuse_are_fatal(self):
        with patch.object(guard,'run',return_value=json.dumps([container(False,code=7)])):
            with self.assertRaisesRegex(ValueError,'terminal state'):guard.observe_container(CID,WORKER,SLICE,{CID},[],{})
        with patch.object(guard,'run',return_value=json.dumps([container()])), \
             patch.object(guard,'process_identity',side_effect=['old','new']), \
             patch.object(Path,'read_text',return_value='0::'+SLICE+'/docker.scope'):
            with self.assertRaisesRegex(ValueError,'identity changed'):guard.observe_container(CID,WORKER,SLICE,{CID},[],{})

    def test_kernel_peak_and_unknown_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name,value in [('memory.peak','123456'),('memory.current','17'),('memory.events','oom 0\noom_kill 0\n')]:
                (root/name).write_text(value)
            self.assertEqual(guard.capture_memory(root)['peak'],123456)
            (root/'memory.peak').unlink()
            self.assertEqual(guard.capture_memory(root)['status'],'UNAVAILABLE')
        self.assertEqual(guard.capture_memory(None)['status'],'UNAVAILABLE')

    def test_final_state_retains_survivors_unknowns_and_all_units(self):
        units=['checks','anchor','watchdog']
        with patch.object(guard,'worker_containers',return_value=[]),patch.object(guard,'unit_state',return_value=('not-found','inactive')):
            state=guard.final_owned_state(WORKER,units)
            self.assertTrue(state['workload_absent']);self.assertEqual(set(state['units']),set(units))
        with patch.object(guard,'worker_containers',return_value=[CID]),patch.object(guard,'unit_state',return_value=('loaded','active')):
            state=guard.final_owned_state(WORKER,units)
            self.assertFalse(state['workload_absent']);self.assertEqual(state['containers'],[CID])
        with patch.object(guard,'worker_containers',side_effect=RuntimeError('daemon unavailable')),patch.object(guard,'unit_state',side_effect=RuntimeError('unit unknown')):
            state=guard.final_owned_state(WORKER,units)
            self.assertIsNone(state['workload_absent']);self.assertEqual(len(state['errors']),4)


if __name__=='__main__':unittest.main()
