"""Current jack source/native binding rejects changed physical and native inputs."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.pcbgen import jack_white_current_binding as binding
from scripts.pcbgen.netlist import read_netlist


ROOT = Path(__file__).resolve().parents[2]


class JackWhiteCurrentBindingTest(unittest.TestCase):
    def view(self, side, modified=None):
        bid='osc-jack-'+side
        receipt=json.loads((ROOT/'.circuit-cache/issue38-recovery/white-current-boards'/bid/'current-native-receipt-v6.json').read_bytes())
        old=json.loads((ROOT/'.circuit-cache/issue38-recovery'/('surface140' if side=='left' else 'right-surface140')/'parallel-native-receipt.json').read_bytes())
        names=set(receipt['source_sha256']) | {name.removeprefix('/work/') for name in old['artifact_sha256']}
        names.add('design/boards/'+bid+'.json')
        names.add('schematic/boards/'+bid+'.net')
        names.add('schematic/boards/'+bid+'.kicad_sch')
        components,_=read_netlist(ROOT/'schematic/boards'/(bid+'.net'))
        names.update('boards/'+bid+'/'+dict(component.fields)['Sheetfile'] for component in components)
        names.add('scripts/pcbgen/netlist.py')
        names.add('design/partition/jack-white-current/schematic-source-sha256.json')
        names.update(json.loads((ROOT/'design/partition/jack-white-current/schematic-source-sha256.json').read_text())[bid])
        folder=tempfile.TemporaryDirectory(dir=ROOT/'.circuit-cache')
        view=Path(folder.name)
        for name in names:
            source=ROOT/name;target=view/name
            target.parent.mkdir(parents=True,exist_ok=True)
            if name==modified:target.write_bytes(source.read_bytes())
            else:target.symlink_to(source)
        return folder,view

    def test_actual_positive_and_wrong_board_companion_drc(self):
        for side,own,total in (('left',1070,1177),('right',896,1005)):
            with self.subTest(side=side):
                folder,view=self.view(side)
                with folder,patch.object(binding,'ROOT',view):
                    result=binding.verify(side)
                    self.assertEqual((result['own_AGND_connected_count'],result['all_source_AGND_connected_count']),(own,total))
                bid='osc-jack-'+side
                candidate=f'boards/{bid}/{bid}-white-current-v1.kicad_pcb'
                folder,view=self.view(side,candidate)
                with folder,patch.object(binding,'ROOT',view):
                    with (view/candidate).open('ab') as handle:handle.write(b'\n')
                    with self.assertRaisesRegex(ValueError,'source pad revision'):binding.verify(side)
                companion=f'boards/{bid}/{bid}-white-current-v1.kicad_pro'
                folder,view=self.view(side,companion)
                with folder,patch.object(binding,'ROOT',view):
                    with (view/companion).open('ab') as handle:handle.write(b'\n')
                    with self.assertRaisesRegex(ValueError,'companion differs'):binding.verify(side)
                drc=f'.circuit-cache/issue38-recovery/white-current-boards/{bid}/native-drc.json'
                folder,view=self.view(side,drc)
                with folder,patch.object(binding,'ROOT',view):
                    report=json.loads((view/drc).read_text());report['source']='wrong-board.kicad_pcb'
                    (view/drc).write_text(json.dumps(report))
                    with self.assertRaisesRegex(ValueError,'native DRC'):binding.verify(side)

    def test_sheet_exporter_and_mid_check_mutation(self):
        side='left';bid='osc-jack-left'
        components,_=read_netlist(ROOT/'schematic/boards'/(bid+'.net'))
        sheet='boards/'+bid+'/'+sorted({dict(c.fields)['Sheetfile'] for c in components})[0]
        folder,view=self.view(side,sheet)
        with folder,patch.object(binding,'ROOT',view):
            with (view/sheet).open('ab') as handle:handle.write(b'\n')
            with self.assertRaisesRegex(ValueError,'frozen source manifest'):binding.verify(side)
        exporter='scripts/pcbgen/extract_power_geometry.py'
        folder,view=self.view(side,exporter)
        with folder,patch.object(binding,'ROOT',view):
            with (view/exporter).open('ab') as handle:handle.write(b'\n')
            with self.assertRaisesRegex(ValueError,'geometry exporter differs'):binding.verify(side)
        geometry=f'.circuit-cache/issue38-recovery/white-current-boards/{bid}/native-geometry.json'
        folder,view=self.view(side,geometry)
        original=binding.reconcile_native
        def mutate(*args,**kwargs):
            result=original(*args,**kwargs)
            with (view/geometry).open('ab') as handle:handle.write(b'\n')
            return result
        with folder,patch.object(binding,'ROOT',view),patch.object(binding,'reconcile_native',side_effect=mutate):
            with self.assertRaisesRegex(ValueError,'changed during verification'):binding.verify(side)


if __name__=='__main__':
    unittest.main()
