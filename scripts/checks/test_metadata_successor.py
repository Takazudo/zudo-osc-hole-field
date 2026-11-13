"""Negative controls for metadata-only successors of adopted PCB bytes."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.checks import metadata_successor as ms

BOARD = 'boards/x/x.kicad_pcb'


def footprint(ref, uid, mpn='', maker='', value='1k'):
    def prop(name, text):
        return (f'\t\t(property "{name}" "{text}"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n'
                f'\t\t\t(uuid "{uid[:-4]}{len(name):04d}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n'
                f'\t\t\t\t)\n\t\t\t)\n\t\t)\n')
    return (f'\t(footprint "lib:R"\n\t\t(layer "F.Cu")\n\t\t(uuid "{uid}")\n\t\t(at 10 20)\n'
            + prop('Reference', ref) + prop('Value', value) + prop('MPN', mpn) + prop('Manufacturer', maker)
            + '\t)\n')


def board(*footprints, track_x=0):
    return ('(kicad_pcb\n\t(version 20250000)\n' + ''.join(footprints)
            + f'\t(segment\n\t\t(start {track_x} 0)\n\t\t(end 1 1)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n'
              '\t\t(net "A")\n\t\t(uuid "00000000-0000-4000-8000-000000000099")\n\t)\n)\n')


A = '00000000-0000-4000-8000-00000000a001'
B = '00000000-0000-4000-8000-00000000b001'
ADOPTED = board(footprint('R1', A), footprint('R2', B))
SUCCESSOR = board(footprint('R1', A, 'RC0603FR-071KL', 'YAGEO'), footprint('R2', B))


class Repo:
    """A scratch Git repository holding the adopted bytes in one commit."""

    def __init__(self, temp):
        self.root = Path(temp)
        (self.root / BOARD).parent.mkdir(parents=True)
        (self.root / BOARD).write_text(ADOPTED)
        git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', '-c', 'commit.gpgsign=false']
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        subprocess.run(git + ['add', BOARD], cwd=self.root, check=True)
        subprocess.run(git + ['commit', '-q', '-m', 'adopt'], cwd=self.root, check=True)
        self.commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=self.root, check=True,
                                     capture_output=True, text=True).stdout.strip()

    def receipt(self, successor_text, changes=None, **overrides):
        adopted = ADOPTED.encode()
        oid = subprocess.run(['git', 'rev-parse', f'{self.commit}:{BOARD}'], cwd=self.root, check=True,
                             capture_output=True, text=True).stdout.strip()
        (self.root / BOARD).write_text(successor_text)
        listed = ms.derive(adopted, SUCCESSOR.encode()) if changes is None else changes
        record = {'schema': ms.SCHEMA, 'board': BOARD, 'allowed_properties': list(ms.PROPERTIES),
                  'adopted': {'label': 'X1', 'sha256': ms.sha(adopted), 'git_commit': self.commit, 'git_blob': oid,
                              'evidence': []},
                  'successor': {'label': 'X1-m', 'sha256': ms.sha(successor_text.encode())},
                  'invariant': ms.INVARIANT, 'change_count': len(listed), 'changes': listed}
        for key, value in overrides.items():
            record[key] = value
        path = self.root / ms.DIRECTORY / 'x.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record))
        return str(path.relative_to(self.root))

    def verify(self, receipt):
        return ms.verify(receipt, self.root, self.root)


class MetadataSuccessorTests(unittest.TestCase):
    def test_exact_property_only_successor_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            receipt = repo.verify(repo.receipt(SUCCESSOR))
            self.assertEqual([(c['reference'], c['property'], c['new']) for c in receipt['changes']],
                             [('R1', 'MPN', 'RC0603FR-071KL'), ('R1', 'Manufacturer', 'YAGEO')])
            found = ms.successor_for(BOARD, ms.sha(SUCCESSOR.encode()), repo.root, repo.root)
            self.assertEqual(found['adopted']['sha256'], ms.sha(ADOPTED.encode()))
            self.assertIsNone(ms.successor_for(BOARD, ms.sha(ADOPTED.encode()), repo.root, repo.root))

    def test_copper_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            moved = SUCCESSOR.replace('(start 0 0)', '(start 0.1 0)')
            with self.assertRaisesRegex(ms.SuccessorError, 'non-property difference'):
                repo.verify(repo.receipt(moved))

    def test_placement_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            with self.assertRaisesRegex(ms.SuccessorError, 'non-property difference'):
                repo.verify(repo.receipt(SUCCESSOR.replace('(at 10 20)', '(at 10 21)', 1)))

    def test_other_property_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            changed = board(footprint('R1', A, 'RC0603FR-071KL', 'YAGEO', value='2k'), footprint('R2', B))
            with self.assertRaisesRegex(ms.SuccessorError, 'non-property difference'):
                repo.verify(repo.receipt(changed))

    def test_extra_property_line_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            extra = SUCCESSOR.replace('\t\t(property "Value"', '\t\t(property "LCSC" "C1"\n\t\t)\n\t\t(property "Value"', 1)
            with self.assertRaisesRegex(ms.SuccessorError, 'line count differs'):
                repo.verify(repo.receipt(extra))

    def test_unlisted_footprint_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            both = board(footprint('R1', A, 'RC0603FR-071KL', 'YAGEO'), footprint('R2', B, 'RC0603FR-071KL', 'YAGEO'))
            listed = ms.derive(ADOPTED.encode(), SUCCESSOR.encode())
            with self.assertRaisesRegex(ms.SuccessorError, 'derived changes differ'):
                repo.verify(repo.receipt(both, changes=listed))

    def test_listed_change_absent_from_bytes_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            listed = ms.derive(ADOPTED.encode(), SUCCESSOR.encode())
            forged = copy.deepcopy(listed) + [{**listed[0], 'reference': 'R2', 'footprint_uuid': B}]
            with self.assertRaisesRegex(ms.SuccessorError, 'derived changes differ'):
                repo.verify(repo.receipt(SUCCESSOR, changes=forged))
            wrong = copy.deepcopy(listed)
            wrong[0]['new'] = 'RC0603FR-072KL'
            with self.assertRaisesRegex(ms.SuccessorError, 'derived changes differ'):
                repo.verify(repo.receipt(SUCCESSOR, changes=wrong))

    def test_wrong_successor_or_adopted_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            with self.assertRaisesRegex(ms.SuccessorError, 'not the receipt successor'):
                repo.verify(repo.receipt(SUCCESSOR, successor={'label': 'X1-m', 'sha256': '0' * 64}))
            path = repo.receipt(SUCCESSOR)
            record = json.loads((repo.root / path).read_text())
            record['adopted']['sha256'] = '0' * 64
            (repo.root / path).write_text(json.dumps(record))
            with self.assertRaisesRegex(ms.SuccessorError, 'not the adopted board'):
                repo.verify(path)
            record['adopted']['sha256'] = ms.sha(ADOPTED.encode())
            record['adopted']['git_commit'] = '0' * 40
            (repo.root / path).write_text(json.dumps(record))
            with self.assertRaisesRegex(ms.SuccessorError, 'absent from Git'):
                repo.verify(path)

    def test_working_bytes_must_be_the_successor(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            path = repo.receipt(SUCCESSOR)
            (repo.root / BOARD).write_text(SUCCESSOR.replace('YAGEO', 'YAGE0'))
            with self.assertRaisesRegex(ms.SuccessorError, 'not the receipt successor'):
                repo.verify(path)

    def test_adopted_bytes_come_from_git_not_the_working_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            path = repo.receipt(SUCCESSOR)
            git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', '-c', 'commit.gpgsign=false']
            moved = ADOPTED.replace('(start 0 0)', '(start 5 0)')
            (repo.root / BOARD).write_text(moved)
            subprocess.run(git + ['commit', '-q', '-am', 'move'], cwd=repo.root, check=True)
            record = json.loads((repo.root / path).read_text())
            record['adopted']['git_commit'] = 'HEAD'
            (repo.root / path).write_text(json.dumps(record))
            (repo.root / BOARD).write_text(SUCCESSOR)
            with self.assertRaisesRegex(ms.SuccessorError, 'not the adopted board'):
                repo.verify(path)

    def test_visible_or_non_footprint_property_change_is_rejected(self):
        visible_old = ADOPTED.replace('\t\t\t(hide yes)\n', '', 4)
        visible_new = SUCCESSOR.replace('\t\t\t(hide yes)\n', '', 4)
        with self.assertRaisesRegex(ms.SuccessorError, 'not hidden'):
            ms.derive(visible_old.encode(), visible_new.encode())
        loose = '(kicad_pcb\n\t(setup\n\t\t(property "MPN" "a"\n\t\t)\n\t)\n)\n'
        with self.assertRaisesRegex(ms.SuccessorError, 'outside a footprint'):
            ms.derive(loose.encode(), loose.replace('"a"', '"b"').encode())

    def test_count_and_invariant_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Repo(temp)
            with self.assertRaisesRegex(ms.SuccessorError, 'count or invariant'):
                repo.verify(repo.receipt(SUCCESSOR, change_count=99))

    def test_committed_receipts_verify_against_git(self):
        paths = ms.receipts()
        self.assertEqual({json.loads((ms.ROOT / p).read_text())['board'] for p in paths}, {
            'boards/osc-core/osc-core.kicad_pcb', 'boards/osc-jack-left/osc-jack-left.kicad_pcb',
            'boards/osc-jack-right/osc-jack-right.kicad_pcb', 'boards/osc-stage-optical/osc-stage-optical.kicad_pcb',
            'boards/osc-control/osc-control-routed-draft.kicad_pcb'})
        for path in paths:
            with self.subTest(receipt=path):
                receipt = ms.verify(path)
                self.assertEqual(set(c['property'] for c in receipt['changes']) - set(ms.PROPERTIES), set())


if __name__ == '__main__':
    unittest.main()
