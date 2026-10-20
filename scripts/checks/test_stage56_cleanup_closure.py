"""Stage56 cleanup-closure candidate schematic/field-sync/decoupling/native-evidence controls."""
from pathlib import Path
import importlib.util,unittest
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('stage56_tests',ROOT/'design/architecture-278/implementation/stage56/cleanup-closure/test_stage56.py');module=importlib.util.module_from_spec(s);s.loader.exec_module(module)
def load_tests(loader,tests,pattern):return loader.loadTestsFromModule(module)
if __name__=='__main__':unittest.main()
