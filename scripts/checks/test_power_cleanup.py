"""Stage54 power cleanup source/accounting/native-evidence controls."""
from pathlib import Path
import importlib.util,unittest
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('stage54_tests',ROOT/'design/architecture-278/implementation/stage54/power-cleanup/test_cleanup.py');module=importlib.util.module_from_spec(s);s.loader.exec_module(module)
def load_tests(loader,tests,pattern):return loader.loadTestsFromModule(module)
if __name__=='__main__':unittest.main()
