"""Current J rail admission binds an exact original native and selected role."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.pcbgen.current_j_rail_entry import enter,digest
from scripts.pcbgen.selected_conductor_export import select

ROOT=Path(__file__).resolve().parents[2]


class CurrentJRailEntryTest(unittest.TestCase):
    def test_exact_current_jl_rail_and_wrong_role(self):
        folder=ROOT/'.circuit-cache/issue38-recovery/white-current-boards/osc-jack-left'
        source=folder/'native-geometry.json';receipt=folder/'current-native-receipt-v6.json'
        raw=source.read_bytes()
        selected=(json.dumps(select(json.loads(raw),'+12V',digest(raw)),separators=(',',':'))+'\n').encode()
        with tempfile.TemporaryDirectory(dir=ROOT/'.circuit-cache') as directory:
            path=Path(directory)/'selected.json';path.write_bytes(selected)
            report=enter(path,selected,source,receipt,'+12V',True,0,True)
            self.assertEqual(len(report['expected_load_contacts']),271)
            self.assertEqual(report['main_contact']['ref'],'TP990001')
            self.assertEqual(report['physical_net'],'+12V')
            with self.assertRaisesRegex(ValueError,'complete J rail basis'):
                enter(path,selected,source,receipt,'+12V',True,1,True)
            with self.assertRaisesRegex(ValueError,'relabeling'):
                enter(path,selected,source,receipt,'-12V',True,0,True)
            changed=selected.replace(b'"board_id":"osc-jack-left"',b'"board_id":"osc-jack-right"',1)
            with self.assertRaises(ValueError):enter(path,changed,source,receipt,'+12V',True,0,True)


if __name__=='__main__':unittest.main()
