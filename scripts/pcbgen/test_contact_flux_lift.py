import math
import unittest
from fractions import Fraction
import numpy as np
from contact_flux_lift import energy_upper, height_range_upper, cosine_mode_field


class ContactFluxLiftTest(unittest.TestCase):
    def test_nonuniform_divergence_traces_and_energy(self):
        w,l,h,rho,I,a=.18,.25,.025,2e-4,.3,7.
        def field(x,z):
            return cosine_mode_field(x,z,width_mm=w,length_mm=l,height_mm=h,
                                     net_current_a=I,amplitude_a_per_mm2=a)
        eps=1e-7
        for x,z in ((.031,.008),(.17,.019)):
            div=(field(x+eps,z)[0]-field(x-eps,z)[0]+field(x,z+eps)[1]-field(x,z-eps)[1])/(2*eps)
            self.assertLess(abs(div),1e-6)
        self.assertAlmostEqual(field(0,.013)[0],0)
        self.assertAlmostEqual(field(l,.013)[0],0)
        self.assertAlmostEqual(field(.031,0)[1],-I/(w*l))
        self.assertAlmostEqual(field(.031,h)[1],-I/(w*l)-a*math.cos(math.pi*.031/l))
        nodes,weights=np.polynomial.legendre.leggauss(32)
        energy=0.
        for n,wn in zip(nodes,weights):
            for m,wm in zip(nodes,weights):
                j=field(l*(n+1)/2,h*(m+1)/2)
                energy += wn*wm*(j[0]**2+j[1]**2)*rho*w*l*h/4
        exact=rho*(h*I**2/(w*l)+(h/3+l*l/(math.pi**2*h))*a*a*w*l/2)
        self.assertAlmostEqual(energy,exact,places=13)
        bound=energy_upper(width_mm=w,length_mm=l,height_mm=h,rho_ohm_mm=rho,
                           net_current_a=I,redistribution_l2_a_per_mm=abs(a)*math.sqrt(w*l/2))
        self.assertGreaterEqual(bound['total_energy_w_upper'],exact)
        self.assertLess(bound['total_energy_w_upper'],exact*1.10)

    def test_zero_net_and_outward_range(self):
        args=dict(width_mm=.18,length_mm=.25,rho_ohm_mm=2e-4,
                  net_current_a=0.,redistribution_l2_a_per_mm=1.)
        upper=height_range_upper(minimum_height_mm=.025,maximum_height_mm=.05,**args)
        self.assertGreater(upper,0)
        for h in np.linspace(.025,.05,29):
            self.assertGreaterEqual(upper,energy_upper(height_mm=h,**args)['total_energy_w_upper'])
        # Exact represented-value check, including extreme nonzero energy.
        v=energy_upper(width_mm=1.,length_mm=1.,height_mm=1.,rho_ohm_mm=1e-200,
                       net_current_a=1e-100,redistribution_l2_a_per_mm=0.)['total_energy_w_upper']
        self.assertGreaterEqual(Fraction.from_float(v),Fraction.from_float(1e-200)*Fraction.from_float(1e-100)**2)
        self.assertGreater(v,0.)


if __name__=='__main__':unittest.main()
