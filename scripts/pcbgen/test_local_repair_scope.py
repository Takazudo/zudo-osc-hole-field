import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import route_jack_grid as driver
from scripts.pcbgen.route_jack_grid import repair_batch,repair_nets
from scripts.pcbgen.test_grid_router import crossing_board


class LocalRepairScopeTests(unittest.TestCase):
    def test_repair_cannot_enable_reserved_planes_or_empty_search(self):
        self.assertEqual(driver.repair_layers({}),list(driver.SIGNAL_LAYERS))
        for layers in ([],['In1.Cu'],['In4.Cu'],['F.Cu','F.Cu']):
            with self.subTest(layers=layers),self.assertRaises(ValueError):
                driver.repair_layers({'repair_layers':layers})

    def test_explicit_corridor_cut_does_not_expand_to_nearby_copper(self):
        dump=crossing_board();dump['tracks']=[{'uuid':'cut','net':'victim'},{'uuid':'keep','net':'victim'}]
        with patch.object(driver,'repair_batch',side_effect=AssertionError('must not expand explicit selection')):
            targets,cut=driver.repair_selection(dump,{'repair_targets':['A'],'repair_source_uuids':['cut']})
        self.assertEqual((targets,cut),(['A'],{'cut'}))

    def test_explicit_corridor_cut_rejects_unknown_objects_and_non_signal_targets(self):
        dump=crossing_board();dump['tracks']=[{'uuid':'ground','net':'AGND'}]
        for targets,cut in [(['A'],['missing']),(['A'],['ground']),(['AGND'],[]),(['missing'],[]),([],[])]:
            with self.subTest(targets=targets,cut=cut),self.assertRaises(ValueError):
                driver.repair_selection(dump,{'repair_targets':targets,'repair_source_uuids':cut})

    def test_unrelated_open_nets_are_not_rerouted(self):
        dump=crossing_board()
        dump['tracks']=[{'uuid':'cut','net':'victim','a':[0,0],'b':[1,0]},
                        {'uuid':'keep','net':'unrelated','a':[9,9],'b':[10,9]}]
        dump['islands']['unrelated']=[['pad'],['padless-fragment']]
        self.assertEqual(repair_nets(dump,['A'],{'cut'}),['A','victim'])
        self.assertEqual(dump['islands']['unrelated'],[['pad'],['padless-fragment']])

    def test_supply_ground_and_unknown_cuts_reject(self):
        dump=crossing_board();dump['tracks']=[{'uuid':'ground','net':'AGND'}]
        for cut in ({'ground'},{'unknown'}):
            with self.assertRaises(ValueError):repair_nets(dump,['A'],cut)

    def test_explicit_target_filter_does_not_select_other_open_nets(self):
        dump=crossing_board()
        targets,cut=repair_batch(dump,only={'A'})
        self.assertEqual(targets,['A'])

    def test_stage_keeps_native_padless_fragments_as_routing_obligations(self):
        original=crossing_board()
        original['tracks']=[{'uuid':'cut','net':'victim','a':[0,0],'b':[1,0]}]
        native={**original,'open_edges':3,'islands':{**original['islands'],'victim':[['pad'],['retained-boundary-fragment']]}}
        class StopAfterCapture(Exception):pass
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);base=root/'base.kicad_pcb';base.write_text('unchanged base')
            base.with_name('dump.json').write_text(json.dumps(original))
            cut=root/'cut';cut.mkdir()
            with patch.object(driver,'ROOT',root),patch.object(driver,'workspace',return_value=cut),\
                 patch.object(driver,'repair_batch',return_value=(['A'],{'cut'})),\
                 patch.object(driver,'run') as apply,patch.object(driver,'check',return_value=({},native)),\
                 patch.object(driver,'route',side_effect=StopAfterCapture) as route:
                with self.assertRaises(StopAfterCapture):
                    driver.stage('osc-jack-right',base,{'name':'local','repair':True,'repair_layers':['F.Cu','In2.Cu','B.Cu']},{},print)
            apply.assert_called_once()
            self.assertEqual(route.call_args.kwargs['allowed_layers'],['F.Cu','In2.Cu','B.Cu'])
            self.assertEqual(route.call_args.args[0]['islands']['victim'],[['pad'],['retained-boundary-fragment']])
            self.assertEqual(route.call_args.args[1],['A','victim'])
            self.assertEqual(route.call_args.kwargs['fill_guards'],{'-12V':'In3.Cu'})
            self.assertEqual(base.read_text(),'unchanged base')
