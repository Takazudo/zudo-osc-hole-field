"""Discover Stage51 additive F3 routing controls."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('stage51_tests',ROOT/'design/architecture-278/implementation/stage51/f3-sense/test_accept.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def load_tests(loader,tests,pattern):return loader.loadTestsFromModule(module)
if __name__=='__main__':unittest.main()
