"""Divergence, boundary flux and finite wire/contact accounting."""
import unittest
import numpy as np
from scripts.pcbgen.contact_transfer import extruded_vertical_current,main_strand_trial


class ContactTransferTests(unittest.TestCase):
    def test_extrusion_divergence_and_face_flux_with_unequal_profiles(self):
        h=.1;f=np.array([0.,2.,3.]);g=np.array([1.,3.,3.])
        bottom=extruded_vertical_current(0.,h,f,g)
        top=extruded_vertical_current(h,h,f,g)
        np.testing.assert_allclose(top,-f);np.testing.assert_allclose(bottom,-g)
        np.testing.assert_allclose((top-bottom)/h+(f-g)/h,0.,atol=1e-14)
        nodes,weights=np.polynomial.legendre.leggauss(3)
        values=extruded_vertical_current((nodes[:,None]+1)*h/2,h,f,g)
        numerical=(weights[:,None]*values**2).sum(axis=0)*h/2
        np.testing.assert_allclose(numerical,h*(f*f+f*g+g*g)/3,rtol=1e-14)

    def test_refined_trials_keep_positive_contact_margin_without_double_wire_charge(self):
        results=[main_strand_trial(p) for p in (.05,.025,.0125)]
        for r in results:
            self.assertLess(r['maximum_current_residual_A'],1e-8)
            self.assertLess(r['fan_copper_hot_upper_ohm_per_m'],.013)
            self.assertGreater(r['remaining_combined_termination_budget_ohm'],.00015)
            self.assertAlmostEqual(r['one_terminal_added_redistribution_ohm'],
                r['one_terminal_copper_redistribution_ohm']-r['one_terminal_tip_straight_wire_baseline_ohm'],places=15)
        values=[r['two_terminal_added_transfer_ohm'] for r in results]
        self.assertLess(abs(values[-1]-values[-2]),abs(values[1]-values[0]))


if __name__=='__main__':unittest.main()
