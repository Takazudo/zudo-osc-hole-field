import copy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from scripts.pcbgen.boundary_contact_profile import FoilCut,compile_cut,glue_cuts,RectangularFoil,disjoint_energy,POTENTIAL_ANSATZ


def faces(cut,positions=None,prefix='n'):
    positions=cut.interval if positions is None else tuple(map(F,positions))
    vertices=[];axis=cut.tangent_axis
    for i,x in enumerate(positions):
        point=list(cut.endpoints_mm[0]);point[axis]=x;vertices.append((prefix+str(i),tuple(point)))
    rows=[]
    for i,(a,b) in enumerate(zip(vertices,vertices[1:])):
        interior=tuple((a[1][j]+b[1][j])/2-cut.outward_normal_xy[j] for j in range(2))
        rows.append({'id':prefix+'f'+str(i),'vertices':[a,b],'foil_layer':cut.foil_layer,'depth_mm':cut.depth_mm,
            'outward_normal_xy':cut.outward_normal_xy,'boundary_incidence':1,'adjacent_interior_mm':interior})
    return rows


def region(name='a',x=(0,2),rho=3,current=2):
    return RectangularFoil(name,'B.Cu',x,(0,4),(F(3,2),F(8,5)),rho,current)


def trace_values(compiled,fn):return {node:fn(x) for node,x in compiled.coordinates.items()}


