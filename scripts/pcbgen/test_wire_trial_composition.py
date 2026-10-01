"""Normal-frame energy and one continuous full-metal potential witness."""
import unittest
import numpy as np
from scripts.pcbgen.wire_trial_composition import bounds
from scripts.pcbgen.strand_adapter import arc,curved_collar_extent


class WireTrialTests(unittest.TestCase):
    def test_curved_bundle_end_cap_requires_arclength_collar(self):
        from scipy.optimize import brentq
        from scipy.integrate import quad
        H=81.2;point=np.array([.80812094,1.01015118,.06779600])
        def position(z):return np.array([8*np.sin(np.pi*z/H)**2,10*np.sin(np.pi*z/H)**2,z])
        def derivative(z):return np.array([8*np.pi/H*np.sin(2*np.pi*z/H),10*np.pi/H*np.sin(2*np.pi*z/H),1.])
        z=brentq(lambda z:np.dot(point-position(z),derivative(z)),0,1)
        self.assertLess(np.linalg.norm(point-position(z)),1.2954)
        s=quad(lambda z:np.linalg.norm(derivative(z)),0,z,epsabs=1e-13)[0]
        self.assertGreater(s,.07)
        upper,_=curved_collar_extent(.06791021359193991,1.2954,25.908,1.)
        self.assertLess(s,upper);self.assertLess(upper,.075)

    def test_adapter_normal_traces_bishop_frame_and_jacobian(self):
        length=.25;tilt=np.deg2rad(3.);azimuth=.73
        q,w=np.polynomial.legendre.leggauss(5)
        s=(q+1)*length/2
        c,t,ex,ey=arc(s,length,tilt,azimuth)
        np.testing.assert_allclose(np.cross(ex,ey),t,rtol=1e-14,atol=1e-14)
        eps=1e-6
        cp,tp,xp,yp=arc(s+eps,length,tilt,azimuth)
        cm,tm,xm,ym=arc(s-eps,length,tilt,azimuth)
        np.testing.assert_allclose((cp-cm)/(2*eps),t,rtol=1e-8,atol=1e-9)
        self.assertLess(np.max(abs(np.einsum('ij,ij->i',(xp-xm)/(2*eps),ey))),1e-9)
        end=arc(np.array([length]),length,tilt,azimuth)
        np.testing.assert_allclose(end[2][0],[1,0,0],atol=1e-15)
        np.testing.assert_allclose(end[3][0],[0,1,0],atol=1e-15)
        # Centred section: the linear Jacobian integrates to its exact area;
        # the same uniform normal current matches both finite endpoint cuts.
        a=.08;u,v=np.meshgrid(a*q,a*q);weights=a*a*np.outer(w,w)
        h=1+tilt/length*(np.cos(azimuth)*u+np.sin(azimuth)*v)
        self.assertGreater(h.min(),1-.175*tilt/length)
        self.assertAlmostEqual(float(np.sum(weights*h)),4*a*a,places=15)

    def test_curved_centred_section_has_no_bishop_current_energy_penalty(self):
        # A centred square is sufficient to exercise the exact linear
        # Jacobian cancellation; no physical wire shape is inferred from it.
        q,w=np.polynomial.legendre.leggauss(5)
        a=.1;R=2.;u,v=np.meshgrid(a*q,a*q)
        weights=a*a*np.outer(w,w);h=1-u/R
        self.assertGreater(h.min(),0)
        area=4*a*a
        self.assertAlmostEqual(float(np.sum(weights*h)),area,places=15)
        # One bundle-coordinate potential is continuous even where hypothetical
        # strands touch. Its full-volume inverse-Jacobian energy is enclosed.
        actual=float(np.sum(weights/h))
        self.assertLessEqual(actual,area/(1-a/R))

    def test_unselected_class_keeps_existing_resistance_and_length_margins(self):
        r=bounds()
        self.assertLess(r['bulk_trial_upper_ohm_per_bundle_axis_m'],.013)
        self.assertGreater(r['remaining_combined_termination_allowance_ohm'],0)
        for row in r['rows']:
            self.assertGreater(row['whole_wire_normal_material_lower_ohm'],0)
            self.assertLess(row['whole_wire_normal_material_lower_ohm'],row['whole_wire_hot_only_lower_ohm'])
            self.assertLess(row['whole_wire_hot_only_lower_ohm'],row['whole_wire_upper_ohm'])
            self.assertGreater(row['remaining_existing_whole_wire_budget_ohm'],0)
            self.assertLess(row['mean_strand_length_with_both_fans_upper_mm'],125)
        self.assertIn('OPEN',r['status'])
        self.assertLess(r['endpoint_adapter']['maximum_fan_plus_adapter_arclength_mm'],4)
        self.assertGreater(r['endpoint_adapter']['minimum_pairwise_vertical_cylinder_gap_mm'],0)


if __name__=='__main__':unittest.main()
