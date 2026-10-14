"""Focused source/provenance checks; no native runner or routing search."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class CorePilotSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepare = module("prepare")
        cls.replay = module("replay")
        cls.manifest = cls.prepare.prepare()

    def test_pinned_baseline_and_complete_case_identities(self):
        data = self.manifest
        self.assertEqual(data["native_open_edges"], 1402)
        self.assertEqual(data["published_board_sha256"], self.prepare.EXPECTED_BOARD)
        self.assertEqual(data["retained_native_dump_sha256"], self.prepare.EXPECTED_DUMP)
        self.assertEqual(len(data["cases"]), 9)
        for row in data["cases"]:
            self.assertIn(row["source_pad"], row["source_group_pads"])
            self.assertEqual(row["source_pad"]["net"], row["net"])
            self.assertEqual(len(row["source_group_sha256"]), 64)
            self.assertIn("uuid", row["source_pad"])
        self.assertEqual({row["package"] for row in data["cases"] if row["case"] != "filter-reference-return"},
                         {"OPA4197IPWR", "ADG5412FBRUZ"})

    def test_generated_manifest_is_deterministic(self):
        saved = json.loads((HERE / "cases.json").read_text())
        self.assertEqual(saved, self.manifest)

    def test_wrong_dump_fails_before_router_import(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / "dump.json"
            wrong.write_text("{}")
            with self.assertRaisesRegex(ValueError, "full accepted K1402 dump absent"):
                self.replay.replay(wrong, "opa-osc-plus", .025)


if __name__ == "__main__":
    unittest.main()
