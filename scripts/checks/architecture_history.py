"""Run retained checkpoint assertions in their original source context.

All other architecture tests use the current checkout. Historical test/source
bytes are never patched, and current retained evidence must match the snapshots.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest

DIRECTORY = 'scripts/architecture278/implementation'
CURRENT_BASE = 'ed3a66125fb48e7777a73a7572fbc7afd2debe2f'
CHECKPOINTS = {
    'e2e580aed4620e86357341d660bbf04f356d33f2': (
        'test_stage18_observation.py', 'test_stage20_observation.py'),
    'f30d653e733a85fe00b1c187a5f571a983a3b47a': ('test_stage25_correction.py',),
    '0c1871791a866ba3de64472cac360b81f9cb90ab': ('test_stage28_din_harness.py',),
    '00266037a7e2134c9c6c70d1ae95695932e7f1f6': ('test_stage29_din_column_reversal.py',),
    '698d91398db411d94117a4298810b1bd58f38d61': ('test_stage30_din_design_integration.py',),
    '2c41e8cd93574c356ba375fafba47ba65a480217': ('test_stage33_large_radius.py',),
    '9d9aa404a27dc7e5b8476e0d9f826fc44c517fbe': ('test_stage34_arch_retention.py',),
}
# These known later updates are current-context inputs, not rewritten history.
# Pin their working bytes to the reviewed pre-repair checkout, rather than grant
# an open-ended exemption from preservation checks.
CURRENT_PATHS = (
    '.github/workflows/check.yml',
    'boards/panel/reports/visual-review.md',
    'design/architecture-278/implementation/README.md',
    'design/architecture-278/implementation/WORK.md',
    'doc/src/content/docs/architecture/osc-panel.mdx',
    'doc/src/content/docs/project/next-actions.mdx',
    'project/osc-hole-field/workbench/README.md',
    'project/osc-hole-field/workbench/src/render.js',
    'scripts/architecture278/implementation/check_source.py',
    'scripts/panel/export_art.cjs',
)
# Only this repair's entrypoint and boundary documentation evolve here.
ADAPTER_PATHS = ('scripts/checks/run-python-tests.sh', 'scripts/pcbgen/TEST-BOUNDARY.md')


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True)


def verify_binding(root, commit, modules, current_base=CURRENT_BASE,
                   current_paths=CURRENT_PATHS, adapter_paths=ADAPTER_PATHS):
    for revision in (commit, current_base):
        if not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise ValueError('Expected immutable full commit: ' + revision)
        git(root, 'rev-parse', '--verify', revision + '^{commit}')
        subprocess.run(['git', 'merge-base', '--is-ancestor', revision, 'HEAD'],
                       cwd=root, check=True)
    changed = set(git(root, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames',
                      '--name-only', '--diff-filter=DMRTUXB', commit, '--').splitlines())
    bad = changed - set(current_paths) - set(adapter_paths)
    if bad:
        raise ValueError('Retained checkpoint bytes changed: ' + ', '.join(sorted(bad)))
    if current_paths:
        drift = git(root, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames',
                    '--name-only', current_base, '--', *current_paths).splitlines()
        if drift:
            raise ValueError('Current-context binding changed: ' + ', '.join(drift))
    for path in (*current_paths, *adapter_paths, *(DIRECTORY + '/' + m for m in modules)):
        if not (root / path).is_file() or (root / path).is_symlink():
            raise ValueError('Missing or redirected bound file: ' + path)
    for module in modules:
        git(root, 'cat-file', '-e', commit + ':' + DIRECTORY + '/' + module)


def replay(root, commit, modules):
    count = 0
    flags = ['-O'] if sys.flags.optimize else []
    with tempfile.TemporaryDirectory(prefix='osc-ci-history-') as temp:
        checkout = Path(temp) / 'checkpoint'
        subprocess.run(['git', 'worktree', 'add', '--quiet', '--detach', str(checkout), commit],
                       cwd=root, check=True)
        try:
            for module in modules:
                print(f'Frozen checkpoint {commit}: {module}', flush=True)
                result = subprocess.run(
                    [sys.executable, *flags, '-m', 'unittest', 'discover',
                     '-s', DIRECTORY, '-p', module], cwd=checkout,
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
                print(result.stdout, end='', flush=True)
                result.check_returncode()
                counts = re.findall(r'^Ran (\d+) tests? in ', result.stdout, re.MULTILINE)
                if len(counts) != 1 or int(counts[0]) == 0:
                    raise ValueError('No unambiguous executed test count: ' + module)
                count += int(counts[0])
        finally:
            subprocess.run(['git', 'worktree', 'remove', '--force', str(checkout)],
                           cwd=root, check=True)
    return count


class CurrentLoader(unittest.TestLoader):
    def __init__(self, frozen):
        super().__init__()
        self.frozen = set(frozen)

    def _match_path(self, path, full_path, pattern):
        return path not in self.frozen and super()._match_path(path, full_path, pattern)


def main():
    root = Path.cwd()
    started = time.monotonic()
    frozen = [module for modules in CHECKPOINTS.values() for module in modules]
    if len(frozen) != len(set(frozen)):
        raise ValueError('Duplicate checkpoint module')
    # Validate every binding before any test can mutate disposable fixtures.
    for commit, modules in CHECKPOINTS.items():
        verify_binding(root, commit, modules)
    total = sum(replay(root, commit, modules) for commit, modules in CHECKPOINTS.items())
    print('Current-source architecture discovery (all unmapped modules)', flush=True)
    suite = CurrentLoader(frozen).discover(DIRECTORY)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    total += result.testsRun
    print(f'Ran {total} tests in {time.monotonic() - started:.3f}s (frozen + current)', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
