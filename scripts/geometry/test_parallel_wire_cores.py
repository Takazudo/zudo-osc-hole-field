import copy
import json
import math
from fractions import Fraction as F
from pathlib import Path
import unittest
import numpy as np
from scipy.integrate import quad

from scripts.geometry.parallel_wire_cores import bounds
from scripts.geometry.power_wire import registered_route
from scripts.pcbgen.contact_transfer import fan_geometry


class ParallelWireCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(Path('design/partition/partition-input.json').read_text())
        cls.fan = json.loads(Path('design/partition/contact-transfer-proposal.json').read_text())['main_strand_class']
        cls.wire = json.loads(Path('design/partition/wire-transfer-proposal.json').read_text())
        cls.geometry = fan_geometry()

    def inputs(self, board='JL', index=0):
        reference = registered_route(self.source, board, index, self.fan,
            self.wire['endpoint_adapter_class'],
            metal_radius=self.wire['bulk_potential_class']['maximum_metal_radius_from_bundle_axis_mm'])
        return [reference, copy.deepcopy(self.geometry), copy.deepcopy(self.fan),
                copy.deepcopy(self.wire['endpoint_adapter_class']),
                copy.deepcopy(self.wire['bulk_current_class']),
                self.source['load_distribution']['max_wire_length_mm']]

    def test_all_individual_lengths_against_independent_quadrature(self):
        for board, index in [('JL',0), ('JR',0), ('P',0), ('P',4)]:
            args = self.inputs(board,index); r = args[0]; result = bounds(*args)
            b = self.source['load_distribution']['branches'][board]
            H = r['bulk_span_mm']; x = b.get('bow_x_mm',0)
            dy = b['core_pad_y_mm'][index]-b['pad_y_mm']
            u = np.array([x,10])/math.hypot(x,10) if x else np.array([0.,1.])
            amp = math.hypot(x,10)
            first = lambda t: amp*math.pi*math.sin(2*math.pi*t)+6*dy*t*(1-t)
            second = lambda t: 2*amp*math.pi**2*math.cos(2*math.pi*t)+6*dy*(1-2*t)
            speed = lambda t: math.hypot(H,first(t))
            curvature = lambda t: H*second(t)/speed(t)**3
            axis = quad(speed,0,1,epsabs=1e-11)[0]
            for i, root in enumerate(self.geometry['root_xy_mm']):
                a = np.dot(root,u)
                length = quad(lambda t:(1-a*curvature(t))*speed(t),0,1,epsabs=1e-11)[0]
                self.assertAlmostEqual(length,axis,places=10)
                # Integrate both smoothstep fan stages independently, plus
                # tip, adapter and solder. The analytic bound covers all 19.
                end = self.fan['redistribution_tip_height_mm']+self.fan['solder_height_upper_mm']+args[3]['arclength_mm']
                for start,finish,h in zip(
                    (self.geometry['root_xy_mm'][i],self.geometry['expanded_xy_mm'][i]),
                    (self.geometry['expanded_xy_mm'][i],self.geometry['tip_xy_mm'][i]),
                    self.geometry['stage_heights_mm']):
                    d = math.dist(start,finish)
                    end += quad(lambda t:math.hypot(h,6*t*(1-t)*d),0,1,epsabs=1e-12)[0]
                self.assertLess(end,result['complete_endpoint_length_upper_mm'][i])
                self.assertLess(length+2*end+10,result['maximum_reference_with_preparation_upper_mm'])
            self.assertLess(result['global_graph_injectivity_factor_upper'],1)
            self.assertGreater(result['minimum_core_gap_lower_mm'],0)
            self.assertGreater(result['minimum_endpoint_horizontal_clearance_lower_mm'],.574999)
            self.assertFalse(result['manufactured_cut_or_material_admission'])

    def test_bad_tubes_and_class_limits_are_rejected(self):
        args=self.inputs(); args[1]['root_xy_mm'][0]=args[1]['root_xy_mm'][1]
        with self.assertRaisesRegex(ValueError,'overlap'): bounds(*args)
        args=self.inputs(); args[0]['bulk_metal_radius_mm']=.8
        with self.assertRaisesRegex(ValueError,'leave'): bounds(*args)
        args=self.inputs(); args[0]['bulk_curve_bounds']['second_parameter_derivative_norm_upper_mm']*=100
        with self.assertRaisesRegex(ValueError,'injectivity'): bounds(*args)
        for end in (0,1):
            args=self.inputs()
            cap=args[0]['endpoint_reservations_mm_positive_rear'][end]
            cap[3]=args[0]['points_mm_positive_rear'][0][0]+1
            with self.assertRaisesRegex(ValueError,'endpoint reservation'): bounds(*args)
        for end in (0,1):
            args=self.inputs()
            cap=args[0]['endpoint_reservations_mm_positive_rear'][end]
            cap[5 if end==0 else 2] += -.1 if end==0 else .1
            with self.assertRaisesRegex(ValueError,'axial geometry'): bounds(*args)
        args=self.inputs(); args[4]['core_radius_times_curvature_upper']=.001
        with self.assertRaisesRegex(ValueError,'curvature'): bounds(*args)
        args=self.inputs(); args[4]['mean_strand_arclength_over_bundle_axis_upper']=.99
        with self.assertRaisesRegex(ValueError,'ratio'): bounds(*args)
        args=self.inputs(); args[4]['frame_spin_upper_rad_per_mm']=-.1
        with self.assertRaisesRegex(ValueError,'spin'): bounds(*args)

    def test_solder_and_exact_cut_boundary_propagate(self):
        args=self.inputs(); base=bounds(*args)
        args[2]['solder_height_upper_mm']+=.01
        args[0]=registered_route(self.source,'JL',0,args[2],args[3],metal_radius=args[0]['bulk_metal_radius_mm'])
        changed=bounds(*args)
        self.assertGreater(changed['complete_endpoint_length_upper_mm'][0],base['complete_endpoint_length_upper_mm'][0])
        args[2]['solder_height_upper_mm']+=.1
        args[0]=registered_route(self.source,'JL',0,args[2],args[3],metal_radius=args[0]['bulk_metal_radius_mm'])
        with self.assertRaisesRegex(ValueError,'including solder'): bounds(*args)
        args=self.inputs(); args[-1]=base['maximum_reference_with_preparation_upper_mm']
        self.assertGreaterEqual(bounds(*args)['source_cut_margin_lower_mm'],0)
        args[-1]=math.nextafter(args[-1],-math.inf)
        with self.assertRaisesRegex(ValueError,'source cut'): bounds(*args)
        exact=F(args[0]['bulk_curve_bounds']['axis_length_upper_mm'])+8+10
        self.assertGreaterEqual(F(base['maximum_reference_with_preparation_upper_mm']),exact)
        self.assertLessEqual(F(base['source_cut_margin_lower_mm']),F(110)-exact)

    def test_wrong_endpoints_and_malformed_geometry_rejected(self):
        args=self.inputs(); args[0]['endpoint_reference']['adapter_tilt_deg']=1
        with self.assertRaisesRegex(ValueError,'axial'): bounds(*args)
        args=self.inputs(); args[2]['solder_height_upper_mm']+=.01
        with self.assertRaisesRegex(ValueError,'differs from'): bounds(*args)
        args=self.inputs(); args[1]['stage_heights_mm'][0]+=.01
        with self.assertRaisesRegex(ValueError,'heights differ'): bounds(*args)
        args=self.inputs(); args[1]['tip_xy_mm'].pop()
        with self.assertRaisesRegex(ValueError,'count'): bounds(*args)
        args=self.inputs(); args[1]['root_xy_mm'][0][0]=float('nan')
        with self.assertRaisesRegex(ValueError,'finite'): bounds(*args)
        args=self.inputs(); args[4]['contained_core_radius_mm']=.174
        with self.assertRaisesRegex(ValueError,'sections'): bounds(*args)

    def test_full_eighteen_reference_inventory(self):
        for board in self.source['load_distribution']['branches']:
            for index in range(6):
                r=bounds(*self.inputs(board,index))
                self.assertEqual(r['core_count'],19)
                self.assertEqual(r['individual_bulk_length_over_axis'],1)
                self.assertLess(r['maximum_reference_with_preparation_upper_mm'],110)
                self.assertLess(max(r['complete_endpoint_length_upper_mm']),4)


if __name__ == '__main__': unittest.main()
