"""Include Stage45 source inventory checks in the repository suite."""
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('stage45_tests', ROOT / 'design/architecture-278/implementation/stage45/connectivity-inventory/test_inventory.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromModule(module)


if __name__ == '__main__': unittest.main()
