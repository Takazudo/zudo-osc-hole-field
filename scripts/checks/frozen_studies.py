"""Replay superseded study tests unchanged at the last commit where they passed.

Some retained studies assert that current canonical bytes still equal the
revision they studied. A later adopted change (named in `superseded_by`) made
that false on purpose, so each such test runs in a disposable worktree at the
parent of that change instead of against the current tree. The test bytes must
be identical at HEAD and at the pinned commit; nothing is skipped or edited.

  frozen_studies.py replay        run every pinned entry in its worktree
  frozen_studies.py discover DIR  current-tree discovery of DIR without pinned modules
"""
from collections import defaultdict
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / 'scripts/checks/frozen-studies.json'
FULL = re.compile(r'[0-9a-f]{40}')


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True)


def load(path=REGISTRY):
    data = json.loads(Path(path).read_text())
    entries = data['studies']
    seen = set()
    for entry in entries:
        if entry['path'] in seen:
            raise ValueError('Duplicate frozen study: ' + entry['path'])
        seen.add(entry['path'])
        if set(entry) - {'path', 'runner', 'commit', 'superseded_by', 'reason'}:
            raise ValueError('Unknown frozen study field: ' + entry['path'])
        if not entry.get('reason'):
            raise ValueError('Frozen study needs a recorded reason: ' + entry['path'])
    return entries


def verify(entry, root=ROOT):
    """The pin is the first parent of an adopted HEAD ancestor, and the test is unedited."""
    commit, later = entry['commit'], entry['superseded_by']
    for revision in (commit, later):
        if not FULL.fullmatch(revision):
            raise ValueError('Expected immutable full commit: ' + revision)
    subprocess.run(['git', 'merge-base', '--is-ancestor', later, 'HEAD'], cwd=root, check=True)
    if git('rev-parse', later + '^1', cwd=root).strip() != commit:
        raise ValueError('Pinned commit is not the first parent of superseded_by: ' + entry['path'])
    paths = [entry['path']] + ([entry['runner']] if 'runner' in entry else [])
    for path in paths:
        if not (root / path).exists():
            raise ValueError('Missing pinned test path: ' + path)
        if subprocess.run(['git', 'diff', '--quiet', commit, '--', path], cwd=root).returncode:
            raise ValueError('Pinned test bytes differ from their frozen commit: ' + path)
    if 'runner' not in entry and not Path(entry['path']).name.startswith('test_'):
        raise ValueError('Module entry must name a test_*.py file: ' + entry['path'])


def command(entry):
    if 'runner' in entry:
        return [sys.executable, entry['runner']]
    path = Path(entry['path'])
    return [sys.executable, '-m', 'unittest', 'discover', '-s', str(path.parent), '-p', path.name]


def replay(entries, root=ROOT):
    for entry in entries:
        verify(entry, root)
    total = 0
    groups = defaultdict(list)
    for entry in entries:
        groups[entry['commit']].append(entry)
    for commit, members in sorted(groups.items()):
        with tempfile.TemporaryDirectory(prefix='osc-frozen-study-') as temp:
            checkout = Path(temp) / 'checkpoint'
            subprocess.run(['git', 'worktree', 'add', '--quiet', '--detach', str(checkout), commit],
                           cwd=root, check=True)
            try:
                for entry in members:
                    print(f"Frozen study {entry['path']} at {commit[:12]} "
                          f"(superseded by {entry['superseded_by'][:12]})", flush=True)
                    result = subprocess.run(command(entry), cwd=checkout, text=True,
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            timeout=1500)
                    print(result.stdout, end='', flush=True)
                    result.check_returncode()
                    counts = re.findall(r'^Ran (\d+) tests? in ', result.stdout, re.MULTILINE)
                    if not counts or int(counts[-1]) == 0:
                        raise ValueError('No executed test count: ' + entry['path'])
                    total += int(counts[-1])
            finally:
                subprocess.run(['git', 'worktree', 'remove', '--force', str(checkout)],
                               cwd=root, check=True)
    print(f'Ran {total} tests in frozen study worktrees', flush=True)
    return total


class CurrentLoader(unittest.TestLoader):
    def __init__(self, pinned):
        super().__init__()
        self.pinned = set(pinned)

    def _match_path(self, path, full_path, pattern):
        return Path(full_path).resolve() not in self.pinned and super()._match_path(path, full_path, pattern)


def discover(directory, entries, root=ROOT):
    target = (root / directory).resolve()
    for entry in entries:
        if 'runner' in entry and (root / entry['path']).resolve() == target:
            print(f"Replayed at {entry['commit'][:12]} by frozen_studies.py replay: {directory}")
            print('Ran 0 tests in 0.000s')
            return 0
    pinned = {(root / e['path']).resolve() for e in entries if 'runner' not in e}
    remaining = [p for p in target.rglob('test_*.py') if p.resolve() not in pinned]
    if not remaining:
        print(f'All test modules under {directory} are replayed as frozen studies')
        print('Ran 0 tests in 0.000s')
        return 0
    suite = CurrentLoader(pinned).discover(str(target), pattern='test_*.py', top_level_dir=str(target))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv):
    entries = load()
    if argv[:1] == ['replay'] and len(argv) == 1:
        replay(entries)
        return 0
    if argv[:1] == ['discover'] and len(argv) == 2:
        # Match `python -m unittest discover -s DIR`: the working directory, not this script's folder.
        sys.path[0] = str(Path.cwd())
        sys.path.insert(0, str((ROOT / argv[1]).resolve()))
        return discover(argv[1], entries)
    raise SystemExit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