class BoundaryProfileTests(unittest.TestCase):
    def test_exact_current_and_weak_load_sign(self):
        r=region();cut=r.cut(0);c=compile_cut(cut,faces(cut,(0,1,4)))
        self.assertEqual(cut.current_into_A,2);self.assertEqual(cut.outward_density_A_per_mm2,-5)
        self.assertEqual([x['outward_current_A'] for x in c.faces],[F(-1,2),F(-3,2)])
        self.assertEqual(dict(c.nodal_load_A),{'n0':F(1,4),'n1':F(1),'n2':F(3,4)})
        values=trace_values(c,lambda y:3+2*y)
        self.assertEqual(c.weak_load(values,ansatz=POTENTIAL_ANSATZ),14)
    def test_rectangular_energy_equals_weak_load_and_dual_energy(self):
        for axis in (0,1):
            r=replace(region(),flow_axis=axis)
            entrance=compile_cut(r.cut(0),faces(r.cut(0)));exit=compile_cut(r.cut(1),faces(r.cut(1)))
            vin=trace_values(entrance,lambda y:F(7))
            vout=trace_values(exit,lambda y:F(7)-r.resistance_ohm*r.current_A)
            load=entrance.weak_load(vin,ansatz=POTENTIAL_ANSATZ)+exit.weak_load(vout,ansatz=POTENTIAL_ANSATZ)
            gradient=-r.rho_ohm_mm*r.current_A/r.cross_area_mm2
            volume=(r.x_mm[1]-r.x_mm[0])*(r.y_mm[1]-r.y_mm[0])*(r.depth_mm[1]-r.depth_mm[0])
            self.assertEqual(load,r.energy_W);self.assertEqual(volume*gradient**2/r.rho_ohm_mm,r.energy_W)
            self.assertEqual(r.voltage(r.cut(1).endpoints_mm[0],7),next(iter(vout.values())))
    def test_two_region_gluing_and_once_only_energy(self):
        a=region();b=region('b',(2,5),rho=7)
        left=compile_cut(a.cut(1),faces(a.cut(1),(0,1,4),'l'))
        right=compile_cut(b.cut(0),faces(b.cut(0),(0,2,3,4),'r'))
        interface_voltage=F(9)-a.resistance_ohm*a.current_A
        lv=trace_values(left,lambda y:interface_voltage);rv=trace_values(right,lambda y:interface_voltage)
        joined=glue_cuts(left,right,lv,rv,ansatz=POTENTIAL_ANSATZ)
        self.assertEqual(joined['internal_weak_work_W'],0)
        self.assertEqual(disjoint_energy([a,b]),(a.resistance_ohm+b.resistance_ohm)*a.current_A**2)
        self.assertEqual(b.voltage(b.cut(0).endpoints_mm[0],interface_voltage),a.voltage(a.cut(1).endpoints_mm[0],9))
    def test_different_partitions_match_complete_nonconstant_trace(self):
        a=region();b=region('b',(2,5))
        l=compile_cut(a.cut(1),faces(a.cut(1),(0,1,4),'l'));r=compile_cut(b.cut(0),faces(b.cut(0),(0,2,4),'r'))
        lv=trace_values(l,lambda y:2*y+3);rv=trace_values(r,lambda y:2*y+3)
        self.assertEqual(glue_cuts(l,r,lv,rv,ansatz=POTENTIAL_ANSATZ)['internal_weak_work_W'],0)
    def test_nonzero_local_gauge_terms_cancel_only_for_balanced_pair(self):
        a=region();l=compile_cut(a.cut(0),faces(a.cut(0)))
        r=compile_cut(a.cut(1),faces(a.cut(1)))
        zero=trace_values(l,lambda y:0);shift=trace_values(l,lambda y:11)
        self.assertEqual(l.weak_load(shift,ansatz=POTENTIAL_ANSATZ)-l.weak_load(zero,ansatz=POTENTIAL_ANSATZ),22)
        self.assertEqual(l.weak_load(shift,ansatz=POTENTIAL_ANSATZ)+r.weak_load(shift,ansatz=POTENTIAL_ANSATZ),0)
    def test_zero_source_preserves_complete_geometry_requirements(self):
        cut=replace(region().cut(0),current_into_A=0);c=compile_cut(cut,faces(cut))
        self.assertEqual(c.weak_load(trace_values(c,lambda y:17*y),ansatz=POTENTIAL_ANSATZ),0)
        with self.assertRaises(ValueError):compile_cut(cut,[])
    def test_missing_partial_gap_overlap_and_duplicate_faces_rejected(self):
        cut=region().cut(0)
        for positions in ((1,4),(0,3),(0,1,5)):
            with self.assertRaises(ValueError):compile_cut(cut,faces(cut,positions))
        for mode in ('gap','overlap','duplicate'):
            fs=faces(cut,(0,1,2,4))
            if mode=='gap':fs.pop(1)
            elif mode=='overlap':fs+=faces(cut,(0,2,4),'x')
            else:fs.append(copy.deepcopy(fs[0]))
            with self.assertRaises(ValueError):compile_cut(cut,fs)
    def test_foil_depth_normal_incidence_and_conductor_side_rejected(self):
        cut=region().cut(0)
        changes={'foil_layer':'F.Cu','depth_mm':(0,1),'outward_normal_xy':(1,0),'boundary_incidence':2,'adjacent_interior_mm':(-1,0)}
        for key,value in changes.items():
            fs=faces(cut);fs[0][key]=value
            with self.assertRaises(ValueError):compile_cut(cut,fs)
    def test_unshared_p1_node_or_conflicting_coordinate_rejected(self):
        cut=region().cut(0);fs=faces(cut,(0,1,4))
        fs[1]['vertices'][0]=('different',fs[1]['vertices'][0][1])
        with self.assertRaisesRegex(ValueError,'unshared'):compile_cut(cut,fs)
        fs=faces(cut,(0,1,4));fs[1]['vertices'][1]=('n0',fs[1]['vertices'][1][1])
        with self.assertRaisesRegex(ValueError,'conflicting'):compile_cut(cut,fs)
    def test_arbitrary_depth_varying_potential_rejected(self):
        cut=region().cut(0);c=compile_cut(cut,faces(cut));v=trace_values(c,lambda y:0)
        for ansatz in ('arbitrary3d','depth_average',None):
            with self.assertRaises(ValueError):c.weak_load(v,ansatz=ansatz)
    def test_equal_average_but_different_full_potential_trace_rejected(self):
        a=region();b=region('b',(2,5));l=compile_cut(a.cut(1),faces(a.cut(1)));r=compile_cut(b.cut(0),faces(b.cut(0)))
        lv=trace_values(l,lambda y:y);rv=trace_values(r,lambda y:4-y)
        self.assertEqual(l.weak_load(lv,ansatz=POTENTIAL_ANSATZ)+r.weak_load(rv,ansatz=POTENTIAL_ANSATZ),0)
        with self.assertRaisesRegex(ValueError,'not continuous'):glue_cuts(l,r,lv,rv,ansatz=POTENTIAL_ANSATZ)
    def test_same_net_current_different_support_is_not_gluing(self):
        a=region();b=replace(region('b',(2,5)),y_mm=(0,2));l=compile_cut(a.cut(1),faces(a.cut(1)));r=compile_cut(b.cut(0),faces(b.cut(0)))
        with self.assertRaisesRegex(ValueError,'full physical section'):glue_cuts(l,r,trace_values(l,lambda y:0),trace_values(r,lambda y:0),ansatz=POTENTIAL_ANSATZ)
    def test_wrong_current_or_normals_do_not_glue(self):
        a=region();b=region('b',(2,5));left=compile_cut(a.cut(1),faces(a.cut(1)))
        for cut in (replace(b.cut(0),current_into_A=-2),replace(b.cut(0),outward_normal_xy=(1,0))):
            right=compile_cut(cut,faces(cut))
            with self.assertRaises(ValueError):glue_cuts(left,right,trace_values(left,lambda y:0),trace_values(right,lambda y:0),ansatz=POTENTIAL_ANSATZ)
    def test_positive_volume_overlap_and_double_count_rejected(self):
        a=region()
        for regions in ([a,a],[a,region('b',(1,3))]):
            with self.assertRaises(ValueError):disjoint_energy(regions)
    def test_wrong_kind_tilt_zero_extent_nonfinite_rejected(self):
        cut=region().cut(0)
        for kw in ({'kind':'area_electrode'},{'endpoints_mm':((0,0),(1,1))},{'depth_mm':(1,1)},{'current_into_A':float('inf')}):
            with self.assertRaises(ValueError):replace(cut,**kw)
    def test_compiled_evidence_cannot_be_mutated(self):
        cut=region().cut(0);c=compile_cut(cut,faces(cut))
        with self.assertRaises(TypeError):c.nodal_load_A['n0']=999
        with self.assertRaises(TypeError):c.faces[0]['outward_current_A']=999


