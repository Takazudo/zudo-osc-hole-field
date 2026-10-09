"""The experimental AGND replay must never silently rebase on newer core copper."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / 'circuit/routing/issue189/core-ground-link/prepare.py'
spec = importlib.util.spec_from_file_location('core_ground_prepare', SOURCE)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class PinnedGroundProposal(unittest.TestCase):
    def test_changed_canonical_or_proposal_stops_before_native_application(self):
        for changed in ('board', 'proposal'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                board = root / 'boards/osc-core/osc-core.kicad_pcb'
                board.parent.mkdir(parents=True)
                board.write_text('original board')
                here = root / 'source'
                here.mkdir()
                proposal = here / 'proposal.json'
                proposal.write_text('{}')
                (here / 'plan.json').write_text(json.dumps({
                    'base_sha256': hashlib.sha256(board.read_bytes()).hexdigest(),
                    'proposal_sha256': hashlib.sha256(proposal.read_bytes()).hexdigest(),
                }))
                (board if changed == 'board' else proposal).write_text('changed')
                with patch.object(prepare, 'ROOT', root), patch.object(prepare, 'HERE', here), patch.object(prepare.subprocess, 'run') as native:
                    with self.assertRaises(ValueError):
                        prepare.main()
                    native.assert_not_called()
                    self.assertFalse((root / '.circuit-cache').exists())


if __name__ == '__main__':
    unittest.main()
