"""Synthetic descriptor-only characterization; never access retained originals."""
import gc
import hashlib
import json
import pickle
import tempfile
import unittest
import weakref
from pathlib import Path
from unittest.mock import patch
from test_attribution_preallocation import descriptors, DescriptorArray
import attribution_characterization as C
from attribution_transport import Budget
import attribution_preallocation as G


def binding(path, value):
    data = pickle.dumps(value); path.write_bytes(data)
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'decoded_limit': len(data), 'format': 'pickle', 'gzip': False}


class CharacterizationTests(unittest.TestCase):
    def test_serial_transport_and_bound_excess(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); ops={'KA': descriptors(), 'KB': descriptors(sizes=(5000,))}
            bindings={k:binding(root/k,v) for k,v in ops.items()}
            refs=[]; real=C.decode
            def observe(b,budget):
                gc.collect(); self.assertTrue(all(r() is None for r in refs))
                op=real(b,budget); refs.append(weakref.ref(op['Kg_face'])); return op
            budget=Budget(); start=budget.started; deadline=budget.deadline
            with patch.object(C,'decode',side_effect=observe):r=C.characterize(bindings,root/'result',budget)
            self.assertTrue(all(x() is None for x in refs));self.assertEqual(r['status'],'COMPLETE')
            self.assertEqual((budget.started,budget.deadline),(start,deadline))
            self.assertEqual(r['summary']['purpose'],'CHARACTERIZATION_ONLY')
            self.assertFalse(r['electrical_acceptance'])
            rows=[json.loads(x) for x in (root/'result/components.jsonl').read_text().splitlines()]
            self.assertEqual(rows[0]['raw_coordinate_upper'],31)
            self.assertEqual(rows[1]['raw_bound_outcome'],'EXCEEDS_RAW_BOUND')
            self.assertEqual(rows[1]['full_pipeline_qualification'],'NOT_QUALIFIED')
            old=G.construction_bounds(G.extract_metadata(ops['KA'],lambda:None),G.MAX_RAW_ENTRIES)
            self.assertEqual(rows[0]['named_array_bytes'],old['named_array_bytes'])
            self.assertLess(budget.used,2*C.MAX_ROW_BYTES+C.MAX_SUMMARY_BYTES+4096)
    def test_second_decode_failure_releases_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); bindings={k:binding(root/k,descriptors()) for k in ('KA','KB')}
            bindings['KB']['sha256']='0'*64
            with self.assertRaises(ValueError):C.characterize(bindings,root/'out',Budget())
            receipt=json.loads((root/'out/terminal.json').read_text())
            self.assertEqual(receipt['status'],'INCOMPLETE');self.assertEqual(receipt['component_rows'],1)
            self.assertFalse((root/'out/components.jsonl').exists())
    def test_metadata_failure_releases_operator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); bindings={k:binding(root/k,descriptors()) for k in ('KA','KB')};refs=[]
            def bad(*args):
                op=descriptors();refs.append(weakref.ref(op['Kg_face']));op['N']=0;return op
            with patch.object(C,'decode',side_effect=bad):
                with self.assertRaises(ValueError):C.characterize(bindings,root/'out',Budget())
            self.assertTrue(all(r() is None for r in refs))
    def test_checkpoint_and_output_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);bindings={k:binding(root/k,descriptors()) for k in ('KA','KB')}
            with patch.object(C,'MAX_CHECKPOINTS',1):
                with self.assertRaisesRegex(ValueError,'checkpoint ceiling'):C.characterize(bindings,root/'visits',Budget())
            with patch.object(C,'MAX_ROW_BYTES',1):
                with self.assertRaisesRegex(ValueError,'row output ceiling'):C.characterize(bindings,root/'output',Budget())
            budget=Budget();budget.cancelled=True
            with patch.object(C,'decode') as decode:
                with self.assertRaisesRegex(ValueError,'CANCELLED'):C.characterize(bindings,root/'cancel',budget)
                decode.assert_not_called()
    def test_binding_schema_and_no_unrequested_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);bindings={k:binding(root/k,descriptors()) for k in ('KA','KB')}
            bindings['mesh']=bindings['KA']
            with patch.object(C,'decode') as decode:
                with self.assertRaises(ValueError):C.characterize(bindings,root/'out',Budget())
                decode.assert_not_called()

if __name__=='__main__':unittest.main()
