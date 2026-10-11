"""Small byte fixtures exercise transport rejection; never native acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("transport", Path(__file__).with_name("transport_original.py"))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = bytes(range(251)) * 9
        self.digest = hashlib.sha256(self.data).hexdigest()
        self.source = self.root / "input.zip"
        self.source.write_bytes(self.data)
        self.parts = self.root / "parts"
        self.target = self.root / "output.zip"
        self.manifest = t.split(self.source, self.parts, len(self.data), self.digest, 512)

    def assemble(self):
        t.join(self.parts, self.target, len(self.data), self.digest, 512)

    def change(self, callback):
        callback(self.manifest)
        (self.parts / "manifest.json").write_text(json.dumps(self.manifest))

    def test_roundtrip(self):
        self.assemble()
        self.assertEqual(self.target.read_bytes(), self.data)

    def test_partial_source_rejected_before_split(self):
        self.source.write_bytes(self.data[:-1])
        with self.assertRaises(ValueError):
            t.split(self.source, self.root / "bad", len(self.data), self.digest, 512)
        self.assertFalse((self.root / "bad").exists())

    def test_wrong_whole_hash_rejected(self):
        with self.assertRaises(ValueError):
            t.split(self.source, self.root / "bad", len(self.data), "0" * 64, 512)

    def test_chunk_corruption(self):
        (self.parts / "original.part000").write_bytes(b"x" * 512)
        with self.assertRaises(ValueError):
            self.assemble()
        self.assertFalse(self.target.exists())

    def test_reordered_chunks(self):
        self.change(lambda m: m["chunks"].reverse())
        with self.assertRaises(ValueError):
            self.assemble()

    def test_missing_chunk(self):
        self.change(lambda m: m["chunks"].pop())
        with self.assertRaises(ValueError):
            self.assemble()

    def test_path_substitution(self):
        self.change(lambda m: m["chunks"][0].update(name="../input.zip"))
        with self.assertRaises(ValueError):
            self.assemble()

    def test_identity_substitution(self):
        self.change(lambda m: m.update(artifact_id=1))
        with self.assertRaises(ValueError):
            self.assemble()

    def test_existing_partial_preserved(self):
        partial = self.target.with_suffix(".zip.partial")
        partial.write_bytes(b"other work")
        with self.assertRaises(FileExistsError):
            self.assemble()
        self.assertEqual(partial.read_bytes(), b"other work")

    def test_self_consistent_chunk_tamper_still_fails_whole_hash(self):
        path = self.parts / "original.part000"
        path.write_bytes(b"x" * 512)
        self.change(lambda m: m["chunks"][0].update(sha256=t.sha(path)))
        with self.assertRaises(ValueError):
            self.assemble()
        self.assertFalse(self.target.exists())
        self.assertFalse(self.target.with_suffix(".zip.partial").exists())


if __name__ == "__main__":
    unittest.main()
