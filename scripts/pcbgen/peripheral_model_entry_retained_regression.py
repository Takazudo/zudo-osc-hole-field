import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import peripheral_model_entry as entry

ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/'.circuit-cache/issue38-recovery/optical-ground-prerequisite-v2/native-geometry.json'
RECEIPT=NATIVE.with_name('native-receipt.json')
MANIFEST=ROOT/'design/partition/peripheral-ground-feasibility/optical-ground-v2/osc-stage-optical.receipt.json'


class PeripheralModelEntryTest(unittest.TestCase):
    def test_missing_failed_stale_and_partial_source_rejects(self):
        raw=NATIVE.read_bytes()
        for receipt,manifest,loads,limit in [(None,None,True,0),(RECEIPT,MANIFEST,False,0),(RECEIPT,MANIFEST,True,3)]:
            with self.assertRaises(ValueError):entry.enter(NATIVE,raw,receipt,manifest,loads,limit)
        with self.assertRaisesRegex(ValueError,'dependency changed'):
            entry.enter(NATIVE,raw,RECEIPT,MANIFEST,True,0)
        with tempfile.TemporaryDirectory(dir=ROOT/'.circuit-cache') as folder:
            p=Path(folder)/'receipt.json';r=json.loads(RECEIPT.read_bytes());r['native_model_prerequisite_passed']=False;p.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'bare/failed'):
                entry.enter(NATIVE,raw,p,MANIFEST,True,0)

    def test_actual_complete_faces_reference_and_uuid_mapping(self):
        native=json.loads(NATIVE.read_bytes());r=json.loads(RECEIPT.read_bytes())
        authority={'board_id':native['board_id'],'source_ground_inventory':r['source_ground_inventory'],'named_reference':native['ground_reference']}
        ports=[{'ref':p['ref'],'pad':p['pad'],'kind':'load' if p['kind']=='own_load' else p['kind'],'layer':0 if p['native_layers']==['F.Cu'] else 1} for p in r['source_ground_inventory']['contacts']]
        geometry={'data':native,'ports':ports,'active_sheet_layers':['F.Cu','B.Cu']}
        entry.select_ports(geometry,authority)
        for change in ['missing','duplicate','face','uuid','reference']:
            bad=copy.deepcopy(geometry);a=copy.deepcopy(authority)
            if change=='missing':bad['ports'].pop()
            if change=='duplicate':bad['ports'][0]=bad['ports'][1]
            if change=='face':bad['ports'][0]['layer']=1-bad['ports'][0]['layer']
            if change=='uuid':next(i for i in bad['data']['items'] if i.get('ref')==bad['ports'][0]['ref'] and i.get('pad')==bad['ports'][0]['pad'])['uuid']='wrong'
            if change=='reference':a['named_reference']['pad']='99'
            with self.assertRaises(ValueError,msg=change):entry.select_ports(bad,a)

    def test_actual_positive_and_bound_wrong_board_companion_changes(self):
        import hashlib
        base=ROOT/'.circuit-cache/issue38-recovery/optical-ground-prerequisite-v3'
        source=base/'native-geometry.json';receipt=base/'native-receipt.json'
        authority=entry.enter(source,source.read_bytes(),receipt,MANIFEST,True,0)
        self.assertEqual(authority['source_ground_inventory']['connected_count'],72)
        with tempfile.TemporaryDirectory(dir=ROOT/'.circuit-cache') as folder:
            view=Path(folder)
            for name in authority['dependency_sha256']:
                path=Path(name);dest=view/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
            copied_receipt=view/receipt.relative_to(ROOT);copied_source=view/source.relative_to(ROOT);copied_manifest=view/MANIFEST.relative_to(ROOT)
            with patch.object(entry,'ROOT',view):
                entry.enter(copied_source,copied_source.read_bytes(),copied_receipt,copied_manifest,True,0)
                native=json.loads(copied_source.read_bytes());board=entry.resolve(native['board'])
                for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):
                    path=board.with_suffix(suffix);old=path.read_bytes();path.write_bytes(old+b'\n')
                    with self.assertRaisesRegex(ValueError,'dependency changed'):
                        entry.enter(copied_source,copied_source.read_bytes(),copied_receipt,copied_manifest,True,0)
                    path.write_bytes(old)
                report=json.loads(copied_receipt.read_bytes());drc_key=next(k for k in report['artifacts_sha256'] if k.endswith('/native-drc.json'));drc=entry.resolve(drc_key);d=json.loads(drc.read_bytes());d['source']='wrong-board.kicad_pcb';drc.write_text(json.dumps(d))
                report['artifacts_sha256'][drc_key]=hashlib.sha256(drc.read_bytes()).hexdigest();copied_receipt.write_text(json.dumps(report))
                with self.assertRaisesRegex(ValueError,'actual DRC artifact fails'):
                    entry.enter(copied_source,copied_source.read_bytes(),copied_receipt,copied_manifest,True,0)

    def test_actual_two_foil_extraction_keeps_all_71_functions(self):
        from scripts.pcbgen.ground_volume_geometry import extract
        from scripts.pcbgen.ground_reference import ordered_profiles
        base=ROOT/'.circuit-cache/issue38-recovery/optical-ground-prerequisite-v3'
        source=base/'native-geometry.json'
        authority=entry.enter(source,source.read_bytes(),base/'native-receipt.json',MANIFEST,True,0)
        geometry=extract(source,2.3e-5,refinement=1,include_loads=True,main_strands=False)
        entry.select_ports(geometry,authority)
        mains,reference,ports,profiles,identity=ordered_profiles(geometry,0)
        self.assertEqual(len(mains),0);self.assertEqual(len(ports),71);self.assertEqual(len(profiles),71)
        self.assertEqual((reference['ref'],reference['pad'],reference['physical_layer']),('J900379','2','B.Cu'))
        self.assertEqual(geometry['physical_foil_layers'],['F.Cu','B.Cu'])
        self.assertEqual(len(geometry['barrels']),1)

    def test_generic_driver_cannot_extract_without_native_authority(self):
        from scripts.pcbgen.solve_conductor_volume import solve
        with tempfile.TemporaryDirectory(dir=ROOT/'.circuit-cache') as folder:
            with patch('scripts.pcbgen.solve_conductor_volume.extract',side_effect=AssertionError('must not reach extraction')):
                with self.assertRaisesRegex(ValueError,'successful native receipt'):
                    solve(NATIVE,Path(folder)/'result.json',2.,.25,1,0,include_loads=True)


if __name__=='__main__':unittest.main()
