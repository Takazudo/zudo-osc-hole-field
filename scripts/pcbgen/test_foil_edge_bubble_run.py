"""Small fixtures only; never load the retained mesh or solve an operator."""
import copy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from scripts.pcbgen.foil_edge_bubble_run import (
    geometry_interfaces,select_edges,checked_patch,read_json,inside,merge_bindings,verify_pair_binding)
from scripts.pcbgen.partial_cell_energy import CanonicalChart,ConservativeIndex,Budget


def fixture():
    sheet=SimpleNamespace(metric_xy=np.array([[0,0],[1,0],[1,1],[0,1]],dtype=np.longdouble),
        triangles=np.array([[0,1,2],[0,2,3]]),metric_factors=np.ones(2),interface_faces={})
    flux=np.array([[[1.,2.],[0.,0.],[-1.,-2.]],[[0.,0.],[0.,0.],[0.,0.]]])
    return sheet,flux


def native_fixture():
    layers=['F.Cu','In1.Cu','In2.Cu','B.Cu']
    rows=[]
    for i,t in enumerate([.07,.35,.14,.4,.07,.5,.07]):
        rows.append({'layer':layers[i//2],'copper_thickness_mm':t} if i%2==0 else {'layer':'dielectric'+str(i),'thickness_mm':t})
    native={'stackup':rows,'thickness_mm':1.6,'enabled_copper_layers':layers,
        'ground_reference':{'ref':'main'},'ground_reference_members':['v1'],'holes':[{'uuid':'v1','net':'AGND','xy_mm':[12.,34.],
        'size_mm':[.3,.3],'plated':True,'copper_layers':layers}]}
    full={'active_sheet_layers':layers,'refinement':1,'barrel_ownership':[{'uuid':'v1','xy_mm':[12.,34.],
        'finished_drill_mm':.3,'flange_radius_mm':.25}]}
    return native,full


class RunnerFixtures(unittest.TestCase):
    def test_descriptor_uses_actual_geometry_method_without_constructor(self):
        import math
        from scripts.pcbgen.barrel_volume import BarrelVolume
        native,full=native_fixture()
        with patch.object(BarrelVolume,'__init__',side_effect=AssertionError('operator construction forbidden')):
            interfaces,stack=geometry_interfaces(native,full)
        points=interfaces[0]['relative'];half=.25*math.tan(math.pi/16)
        self.assertEqual(points.shape,(16,2));self.assertEqual(tuple(points[0]),(.25,-half))
        # Independent scalar expression for every original, un-subdivided corner.
        for i,p in enumerate(points):
            theta=2*math.pi*i/16
            expected=np.array([.25*math.cos(theta)+half*math.sin(theta),
                               .25*math.sin(theta)-half*math.cos(theta)])
            np.testing.assert_array_equal(p,expected)
    def test_legacy_main_component_membership_matches_native_extractor(self):
        native,full=native_fixture();native['ground_reference']=None
        native['ground_reference_members']=None;native['main_rail_members']={'AGND':['v1']}
        interfaces,_=geometry_interfaces(native,full)
        self.assertEqual(len(interfaces),1)
    def test_changed_ownership_and_unsupported_refinement_rejected(self):
        for mutation in ('centre','plating','refinement'):
            native,full=native_fixture()
            if mutation=='centre':full['barrel_ownership'][0]['xy_mm']=[13.,34.]
            elif mutation=='plating':native['holes'][0]['plated']=False
            else:full['refinement']=2
            with self.assertRaises(ValueError):geometry_interfaces(native,full)
    def test_actual_edge_selection_exact_flux_reconstruction(self):
        sheet,flux=fixture();chart=CanonicalChart(sheet,[]);chart.validate_all_vertices()
        rows,census=select_edges(sheet,flux,chart.interface,128,500000)
        self.assertEqual(census,{'all_edges':5,'eligible_edges':1,'selected_patches':1})
        r=checked_patch(rows[0],chart,ConservativeIndex(sheet),[],flux,F(1),Budget({'overlap_checks':100}))
        self.assertEqual(r['raw_work_exact'],['1/3','2/3']);self.assertEqual(r['bubble_energy_exact'],'1/3')
    def test_interface_cut_crossing_without_selected_interface_vertices_rejected(self):
        sheet,flux=fixture();chart=CanonicalChart(sheet,[]);chart.validate_all_vertices()
        rows,_=select_edges(sheet,flux,[],128,500000)
        cut=tuple(tuple(map(F,p)) for p in [(-1,F(2,5)),(2,F(2,5)),(2,F(1,2)),(-1,F(1,2))])
        with self.assertRaisesRegex(ValueError,'complete barrel interface'):
            checked_patch(rows[0],chart,ConservativeIndex(sheet),[cut],flux,F(1),Budget({'overlap_checks':100}))
    def test_overlapping_foreign_cell_rejected(self):
        sheet,flux=fixture()
        sheet.metric_xy=np.r_[sheet.metric_xy,np.array([[.5,.1],[.8,.1],[.8,.2]],dtype=np.longdouble)]
        sheet.triangles=np.r_[sheet.triangles,[[4,5,6]]];sheet.metric_factors=np.ones(3)
        chart=CanonicalChart(sheet,[]);chart.validate_all_vertices()
        with self.assertRaisesRegex(ValueError,'positive area'):
            checked_patch({'triangles':[0,1],'edge_vertices':[0,2]},chart,ConservativeIndex(sheet),[],flux,F(1),Budget({'overlap_checks':100}))
    def test_nonfinite_selection_and_work_caps_rejected(self):
        sheet,flux=fixture()
        with self.assertRaises(ValueError):select_edges(sheet,flux,[],128,4)
        flux[0,0,0]=np.nan
        with self.assertRaises(ValueError):select_edges(sheet,flux,[],128,500000)
    def test_manifest_bytes_mutation_and_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json';path.write_text('{"upper": 1}')
            expected=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(read_json(path,expected)[0],{'upper':1})
            path.write_text('{"upper": 2}')
            with self.assertRaises(ValueError):read_json(path,expected)
            with self.assertRaises(ValueError):inside(tmp,'../foreign')
        with self.assertRaises(ValueError):merge_bindings({'a':'old'},{'a':'new'})
    def test_pair_field_and_capture_binding_rejected_on_splice(self):
        with tempfile.TemporaryDirectory() as tmp:
            config={'pair_receipt':'pair/receipt.json','current_fields':'pair/current-fields.npz',
                    'input_sha256':{'pair/receipt.json':'pairsha','pair/current-fields.npz':'fieldsha'}}
            ref={'ref':'TP990031','pad':'1','layer':3,'kind':'main','physical_layer':'B.Cu'}
            pair={'selected_columns':[['J900134','2'],['C107','2']],'matrix_indices':[4,128],
                  'reference_contact':ref,'raw_field_artifacts':{'current-fields.npz':'fieldsha'},'input_sha256':{'scripts/pcbgen/producer.py':'old'}}
            full={'reference_contact':ref,'model_source_sha256':{'producer.py':'old'}}
            capture={'source_pair':pair['selected_columns'],'input_sha256':{'pair/receipt.json':'pairsha'}}
            verify_pair_binding(config,pair,full,capture,Path(tmp))
            for mutation in ('path','fieldhash','producer','missing_producer','capture'):
                c,p,f,v=map(copy.deepcopy,(config,pair,full,capture))
                if mutation=='path':c['current_fields']='foreign/current-fields.npz';c['input_sha256'][c['current_fields']]='fieldsha'
                elif mutation=='fieldhash':p['raw_field_artifacts']['current-fields.npz']='other'
                elif mutation=='producer':f['model_source_sha256']['producer.py']='changed'
                elif mutation=='missing_producer':p['input_sha256'].clear()
                else:v['input_sha256']['pair/receipt.json']='otherpair'
                with self.assertRaises(ValueError):verify_pair_binding(c,p,f,v,Path(tmp))

if __name__=='__main__':unittest.main()
