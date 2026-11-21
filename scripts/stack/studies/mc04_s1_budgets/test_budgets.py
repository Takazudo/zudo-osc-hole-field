import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('budgets', Path(__file__).with_name('budgets.py'))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)


class Sources(unittest.TestCase):
    def test_parse_sources(self):
        self.assertIsNone(b.parse_sources([]))
        self.assertEqual(b.parse_sources(['a=x.json', 'b=y.json']), {'a': Path('x.json'), 'b': Path('y.json')})
        for bad in (['a'], ['=x'], ['a='], ['a=x', 'a=y']):
            with self.assertRaises(ValueError):
                b.parse_sources(bad)

    def test_given_source_is_recorded_by_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'nets.json'
            p.write_text(json.dumps({'nets': [{'net': '/X/LED_A'}]}))
            out = b.nets_sources({'current': p})
        self.assertEqual(out['current'][1], hashlib.sha256(json.dumps({'nets': [{'net': '/X/LED_A'}]}).encode()).hexdigest())
        self.assertEqual(out['current'][2], [{'net': '/X/LED_A'}])

    def test_pinned_sources_are_enforced(self):
        real = dict(b.NETS)
        k = next(iter(real))
        b.NETS[k] = (real[k][0], '0' * 64)
        try:
            with self.assertRaisesRegex(ValueError, 'changed'):
                b.nets_sources()
        finally:
            b.NETS.clear(); b.NETS.update(real)


if __name__ == '__main__':
    unittest.main()
