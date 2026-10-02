import copy
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from scripts.pcbgen.generate_peripheral_ground import generate,source_contacts
from scripts.pcbgen.peripheral_project_source import derive,fresh_sync_project
from scripts.pcbgen.native_companion_binding import verify
from scripts.pcbgen.peripheral_source_epoch import (derive as derive_epoch, prove_display_only,
    prove_power_metadata_only, prove_octave_routing_only, historical, IO, FP, OUTPUT,
    METADATA_BASE, ROUTING_BASE, ROUTING, CONTRACT, SUPPLY)
import hashlib

BASE=Path('design/partition/peripheral-ground-feasibility')


class PeripheralGroundSourceTests(unittest.TestCase):
    def test_all_fixed_sources_and_independent_contacts(self):
        proposal=json.loads((BASE/'proposal.json').read_bytes())
        epoch=json.loads(OUTPUT.read_bytes())
        epochs={row['board_id']:row for row in epoch['boards']}
        self.assertEqual(set(epochs),{row['board_id'] for row in proposal['boards']})
        with tempfile.TemporaryDirectory() as folder:
            for row in proposal['boards']:
                path=Path(folder)/(row['board_id']+'.json');receipt=generate(BASE/'proposal.json',row['board_id'],path)
                original=json.loads(Path('design/boards',path.name).read_bytes());current=json.loads(path.read_bytes())
                self.assertEqual({k:v for k,v in original.items() if k not in ('stackup','routing')},
                    {k:v for k,v in current.items() if k not in ('stackup','routing')})
                # Preserve historical receipts: source equivalence is separate
                # from native/model admission and never rewrites their hashes.
                historic_bytes=(BASE/(row['board_id']+'.receipt.json')).read_bytes()
                historic=json.loads(historic_bytes);bound=epochs[row['board_id']]
                self.assertEqual(hashlib.sha256(historic_bytes).hexdigest(),bound['historical_receipt_sha256'])
                self.assertEqual(hashlib.sha256(path.with_suffix('.receipt.json').read_bytes()).hexdigest(),bound['current_source_receipt_sha256'])
                self.assertEqual(receipt['definition_sha256'],bound['unchanged_definition_sha256'])
                changes={'design/partition/partition.json','design/reports/io-partition.json'}
                if row['board_id'].startswith('osc-octave-'):changes.add('design/boards/'+path.name)
                self.assertEqual(set(bound['source_changes']),changes)
                expected=copy.deepcopy(historic)
                for source,change in bound['source_changes'].items():
                    self.assertEqual(expected['source_sha256'][source],change['historical'])
                    self.assertEqual(hashlib.sha256(Path(source).read_bytes()).hexdigest(),change['current'])
                    expected['source_sha256'][source]=change['current']
                self.assertEqual(receipt,expected)
                self.assertEqual(len(receipt['source_packages']),row['footprints'])
                self.assertEqual(len(receipt['own_ground_contacts'])+len(receipt['GH_ground_contacts']),72 if row['board_key']=='EL' else 7)
                self.assertFalse(receipt['model_entry_allowed'])
        partition=json.loads(Path(proposal['partition']).read_bytes());io=json.loads(Path(proposal['io']).read_bytes())
        changed=copy.deepcopy(partition);changed['connectors'].append(next(h for h in changed['connectors'] if h['board']=='O1'))
        with self.assertRaisesRegex(ValueError,'duplicate source header'):
            source_contacts('osc-octave-1','O1',changed,io)

    def test_epoch_chain_is_reproducible_and_display_proof_rejects_geometry_changes(self):
        self.assertEqual(json.loads(OUTPUT.read_bytes()), derive_epoch())
        old_io, new_io = historical(IO), historical(IO, METADATA_BASE)
        old_fp, new_fp = historical(FP), historical(FP, METADATA_BASE)
        prove_display_only(old_io, new_io, old_fp, new_fp)
        with self.assertRaisesRegex(ValueError, '2D footprint geometry changed'):
            prove_display_only(old_io, new_io, old_fp, new_fp + b'\n')
        changed = json.loads(new_io)
        changed['physical_packages'][0]['courtyard']['width_mm'] += 1
        with self.assertRaisesRegex(ValueError, 'beyond the U6101'):
            prove_display_only(old_io, json.dumps(changed).encode(), old_fp, new_fp)
        with self.assertRaisesRegex(ValueError, 'historical footprint hash mismatch'):
            prove_display_only(old_io, new_io, new_fp, new_fp)

    def test_metadata_comparison_rejects_geometry_connectivity_and_wrong_currents(self):
        old_io, new_io = historical(IO, METADATA_BASE), Path(IO).read_bytes()
        contract, supply = json.loads(Path(CONTRACT).read_bytes()), json.loads(Path(SUPPLY).read_bytes())
        prove_power_metadata_only(old_io, new_io, contract, supply)
        for kind in ['geometry', 'pin', 'current', 'package']:
            with self.subTest(kind=kind):
                changed = json.loads(new_io)
                if kind == 'geometry':
                    changed['physical_packages'][0]['courtyard']['width_mm'] += .001
                elif kind == 'pin':
                    changed['allowed_crossings'][0]['members'][0]['pin'] = 'WRONG'
                elif kind == 'current':
                    row = next(r for r in changed['allowed_crossings'] if r['net']=='AGND')
                    row['current_mA']['whole_domain_maximum_return_magnitude'] = 4400
                else:
                    changed['current_repacking_added_packages']['packages'].pop()
                with self.assertRaisesRegex(ValueError, 'beyond the exact power/package'):
                    prove_power_metadata_only(old_io, json.dumps(changed).encode(), contract, supply)

    def test_metadata_epoch_requires_unchanged_supply_source(self):
        def changed_snapshot(path, commit=None):
            if path == CONTRACT and commit == METADATA_BASE:
                return b'{}\n'
            return historical(path) if commit is None else historical(path, commit)
        with patch('scripts.pcbgen.peripheral_source_epoch.historical', side_effect=changed_snapshot):
            with self.assertRaisesRegex(ValueError, 'supply source changed'):
                derive_epoch()

    def test_source_bridge_accounting_and_invalid_declaration(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            proposal=BASE/'optical-ground-v2/proposal.json'
            for bid,count in [('osc-stage-optical',1),('osc-octave-1',0)]:
                r=generate(proposal,bid,folder/(bid+'.json'))
                self.assertEqual(r['source_added_copper'],{'tracks':0,'vias':count,'keepout_exceptions':0})
                self.assertEqual(r['no_added_tracks_vias_or_exceptions'],count==0)
            altered=json.loads(proposal.read_bytes());altered['source_ground_bridge']['net']='+5V'
            wrong=folder/'wrong.json';wrong.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError,'unsupported source ground bridge'):
                generate(wrong,'osc-stage-optical',folder/'osc-stage-optical.json')

    def test_complete_project_is_source_derived_with_only_named_changes(self):
        template=Path('boards/osc-jack-left/osc-jack-left.kicad_pro').read_bytes()
        for bid in ['osc-octave-1','osc-stage-optical']:
            # This tests the retained historical ground prerequisite, whose
            # minimal project predates the separately checked real PCB drafts.
            original=historical(f'boards/{bid}/{bid}.kicad_pro',ROUTING_BASE);definition=(BASE/(bid+'.json')).read_bytes()
            expected,receipt=derive(template,original,definition,bid+'-trial.kicad_pro');project=json.loads(expected)
            self.assertEqual(project['board']['design_settings']['rules']['min_copper_edge_clearance'],.5)
            self.assertEqual(project['board']['design_settings']['rules']['min_track_width'],.2)
            self.assertTrue(receipt['all_unrelated_template_values_unchanged'])
            self.assertEqual(derive(template,original,definition,bid+'-trial.kicad_pro')[0],expected)
            weakened=json.loads(definition);weakened['routing']['min_track_width_mm']=.05
            with self.assertRaisesRegex(ValueError,'cannot weaken'):
                derive(template,original,json.dumps(weakened).encode(),bid+'-trial.kicad_pro')
            changed=json.loads(original);changed['foreign_setting']='preserve me'
            with self.assertRaisesRegex(ValueError,'known source form'):
                derive(template,json.dumps(changed).encode(),definition,bid+'-trial.kicad_pro')

    def test_routing_transition_rejects_geometry_and_undeclared_rules(self):
        path='design/boards/osc-octave-1.json'
        old=historical(path,ROUTING_BASE);current=Path(path).read_bytes()
        routing=json.loads(Path(ROUTING).read_bytes())
        prove_octave_routing_only(old,current,routing)
        for field in ('outline','layers','routing'):
            changed=json.loads(current)
            if field=='outline':changed[field][0][0]+=.01
            elif field=='layers':changed[field]=4
            else:changed[field]['net_classes'][0]['clearance_mm']=.01
            with self.assertRaisesRegex(ValueError,'beyond declared routing'):
                prove_octave_routing_only(old,json.dumps(changed).encode(),routing)



if __name__=='__main__':unittest.main()
