"""No native execution: exact current slice and aggregate-cap refusal tests."""
import unittest
from pathlib import Path
from unittest.mock import patch

from native_diagnostic import require_admission


class Admission(unittest.TestCase):
    worker = 'jl250-test'
    slice_name = 'epic242-w' + worker.encode('ascii').hex() + '.slice'

    def call(self, membership=None, aggregate='12884901888', deadline='9999999999'):
        env = {'EPIC242_NATIVE_WORKER': self.worker, 'EPIC242_NATIVE_SLICE': self.slice_name,
               'EPIC242_NATIVE_DEADLINE': deadline}

        def content(path):
            name = str(path)
            if name == '/proc/self/cgroup':
                return '0::' + (membership or '/epic242.slice/' + self.slice_name + '/checks.service') + '\n'
            if name.endswith('memory.swap.max'):
                return '0\n'
            if name == '/sys/fs/cgroup/epic242.slice/memory.max':
                return aggregate + '\n'
            return '6442450944\n'

        with patch.dict('os.environ', env, clear=True), patch.object(Path, 'read_text', content):
            require_admission('parent-slot', '250-test')

    def test_exact_hex_slice_with_caps(self):
        self.call()

    def test_nested_wrong_parent_refused(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.call('/wrong/epic242.slice/' + self.slice_name + '/checks.service')

    def test_aggregate_unbounded_refused(self):
        with self.assertRaisesRegex(ValueError, 'aggregate'):
            self.call(aggregate='max')

    def test_expired_deadline_refused(self):
        with self.assertRaisesRegex(ValueError, 'expired'):
            self.call(deadline='1')

    def test_historical_slice_refused(self):
        env = {'EPIC242_NATIVE_WORKER': self.worker, 'EPIC242_NATIVE_SLICE': 'epic242-' + self.worker + '.slice',
               'EPIC242_NATIVE_DEADLINE': '9999999999'}
        with patch.dict('os.environ', env, clear=True), self.assertRaisesRegex(ValueError, 'identity'):
            require_admission('parent-slot', '250-test')


if __name__ == '__main__':
    unittest.main()
