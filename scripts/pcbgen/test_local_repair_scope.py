import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import route_jack_grid as driver
from scripts.pcbgen.route_jack_grid import repair_batch,repair_nets
from scripts.pcbgen.test_grid_router import crossing_board


class LocalRepairScopeTests(unittest.TestCase):
    def test_bounded_cut_requires_entire_geometry_and_explicit_scope(self):
        dump={'pads':[{'net':'A','xy':[5e6,5e6]}],
              'tracks':[{'uuid':'cut','net':'B','a':[4e6,5e6],'b':[6e6,5e6],'width':.2e6}],
              'vias':[]}
        spec={'repair_bounds_mm':[3,3,7,7],'repair_source_uuids':['cut']}
        self.assertEqual(driver.repair_bounds(dump,spec,['A'],{'cut'}),[3,3,7,7])
        for change in ({'repair_bounds_mm':[4,3,7,7]}, # Track width crosses the frame.
                       {'repair_bounds_mm':[3,3,6,7]},
                       {'repair_bounds_mm':[0,0,60,10]},
                       {'repair_bounds_mm':[3,3,float('nan'),7]},
                       {'repair_bounds_mm':[3,3,7]},
                       {'repair_bounds_mm':[8,3,7,7]}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                driver.repair_bounds(dump,{**spec,**change},['A'],{'cut'})
        with self.assertRaises(ValueError):
            driver.repair_bounds(dump,{'repair_bounds_mm':[3,3,7,7]},['A'],{'cut'})
        with self.assertRaises(ValueError):driver.repair_bounds(dump,spec,['A'],set())
        self.assertIsNone(driver.repair_bounds(dump,{},['A'],{'cut'}))

    def test_bounded_repair_limits_victims_and_requires_a_target_inside(self):
        dump={'pads':[{'net':'A','xy':[20e6,20e6]}],
              'tracks':[{'uuid':str(i),'net':f'B{i}','a':[4e6,5e6],'b':[6e6,5e6],'width':.2e6}
                        for i in range(13)],'vias':[]}
        spec={'repair_bounds_mm':[3,3,7,7],'repair_source_uuids':['0']}
        for cut in ({'0'},set(map(str,range(3))),set(map(str,range(13)))):
            with self.subTest(cut=cut),self.assertRaises(ValueError):
                driver.repair_bounds(dump,spec,['A'],cut)

    def test_bounded_stage_keeps_all_native_groups_after_the_cut(self):
        original=crossing_board()
        original['tracks']=[{'uuid':'cut','net':'victim','a':[5e6,3e6],
                             'b':[5e6,5e6],'width':.2e6}]
        native={**original,'open_edges':4,'islands':{**original['islands'],
                'victim':[['far-pad'],['padless-boundary']],'unrelated':[['p'],['q']]}}
        spec={'name':'bounded','repair':True,'repair_targets':['A'],
              'repair_source_uuids':['cut'],'repair_bounds_mm':[0,0,12,8],'res':.025}
        class Captured(Exception):pass
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);base=root/'base.kicad_pcb';base.write_text('unchanged')
            base.with_name('dump.json').write_text(json.dumps(original));cut=root/'cut';cut.mkdir()
            with patch.object(driver,'ROOT',root),patch.object(driver,'workspace',return_value=cut),\
                 patch.object(driver,'run'),patch.object(driver,'check',return_value=({},native)),\
                 patch.object(driver,'route',side_effect=Captured) as route:
                with self.assertRaises(Captured):driver.stage('osc-jack-left',base,spec,{},print)
            self.assertEqual(route.call_args.args[0]['islands'],native['islands'])
            self.assertEqual(route.call_args.kwargs['bounds_mm'],[0,0,12,8])
            self.assertEqual(route.call_args.kwargs['max_expansions'],300000)
            self.assertEqual(route.call_args.kwargs['allowed_layers'],driver.SIGNAL_LAYERS)
            self.assertEqual(base.read_text(),'unchanged')

    def test_ground_corridor_requires_explicit_bounded_signal_cuts(self):
        dump=crossing_board()
        dump['pads'] += [{'uuid':'g','net':'AGND'}]
        dump['islands']['AGND']=[['main','anchor'],['g']]
        dump['tracks']=[{'uuid':'cut','net':'victim'},{'uuid':'supply','net':'-12V'}]
        spec={'repair_targets':['AGND'],'repair_ground_pad_uuids':['g'],'repair_source_uuids':['cut']}
        self.assertEqual(driver.repair_selection(dump,spec),(['AGND'],{'cut'}))
        for change in ({'repair_ground_pad_uuids':[]},{'repair_ground_pad_uuids':['missing']},
                       {'repair_ground_pad_uuids':['g','g']},{'repair_targets':['-12V']},
                       {'repair_source_uuids':['supply']},{'repair_targets':['AGND','A']}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                driver.repair_selection(dump,{**spec,**change})
        with self.assertRaises(ValueError):
            driver.repair_selection(dump,{k:v for k,v in spec.items() if k!='repair_source_uuids'})
        dump['tracks']=[{'uuid':str(i),'net':f'victim{i}'} for i in range(13)]
        for count in (3,13):
            with self.subTest(count=count),self.assertRaises(ValueError):
                driver.repair_selection(dump,{**spec,'repair_source_uuids':[str(i) for i in range(count)]})

    def test_ground_search_scope_does_not_hide_native_groups_or_victim_fragments(self):
        dump={'islands':{'AGND':[['main','anchor'],['chosen'],['other']],
                         'victim':[['pad'],['padless-boundary']]}}
        search=driver.repair_search_dump(dump,{'repair_ground_pad_uuids':['chosen']})
        self.assertEqual(search['islands']['AGND'],[['main','anchor'],['chosen']])
        self.assertEqual(search['islands']['victim'],[['pad'],['padless-boundary']])
        self.assertEqual(len(dump['islands']['AGND']),3)

    def test_ground_stage_preserves_ground_dimensions_and_reserved_layers(self):
        original=crossing_board()
        original['pads'] += [{'uuid':'ground-pad','net':'AGND'}]
        original['islands']['AGND']=[['main','anchor'],['ground-pad'],['unrelated-ground']]
        original['tracks']=[{'uuid':'cut','net':'victim'}]
        native={**original,'open_edges':4,'islands':{**original['islands'],'victim':[['pad'],['boundary']]}}
        spec={'name':'ground','repair':True,'repair_targets':['AGND'],'repair_ground_pad_uuids':['ground-pad'],
              'repair_source_uuids':['cut'],'clearance':.2,'signal_width':.2}
        class Captured(Exception):pass
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);base=root/'base.kicad_pcb';base.write_text('unchanged')
            base.with_name('dump.json').write_text(json.dumps(original));cut=root/'cut';cut.mkdir()
            with patch.object(driver,'ROOT',root),patch.object(driver,'workspace',return_value=cut),\
                 patch.object(driver,'run'),patch.object(driver,'check',return_value=({},native)),\
                 patch.object(driver,'route',side_effect=Captured) as route:
                with self.assertRaises(Captured):driver.stage('osc-jack-left',base,spec,{},print)
            kwargs=route.call_args.kwargs
            self.assertEqual((kwargs['clearance'],kwargs['rail_width'],kwargs['via_diameter']),(.25,.3,.6))
            self.assertIn('AGND',kwargs['rail_nets'])
            self.assertIn('AGND',kwargs['grow'])  # Ground cannot use signal neck-down dimensions.
            self.assertEqual(kwargs['allowed_layers'],driver.SIGNAL_LAYERS)
            self.assertEqual(route.call_args.args[0]['islands']['victim'],[['pad'],['boundary']])
            self.assertEqual(len(native['islands']['AGND']),3)
            self.assertEqual(base.read_text(),'unchanged')

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
