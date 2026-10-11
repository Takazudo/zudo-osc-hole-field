"""Fail-closed fixture identity tests; no archive recovery or native execution."""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import f3_fixture as f


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.fixture = self.root/'fixture'; self.fixture.mkdir()
        for name, content in {'before/osc-core.kicad_pcb': 'pcb', 'before/dump.json': json.dumps({'board_sha256': hashlib.sha256(b'pcb').hexdigest()}),
                              'context/library': 'frozen library'}.items():
            path = self.fixture/name; path.parent.mkdir(exist_ok=True); path.write_text(content)
        self.manifest = {'bindings': {'K1402': {'board_sha256': f.check.digest(self.fixture/'before/osc-core.kicad_pcb'),
                                              'dump_sha256': f.check.digest(self.fixture/'before/dump.json')}}}
        (self.root/'matched-demands.json').write_text(json.dumps(self.manifest))
        self.lock = {'source_tree_sha': 'new-adapter-commit', 'original_input_method_sha': f.ORIGINAL_METHOD,
                     'access_tool_sha256': {'adapter': 'sealed'}, 'recovery_artifact': f.ARTIFACTS['K1402'],
                     'files': {str(p.relative_to(self.fixture)): f.check.digest(p) for p in self.fixture.rglob('*') if p.is_file()}}
        self.digest = self.seal()
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        for target, value in [('check.source_checks', None), ('verify_committed_method', None),
                              ('matching.validate_fixture_method', None), ('original_groups', None)]:
            self.stack.enter_context(patch('f3_fixture.'+target, return_value=value))
        self.stack.enter_context(patch.object(f, 'PILOT', self.root))
        self.stack.enter_context(patch.object(f, 'method_hashes', return_value={'adapter':'sealed'}))
        self.stack.enter_context(patch.object(f.subprocess, 'check_output', return_value='new-adapter-commit\n'))

    def seal(self):
        path = self.fixture/'fixture-lock.json'; path.write_text(json.dumps(self.lock))
        return f.check.digest(path)

    def test_external_reviewed_lock_and_complete_members_pass(self):
        f.validate(self.fixture, 'K1402', self.digest)

    def test_omitted_lock_member_cannot_be_resealed_under_reviewed_digest(self):
        self.lock['files'].pop('context/library'); self.seal()
        with self.assertRaisesRegex(ValueError, 'external fixture-lock'):
            f.validate(self.fixture, 'K1402', self.digest)

    def test_census_rejects_extra_or_missing_context(self):
        (self.fixture/'context/extra').write_text('unexpected')
        with self.assertRaisesRegex(ValueError, 'census'):
            f.validate(self.fixture, 'K1402', self.digest)
        (self.fixture/'context/extra').unlink(); (self.fixture/'context/library').unlink()
        with self.assertRaisesRegex(ValueError, 'census'):
            f.validate(self.fixture, 'K1402', self.digest)

    def test_tampered_context_bytes_fail(self):
        (self.fixture/'context/library').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'fixture file drift'):
            f.validate(self.fixture, 'K1402', self.digest)

    def test_original_and_adapter_epochs_are_not_interchangeable(self):
        self.lock['source_tree_sha'] = f.ORIGINAL_METHOD
        with self.assertRaisesRegex(ValueError, 'wrong adapter commit'):
            f.validate(self.fixture, 'K1402', self.seal())
        self.lock['source_tree_sha'] = 'new-adapter-commit'; self.lock['original_input_method_sha'] = 'new-adapter-commit'
        with self.assertRaisesRegex(ValueError, 'adapter/input method drift'):
            f.validate(self.fixture, 'K1402', self.seal())


if __name__ == '__main__':
    unittest.main()
