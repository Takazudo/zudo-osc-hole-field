import math
import unittest
import numpy as np
from scripts.pcbgen.barrel_source_flux import energy_coefficient_upper,mode_field


class BarrelSourceFluxTest(unittest.TestCase):
    def test_actual_jack_shell_wall_mode(self):
        ri,ro,L,rho=.61,.635,1.6,2.3e-5
        kw=dict(inner_radius_mm=ri,outer_radius_mm=ro,length_mm=L,amplitude=1.,angular_mode=1,axial_mode=2)
        f=lambda r,u,z:mode_field(r,u,z,**kw)
        r,u,z=.622,.2,.45;eps=1e-7
        div=((r+eps)*f(r+eps,u,z)[0]-(r-eps)*f(r-eps,u,z)[0])/(2*eps*r)
        div += ri/r*(f(r,u+eps,z)[1]-f(r,u-eps,z)[1])/(2*eps)
        div += (f(r,u,z+eps)[2]-f(r,u,z-eps)[2])/(2*eps)
        self.assertLess(abs(div),1e-7)
        self.assertAlmostEqual(f(ri,u,z)[0],math.cos(u/ri)*math.cos(2*math.pi*z/L))
        self.assertAlmostEqual(f(ro,u,z)[0],0)
        self.assertAlmostEqual(f(r,u,0)[2],0);self.assertAlmostEqual(f(r,u,L)[2],0)
        for i in range(3):self.assertAlmostEqual(f(r,0,z)[i],f(r,2*math.pi*ri,z)[i])
        nodes,weights=np.polynomial.legendre.leggauss(16);E=0
        for nr,wr in zip(nodes,weights):
            rr=ri+(ro-ri)*(nr+1)/2
            for nu,wu in zip(nodes,weights):
                uu=math.pi*ri*(nu+1)
                for nz,wz in zip(nodes,weights):
                    zz=L*(nz+1)/2;j=f(rr,uu,zz)
                    E+=wr*wu*wz*sum(x*x for x in j)*(rr/ri)*(ro-ri)/2*(math.pi*ri)*L/2*rho
        norm2=2*math.pi*ri*L/4
        upper=energy_coefficient_upper(inner_radius_mm=ri,outer_radius_mm=ro,length_mm=L,rho_max_ohm_mm=rho)*norm2
        self.assertGreaterEqual(upper,E);self.assertGreater(E,0)

    def test_positive_thickness_and_zero_net_mode(self):
        with self.assertRaises(ValueError):energy_coefficient_upper(inner_radius_mm=.15,outer_radius_mm=.15,length_mm=1.6,rho_max_ohm_mm=2.3e-5)
        self.assertGreater(energy_coefficient_upper(inner_radius_mm=.15,outer_radius_mm=.175,length_mm=1.6,rho_max_ohm_mm=2.3e-5),0)
        f=mode_field(.15,0,.3,inner_radius_mm=.15,outer_radius_mm=.175,length_mm=1.6,amplitude=1,angular_mode=1,axial_mode=0)
        self.assertNotEqual(f[0],0)  # integral over theta is zero, local flux is not


if __name__=='__main__':unittest.main()
