#!/usr/bin/env python3
"""Run one discovery root without the separately admitted native oracle case."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
ORACLE = ('test_sweep_precision_vendor.PrecisionVendorSweepGate.'
          'test_original_network_returns_nonzero_for_supported_failure')


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


def main():
    directory = Path(sys.argv[1]).as_posix()
    suite = unittest.TestLoader().discover(directory, pattern='test_*.py')
    discovered = list(cases(suite))
    expected = 1 if directory in ('design/spec', 'design/spec/cells') else 0
    actual = sum(case.id() == ORACLE for case in discovered)
    if actual != expected:
        print(f'FAIL: oracle discovery mismatch in {directory}: expected {expected}, found {actual}',
              file=sys.stderr)
        return 2
    selected = []
    for case in discovered:
        if case.id() == ORACLE:
            print('NOT RUN: ' + ORACLE + ' (requires separate native admission)', flush=True)
        else:
            selected.append(case)
    result = unittest.TextTestRunner().run(unittest.TestSuite(selected))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