class ExistingConventionAndSourceFixtureTests(unittest.TestCase):
    def test_outward_flux_sign_matches_existing_boundary_current_api(self):
        from types import SimpleNamespace
        import numpy as np
        from shapely.geometry import LineString
        from scripts.pcbgen.sheet_flux import FluxSheet
        # Call the existing method on explicit geometry, never its constructor.
        cut=FoilCut('r','r:left','B.Cu',((0,0),(0,4)),(0,1),(-1,0),2)
        compiled=compile_cut(cut,faces(cut,(0,1,4)))
        fixture=SimpleNamespace(edges=np.array([[0,1],[1,2]]),counts=np.array([1,1]),
            sheet=SimpleNamespace(xy=np.array([[0.,0.],[0.,1.],[0.,4.]])))
        actual=FluxSheet.boundary_current(fixture,LineString(cut.endpoints_mm),-float(cut.current_into_A))
        self.assertEqual(list(map(F,actual)),[row['outward_current_A'] for row in compiled.faces])
    def test_source_fixture_exact_full_trace_and_once_only_energy(self):
        import json
        from pathlib import Path
        spec=json.loads((Path(__file__).resolve().parents[2]/'design/partition/foil-cut-profile-proposal.json').read_text())
        self.assertEqual(spec['status'],'UNSELECTED synthetic analytic fixture; no physical/candidate admission')
        self.assertEqual(spec['source_kind'],'full_section_foil_cut');self.assertEqual(spec['potential_ansatz'],POTENTIAL_ANSATZ)
        a,b=[RectangularFoil(**r) for r in spec['regions']]
        lc=compile_cut(a.cut(1),faces(a.cut(1),spec['left_join_face_breakpoints_mm'],'l'))
        rc=compile_cut(b.cut(0),faces(b.cut(0),spec['right_join_face_breakpoints_mm'],'r'))
        entrance=F(spec['entrance_voltage_V']);join=a.voltage(a.cut(1).endpoints_mm[0],entrance)
        glue_cuts(lc,rc,trace_values(lc,lambda y:join),trace_values(rc,lambda y:join),ansatz=spec['potential_ansatz'])
        self.assertEqual(disjoint_energy([a,b]),F(spec['expected_total_energy_W_exact']))
        self.assertEqual(a.resistance_ohm+b.resistance_ohm,F(spec['expected_series_resistance_ohm_exact']))
        far_voltage=b.voltage(b.cut(1).endpoints_mm[0],join)
        self.assertEqual(a.current_A*(entrance-far_voltage),disjoint_energy([a,b]))

if __name__=='__main__':unittest.main()
