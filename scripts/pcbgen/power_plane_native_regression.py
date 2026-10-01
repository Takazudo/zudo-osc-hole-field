"""Pinned native ownership regression for source-defined plane replacement."""
import sys
import tempfile
import subprocess
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.route_kicad import ensure_zones
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.source_zones import retire


class PlaneOwnershipTests(unittest.TestCase):
    def test_inner_rule_checks_through_via_and_pth_annuli(self):
        board = pcbnew.BOARD(); board.SetCopperLayerCount(4)
        nets = []
        for name, code in (('A', 1), ('B', 2)):
            net = pcbnew.NETINFO_ITEM(board, name, code); board.Add(net); nets.append(net)
        movable = []
        for index, net in enumerate(nets):
            x = 3+index
            via = pcbnew.PCB_VIA(board); via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(3)))
            via.SetWidth(pcbnew.FromMM(.7)); via.SetDrill(pcbnew.FromMM(.3)); via.SetNet(net); board.Add(via)
            fp = pcbnew.FOOTPRINT(board); fp.SetReference('T'+str(index+1)); board.Add(fp)
            pad = pcbnew.PAD(fp); pad.SetNumber('1'); pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE); pad.SetLayerSet(pcbnew.LSET.AllCuMask())
            pad.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(6)))
            pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(.7), pcbnew.FromMM(.7)))
            pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(.3), pcbnew.FromMM(.3)))
            pad.SetNet(net); fp.Add(pad)
            if index:
                movable.extend((via, pad))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'annuli.kicad_pcb'; report = Path(directory)/'drc.json'
            def violations():
                pcbnew.SaveBoard(str(path), board)
                subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '-o', str(report), str(path)],
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                return [r for r in json.loads(report.read_text())['violations'] if r['type'] == 'clearance']
            self.assertEqual(violations(), [])
            path.with_suffix('.kicad_dru').write_text('(version 1)\n(rule "Thick inner copper" (layer "In1.Cu") (constraint clearance (min 0.35mm)))\n')
            failed = violations()
            self.assertEqual(len(failed), 2)
            self.assertTrue(all('0.3500' in r['description'] or '0.35' in r['description'] for r in failed))
            for item in movable:
                position = item.GetPosition(); position.x += pcbnew.FromMM(.1); item.SetPosition(position)
            self.assertEqual(violations(), [])

    def test_only_matching_owned_zone_can_be_retired(self):
        board = pcbnew.BOARD(); board.SetCopperLayerCount(4)
        net = pcbnew.NETINFO_ITEM(board, 'AGND', 1); board.Add(net)
        old = pcbnew.ZONE(board); old.SetZoneName('pcbgen:fixture:pour:old:F.Cu')
        old.SetUuid(pcbnew.KIID(stable_uuid('fixture', 'pour', 'old:F.Cu')))
        old.SetLayer(pcbnew.F_Cu); old.SetNet(net); board.Add(old)
        owner = pcbnew.ZONE(board); owner.SetZoneName('owner geometry')
        owner.SetLayer(pcbnew.B_Cu); owner.SetNet(net); board.Add(owner)
        owner_uid = owner.m_Uuid.AsString()
        for zone in (old, owner):
            outline = zone.Outline(); index = outline.NewOutline()
            for x, y in ((0, 0), (10, 0), (10, 10), (0, 10)):
                outline.Append(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), index)
        definition = SimpleNamespace(outline=((0, 0), (10, 0), (10, 10), (0, 10)), routing={'zones': [
            {'name': 'new', 'net': 'AGND', 'layers': ['In1.Cu'], 'clearance_mm': .35,
             'min_thickness_mm': .35, 'pad_connection': 'full'}]})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.kicad_pcb'
            pcbnew.SaveBoard(str(path), board)
            filtered, retired = retire(path.read_text(), 'fixture', definition.routing)
            path.write_text(filtered)
            board = pcbnew.LoadBoard(str(path))
        created, managed = ensure_zones(board, 'fixture', definition)
        managed.update(retired)
        self.assertEqual({z.GetZoneName() for z in board.Zones()}, {'owner geometry', 'pcbgen:fixture:pour:new:In1.Cu'})
        self.assertIn(owner_uid, {z.m_Uuid.AsString() for z in board.Zones()})
        self.assertEqual(len(created), 1)
        self.assertEqual(len(managed), 2)


if __name__ == '__main__':
    unittest.main()
