"""Independent curve quadrature and registered endpoint/corridor regressions."""
import copy
import json
import math
from pathlib import Path
import unittest
from decimal import Decimal,localcontext
import numpy as np
from scipy.integrate import quad
from scripts.geometry.power_wire import curve_point,curve_bounds,registered_route,pi_interval
from scripts.pcbgen.contact_transfer import fan_geometry


class PowerWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads(Path('design/partition/partition-input.json').read_text())
        cls.fan=json.loads(Path('design/partition/contact-transfer-proposal.json').read_text())['main_strand_class']
        wire=json.loads(Path('design/partition/wire-transfer-proposal.json').read_text())
        cls.adapter=wire['endpoint_adapter_class']
        cls.radius=wire['bulk_potential_class']['maximum_metal_radius_from_bundle_axis_mm']

    def test_length_slope_curvature_against_independent_integration(self):
        for dy in (-4,0,4):
            H=79.3;bound=curve_bounds(H,H,dy,profile='smoothstep')
            first=lambda t:6*dy*t*(1-t)+10*math.pi*math.sin(2*math.pi*t)
            second=lambda t:6*dy*(1-2*t)+20*math.pi**2*math.cos(2*math.pi*t)
            length=quad(lambda t:math.hypot(H,first(t)),0,1,epsabs=1e-11)[0]
            self.assertLess(length,bound['axis_length_upper_mm'])
            for t in np.linspace(0,1,1001):
                self.assertLessEqual(abs(first(t))/H,bound['slope_upper'])
                curvature=abs(H*second(t))/(H*H+first(t)**2)**1.5
                self.assertLessEqual(curvature,1/bound['curvature_radius_lower_mm'])
            self.assertTrue(bound['axial_endpoint_tangents'])
        self.assertFalse(curve_bounds(79.3,79.3,-4)['axial_endpoint_tangents'])

    def test_full_source_endpoints_solder_and_both_offset_groups(self):
        branch=self.source['load_distribution']['branches']['P']
        for i in range(6):
            route=registered_route(self.source,'P',i,self.fan,self.adapter,metal_radius=self.radius)
            self.assertAlmostEqual(route['bulk_span_mm'],79.3)
            self.assertAlmostEqual(route['endpoint_reference']['axial_height_mm'],3.65)
            points=route['points_mm_positive_rear']
            np.testing.assert_allclose(points[0],[branch['x_mm'][i],179,13.4],atol=1e-12)
            np.testing.assert_allclose(points[-1],[branch['x_mm'][i],branch['core_pad_y_mm'][i],100],atol=1e-12)
            fan=copy.deepcopy(self.fan);fan['solder_height_upper_mm']+=.01
            moved=registered_route(self.source,'P',i,fan,self.adapter,metal_radius=self.radius)
            self.assertAlmostEqual(moved['bulk_span_mm'],route['bulk_span_mm']-.02)
            self.assertGreater(moved['endpoint_reservations_mm_positive_rear'][0][5],route['endpoint_reservations_mm_positive_rear'][0][5])

    def test_planar_registered_root_frames_match_both_fans(self):
        roots=np.asarray(fan_geometry()['root_xy_mm'])
        self.assertEqual(len(roots),19)
        np.testing.assert_allclose(roots.sum(axis=0),[0,0],atol=1e-14)
        H=79.3;dy=-4
        for t in (0.,1.):
            slope=(6*dy*t*(1-t)+10*math.pi*math.sin(2*math.pi*t))/H
            tangent=np.array([0,slope,1])/math.hypot(1,slope)
            ex=np.array([1,0,0]);ey=np.cross(tangent,ex)
            placed=roots[:,0,None]*ex+roots[:,1,None]*ey
            np.testing.assert_allclose(placed[:,:2],roots,atol=1e-14)
            np.testing.assert_allclose(placed[:,2],0,atol=1e-14)
            np.testing.assert_allclose(np.cross(ex,ey),tangent,atol=1e-14)
        for t in (1e-7,1-1e-7):
            point=curve_point(t,H,dy,profile='smoothstep')
            end=curve_point(0 if t<.5 else 1,H,dy,profile='smoothstep')
            self.assertLess(abs((point[1]-end[1])/(point[2]-end[2])),1e-5)

    def test_analytic_chord_enclosure_and_continuous_length(self):
        route=registered_route(self.source,'P',0,self.fan,self.adapter,metal_radius=self.radius)
        bulk=route['bulk_points_mm_positive_rear'];error=route['bulk_chord_error_upper_mm']
        for i,(p,q) in enumerate(zip(bulk,bulk[1:])):
            for u in (.1,.25,.5,.75,.9):
                local=curve_point((i+u)/100,route['bulk_span_mm'],-4,profile='smoothstep')
                actual=[p[0]+local[0],179+local[1],bulk[0][2]+local[2]]
                linear=[(1-u)*a+u*b for a,b in zip(p,q)]
                self.assertLessEqual(math.dist(actual,linear),error)
        length=sum(math.dist(p,q) for p,q in zip(route['points_mm_positive_rear'],route['points_mm_positive_rear'][1:]))
        self.assertLess(length,route['continuous_centreline_length_upper_mm'])

    def test_unproved_spatial_roll_and_shrunken_cap_are_rejected(self):
        for key,value in [('bow_x_mm',1),('endpoint_metal_half_extent_mm',1.99),('route_profile','unknown')]:
            source=copy.deepcopy(self.source);source['load_distribution']['branches']['P'][key]=value
            with self.assertRaises(ValueError):registered_route(source,'P',0,self.fan,self.adapter,metal_radius=self.radius)
        for values in [(0,1,0),(2,1,0),(1,1,float('nan'))]:
            with self.assertRaises(ValueError):curve_bounds(*values)
        source=copy.deepcopy(self.source);p=source['load_distribution']['branches']['P']
        p.update(bow_x_mm=5e-324,pad_y_mm=0,core_pad_y_mm=[5e-324]*6)
        with self.assertRaisesRegex(ValueError,'planar'):
            registered_route(source,'P',0,self.fan,self.adapter,metal_radius=self.radius)

    def test_all_eighteen_registered_routes_and_jl_endpoint_frame(self):
        routes=[]
        for board,branch in self.source['load_distribution']['branches'].items():
            for index,label in enumerate(self.source['load_distribution']['wire_labels']):
                route=registered_route(self.source,board,index,self.fan,self.adapter,metal_radius=self.radius)
                routes.append(route)
                self.assertEqual(route['wire_label'],label)
                self.assertGreater(route['bulk_curve_bounds']['curvature_radius_lower_mm'],self.source['load_distribution']['minimum_bend_radius_mm'])
                self.assertLess(route['continuous_centreline_length_upper_mm']+10,110)
        self.assertEqual(len(routes),18)
        roots=np.asarray(fan_geometry()['root_xy_mm'])
        u=np.array([8,10,0])/math.hypot(8,10);v=np.array([-u[1],u[0],0]);z=np.array([0,0,1])
        for t in (0.,1.):
            theta=math.atan(math.pi*math.hypot(8,10)*math.sin(2*math.pi*t)/81.1)
            normal=math.cos(theta)*u-math.sin(theta)*z
            ex=u[0]*normal+v[0]*v;ey=u[1]*normal+v[1]*v
            mapped=roots[:,0,None]*ex+roots[:,1,None]*ey
            np.testing.assert_allclose(mapped,np.column_stack((roots,np.zeros(19))),atol=1e-14)

    def test_directed_bounds_enclose_independent_high_precision_values(self):
        with localcontext() as ctx:
            ctx.prec=70
            pi=Decimal('3.1415926535897932384626433832795028841971693993751')
            lower,upper=pi_interval()
            self.assertLess(Decimal(lower.numerator)/Decimal(lower.denominator),pi)
            self.assertGreater(Decimal(upper.numerator)/Decimal(upper.denominator),pi)
            for span in (81.1,81.10000000000001,79.3):
                r=curve_bounds(span,span,0,8)
                H=Decimal.from_float(span)
                second=2*pi*pi*Decimal(164).sqrt()
                self.assertGreaterEqual(Decimal.from_float(r['second_parameter_derivative_norm_upper_mm']),second)
                self.assertLessEqual(Decimal.from_float(r['curvature_radius_lower_mm']),H*H/second)
                self.assertGreaterEqual(Decimal.from_float(r['axis_length_upper_mm']),(H*H+pi*pi*82).sqrt())
            for index,dy in ((0,-4),(4,0)):
                route=registered_route(self.source,'P',index,self.fan,self.adapter,metal_radius=self.radius)
                H=Decimal.from_float(route['bulk_span_mm'])
                cap=Decimal.from_float(route['endpoint_reference']['axial_height_mm'])
                true_bound=(H*H+Decimal(6)*dy*dy/5+pi*pi*50).sqrt()+2*cap
                self.assertGreaterEqual(Decimal.from_float(route['continuous_centreline_length_upper_mm']),true_bound)


if __name__=='__main__':unittest.main()
