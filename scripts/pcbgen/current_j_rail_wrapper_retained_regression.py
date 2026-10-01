"""Current J rail wrapper rejects stale feeds and occupied output stems early."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.pcbgen.solve_rail_volume import run

ROOT=Path(__file__).resolve().parents[2]


class CurrentJRailWrapperTest(unittest.TestCase):
    def test_missing_authority_stale_feed_and_occupied_selected_path(self):
        folder=ROOT/'.circuit-cache/issue38-recovery/white-current-boards/osc-jack-left'
        native=folder/'native-geometry.json';receipt=folder/'current-native-receipt-v6.json'
        current=folder/'current-power-feed-map-v1.json'
        with tempfile.TemporaryDirectory(dir=ROOT/'.circuit-cache') as temporary:
            base=Path(temporary);output=base/'rail.json';stale=base/'stale-feed.json'
            power=json.loads(current.read_bytes());power['board_sha256']='historical-board'
            stale.write_text(json.dumps(power)+'\n')
            with self.assertRaisesRegex(ValueError,'reviewed native v6 receipt'):
                run(native,stale,output,'+12V',2.,.125,2,(0.,0.))
            with self.assertRaisesRegex(ValueError,'exact native derivation'):
                run(native,stale,output,'+12V',2.,.125,2,(0.,0.),receipt)
            self.assertFalse(output.exists())
            occupied=base/'rail-selected-native.json'
            occupied.symlink_to(base/'missing-selected.json')
            with self.assertRaisesRegex(ValueError,'occupies this stem'):
                run(native,current,output,'+12V',2.,.125,2,(0.,0.),receipt)


if __name__=='__main__':unittest.main()
