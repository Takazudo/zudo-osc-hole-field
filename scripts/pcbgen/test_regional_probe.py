"""Analytic counterexamples and a real sheet/barrel/source reconstruction."""
from fractions import Fraction as F
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from shapely.geometry import box

from scripts.pcbgen.regional_probe import (
    polarization_interval, corrected_region, regional_solution_interval,
    metric_cross, barrel_lower_mass, collect_regions, sum_raw, verify_hashes, sha, source_lift_region)
from scripts.pcbgen.barrel_volume import BarrelVolume
from scripts.pcbgen.current_trial_matrix import current_matrix
from scripts.pcbgen.sheet_conservation import SheetConservation
from scripts.pcbgen.test_sheet_volume import assembly, RHO, THICKNESS, BANDS


class RegionalProbeTests(unittest.TestCase):
    def assertContains(self, interval, value):
        self.assertLessEqual(interval[0],value)
        self.assertGreaterEqual(interval[1],value)

    def test_psd_upper_off_diagonal_is_not_an_upper_transfer(self):
        # Both physical matrices lie between 0 and 2I, while the upper
        # off-diagonal is zero and actual cross can have either sign.
        bound=polarization_interval([[2,0],[0,2]],[[0,0],[0,0]])
        for sign in (-1,1):
            self.assertContains(bound['cross_interval'],sign)
        self.assertEqual(bound['cross_interval'],[-1.,1.])

    def test_positive_two_sided_metric_and_negative_cross(self):
        U=[[3,-1],[-1,3]];L=[[1,-1],[-1,1]]
        result=polarization_interval(U,L)
        self.assertContains(result['cross_interval'],-1)
        self.assertEqual(result['cross_interval'],[-2.,0.])
        with self.assertRaises(ValueError):polarization_interval([[1,2],[2,1]],L)

    def test_cell_metric_enclosure_contains_actual_gram(self):
        q=np.array([[[1.,2.],[-3.,1.]],[[.25,-2.],[1.,.5]]])
        low=np.array([np.diag([1.,2.]),np.diag([2.,3.])]);high=low+np.eye(2)[None,:,:]*2
        result=metric_cross(q,high,low)
        for fraction in (0,.2,.8,1):
            physical=low+fraction*(high-low)
            exact=np.einsum('ti,tij,tj->',q[:,:,0],physical,q[:,:,1])
            self.assertContains(result['cross_interval'],exact)
            for k in (0,1):
                self.assertGreaterEqual(result['energy_upper'][k],np.einsum('ti,tij,tj->',q[:,:,k],physical,q[:,:,k]))

    def test_exact_finite_source_lift_shared_and_signed_overlap(self):
        a=box(0,0,1,1);b=box(.5,0,1.5,1)
        profiles=[[(0,a,1.)],[(0,b,-1.)]]
        raw=source_lift_region(profiles,0,3.,1.)
        self.assertEqual(raw['energy_upper'],[1.,1.])
        self.assertEqual(raw['cross_interval'],[-.5,-.5])
        from shapely.geometry import Polygon
        with self.assertRaisesRegex(ValueError,'rectilinear'):
            source_lift_region([[(0,Polygon([(0,0),(1,0),(0,1)]),1.)],profiles[0]],0,3.,1.)

    def test_actual_barrel_metric_minima_keep_every_cell(self):
        for refinement in (1,2):
            b=BarrelVolume(.15,.025,.25,1.6,BANDS,RHO,polygon_sides=8,
                angular_subdivisions=refinement,radial_steps=refinement,
                band_steps=refinement,gap_steps=2*refinement)
            low=barrel_lower_mass(b,.15,refinement)
            self.assertEqual(low.shape,b.rt_mass.shape)
            self.assertGreater(np.linalg.eigvalsh(low).min(),0)
            self.assertGreaterEqual(np.linalg.eigvalsh(b.rt_mass-low).min(),0)
            # Within each cell all diagonal metric ratios share r_lo*theta_min
            # /(r_hi*theta_max); even the worst complete-annulus ratio is >0.
            ratios=low[:,0,0]/b.rt_mass[:,0,0]
            self.assertGreater(ratios.min(),.4)
            self.assertLess(ratios.max(),1)
        with self.assertRaises(ValueError):barrel_lower_mass(b,.15,1)

    def test_raw_to_conserved_norm_charge_and_union(self):
        a=np.array([2.,-1.]);b=np.array([-3.,4.]);ea=np.array([.2,-.1]);eb=np.array([-.1,.3])
        raw={'energy_upper':[float(a@a),float(b@b)],'cross_interval':[float(a@b)]*2}
        result=corrected_region(raw,[float(ea@ea),float(eb@eb)])
        self.assertContains(result['cross_interval'],float((a+ea)@(b+eb)))
        self.assertGreaterEqual(result['energy_upper'][0],float((a+ea)@(a+ea)))
        rows=[{'energy_upper':[1.,2.],'cross_interval':[-1.,-.5]},
              {'energy_upper':[3.,4.],'cross_interval':[.25,.5]}]
        self.assertEqual(sum_raw(rows),{'energy_upper':[4.,6.],'cross_interval':[-.75,0.]})

    def test_loose_independent_regional_uppers_keep_global_gap(self):
        trial={'energy_upper':[20,20],'cross_interval':[1,1]}
        result=regional_solution_interval(trial,[2,2],[2,2])
        self.assertEqual(result['transfer_interval_ohm'],[1.,1.])
        with self.assertRaises(ValueError):regional_solution_interval(trial,[1,2],[2,2])

    def test_mutated_input_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input';p.write_text('old');row={str(p):sha(p)}
            verify_hashes(row);p.write_text('new')
            with self.assertRaisesRegex(ValueError,'changed diagnostic input'):verify_hashes(row)

    def test_gated_two_column_physical_fixture_exports_every_piece(self):
        source=box(.4,.4,.65,.65);sink=box(-.7,-.5,-.45,-.25)
        v=assembly([(0,0)],(-1,-1,1,1),source,sink,1)
        v.certificate_mode='current'
        profiles=[[(3,source,1.),(1,sink,-1.)],[(0,source,1.),(1,sink,-1.)]]
        geometry={'thickness':THICKNESS,'active_sheet_layers':['F.Cu','In1.Cu','In2.Cu','B.Cu'],
                  '_probe_refinement':1,'barrel_ownership':[{'uuid':'fixture-via','finished_drill_mm':.3}]}
        with tempfile.TemporaryDirectory() as td:
            class Recorder(SheetConservation):
                def correction_energy(self,field,sources):
                    energy,receipt=super().correction_energy(field,sources)
                    self.rows,self.internal=collect_regions(self.volume,field,sources,geometry,profiles,RHO,Path(td))
                    self.energy=energy
                    return energy,receipt
            recorder=Recorder(v);v.conservation_repair=recorder
            result=current_matrix(v,profiles,RHO,THICKNESS,batch_size=2)
            self.assertLess(result['maximum_equation_residual_A'],1e-8)
            self.assertEqual(len(recorder.rows),5)
            self.assertEqual(recorder.rows[-1]['id'],'barrel:fixture-via')
            archive=np.load(Path(td)/'current-fields.npz')
            self.assertEqual(archive['hybrid_field'].shape[1],2)
            self.assertIn('barrel_port_0',archive.files)
            faces,local=v.barrel_local_maps[0]
            expected=-v.barrel_field_admittances[0]@(local@archive['hybrid_field'][faces])
            np.testing.assert_array_equal(archive['barrel_port_0'],expected)
            self.assertIn('sheet_flux_3',archive.files)
            raw=sum_raw(recorder.rows)
            # The raw metric cross interval plus a strict numerical correction
            # margin encloses this same physical trial's upper-metric cross
            # only if that upper metric is actually attained; do NOT assert it.
            # Instead check conservation errors are charged and physically
            # nonempty regional diagonal bounds cover positive finite energy.
            self.assertGreater(min(raw['energy_upper']),0)
            self.assertGreaterEqual(min(recorder.energy),0)
            self.assertGreaterEqual(min(recorder.internal),0)
            self.assertGreater(raw['cross_interval'][1],raw['cross_interval'][0])
            self.assertLess(max(recorder.internal),1e-10)


if __name__=='__main__':unittest.main()
