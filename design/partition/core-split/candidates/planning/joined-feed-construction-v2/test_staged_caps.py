"""Independent synthetic regressions; no project geometry or native execution."""
import copy
import unittest
import connectivity as graph
import staged_caps as caps


def pad(identity, net, x, y=0, radius=.05, layer='F.Cu'):
    return dict(id=identity, kind='pad', net=net, layers=[layer],
                polygon_mm=[[x-radius,y-radius],[x+radius,y-radius],
                            [x+radius,y+radius],[x-radius,y+radius]])


def fixture():
    nets=['+12V','-12V','+5V','AGND','AGND','AGND']
    objects=[pad(f'CS247-KA-W{i+1}', net, i*10) for i,net in enumerate(nets)]
    source=dict(board='KA', objects=objects,
                loads=[dict(net=net,pad_id=objects[i]['id']) for i,net in enumerate(nets[:4])])
    return source,dict(new_objects=[],clipped_sheets={net:[] for net in graph.NET_LAYER})


def stage(identity, layers, x=0, net='+12V', source='CS247-KA-W1'):
    return dict(id=identity,kind='via',net=net,layers=layers,center_mm=[x,0],
                diameter_mm=.15,drill_mm=.075,via_type='microvia',
                source_pad_uuid=source,filled_and_capped_required=True,
                barrel_wall_min_mm=.025)


class StagedCapsTests(unittest.TestCase):
    def test_adjacent_same_net_stages_share_finite_cap(self):
        source,planes=fixture()
        source['objects'] += [stage('s1',['F.Cu','In1.Cu']),stage('s2',['In1.Cu','In2.Cu']),
                              pad('target','+12V',0,layer='In2.Cu')]
        source['loads'][0]['pad_id']='target'
        result=graph.build(caps.materialize(source),planes)
        self.assertEqual(result['explicit_closed_cap_count'],4)
        self.assertEqual(result['status'],'SOURCE_ALL_DIRECT_LOADS_CONNECTED')

    def test_disjoint_dielectric_depths_do_not_cut_walls(self):
        source,planes=fixture()
        source['objects'] += [stage('s1',['F.Cu','In1.Cu']),stage('s2',['In3.Cu','In4.Cu'])]
        self.assertEqual(graph.build(caps.materialize(source),planes)['explicit_closed_cap_count'],4)

    def test_original_open_drill_cutting_cap_refused(self):
        source,planes=fixture();source['objects'].append(stage('s',['F.Cu','In1.Cu']))
        source['objects'].append(dict(id='old',kind='via',net='+12V',layers=list(caps.LAYERS),
                                      center_mm=[0,0],diameter_mm=.7,drill_mm=.3))
        with self.assertRaisesRegex(ValueError,'open drill cuts closed copper cap'):
            graph.build(caps.materialize(source),planes)

    def test_overlapping_dielectric_drill_cuts_wall_refused(self):
        source,planes=fixture()
        source['objects'] += [stage('s1',['F.Cu','In1.Cu']),stage('s2',['F.Cu','In1.Cu'],x=.06)]
        with self.assertRaisesRegex(ValueError,'cuts declared continuous barrel wall'):
            graph.build(caps.materialize(source),planes)

    def test_different_net_overlapping_caps_refused(self):
        source,planes=fixture();source['objects'].append(pad('foreign-pad','-12V',0))
        source['objects'] += [stage('s1',['F.Cu','In1.Cu']),
                              stage('s2',['In1.Cu','In2.Cu'],net='-12V',source='foreign-pad')]
        with self.assertRaisesRegex(ValueError,'different-net cap solids overlap'):
            graph.build(caps.materialize(source),planes)

    def test_process_identity_and_exact_depth_bindings(self):
        source,_=fixture();source['objects'].append(stage('s',['F.Cu','In1.Cu']))
        for mutation in ['flag','source-pad','cap-via-id','depth','thickness']:
            with self.subTest(mutation=mutation):
                value=copy.deepcopy(source)
                if mutation=='flag':value['objects'][-1]['filled_and_capped_required']=False
                if mutation=='source-pad':value['objects'][-1]['source_pad_uuid']='absent'
                if mutation in ['flag','source-pad']:
                    with self.assertRaises(ValueError):caps.materialize(value)
                    continue
                value=caps.materialize(value);cap=value['staged_cap_solids']['caps'][0]
                if mutation=='cap-via-id':cap['via_id']='unknown'
                if mutation=='depth':cap['z_band_mm']=[0,.071]
                if mutation=='thickness':cap['copper_thickness_mm']=.071
                with self.assertRaises(ValueError):caps.validate(value)

    def test_in_place_cap_band_mutation_cannot_change_expected_stack(self):
        source,_=fixture();source['objects'].append(stage('s',['F.Cu','In1.Cu']))
        expected=copy.deepcopy(caps.BANDS)
        material=caps.materialize(source)
        material['staged_cap_solids']['caps'][0]['z_band_mm'][1]=.071
        self.assertEqual(caps.BANDS,expected)
        self.assertEqual(material['staged_cap_solids']['foil_bands_mm'],expected)
        with self.assertRaises(ValueError):caps.validate(material)
        material=caps.materialize(source)
        material['staged_cap_solids']['foil_bands_mm']['F.Cu'][1]=.071
        self.assertEqual(caps.BANDS,expected)
        with self.assertRaisesRegex(ValueError,'six-foil'):caps.validate(material)

    def test_legacy_open_via_does_not_acquire_cap(self):
        source,planes=fixture()
        source['objects'].append(dict(id='legacy',kind='via',net='+12V',layers=list(caps.LAYERS),
                                      center_mm=[0,0],diameter_mm=.7,drill_mm=.3))
        material=caps.materialize(source)
        self.assertEqual(material['staged_cap_solids']['caps'],[])
        result=graph.build(material,planes)
        self.assertTrue(any(row['pad_id']=='CS247-KA-W1' for row in result['disconnected_loads']))

    def test_nonadjacent_staged_endpoints_refused(self):
        source,_=fixture();source['objects'].append(stage('bad',['F.Cu','In2.Cu']))
        with self.assertRaisesRegex(ValueError,'adjacent staged foils'):caps.materialize(source)

    def test_remote_split_foil_piece_does_not_join_barrel(self):
        source,planes=fixture();source['objects'][0]=pad('CS247-KA-W1','+12V',.22,radius=.025)
        source['objects'] += [dict(id='split',kind='via',net='+12V',layers=['F.Cu','B.Cu'],
                                  center_mm=[0,0],diameter_mm=2.,drill_mm=.3),
                              pad('remote','+12V',.96,radius=.015,layer='B.Cu')]
        source['objects'] += [dict(id=f'hole{i}',kind='keepout',net='FOREIGN',layers=['F.Cu','B.Cu'],
                                  center_mm=[.6,y],drill_mm=.62) for i,y in enumerate([-.6,0,.6])]
        source['loads'][0]['pad_id']='remote'
        result=graph.build(caps.materialize(source),planes)
        self.assertTrue(any(row['pad_id']=='remote' for row in result['disconnected_loads']))


if __name__=='__main__':unittest.main()
