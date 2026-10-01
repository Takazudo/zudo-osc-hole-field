import unittest
import numpy as np
from scripts.pcbgen.gh_foot_trial import field,energy,height_interval_upper


class GHFootTrialTests(unittest.TestCase):
    def test_normal_traces_divergence_and_exact_volume_energy(self):
        nodes,weights=np.polynomial.legendre.leggauss(3)
        for length,inlet,start in ((.25,.1,0.),(.25,.1,.075),(.25,.25,0.)):
            w=.15;h=.05;rho=.0002
            args=dict(width=w,length=length,inlet_length=inlet,inlet_start=start,height=h)
            total=top=bottom=0.
            cuts=sorted(set((0.,start,start+inlet,length)))
            for a,b in zip(cuts,cuts[1:]):
                x=(a+b)/2+nodes*(b-a)/2;z=(nodes+1)*h/2
                jx,jz=field(x[:,None],z[None,:],**args)
                total+=rho*w*(weights[:,None]*weights[None,:]*(jx*jx+jz*jz)).sum()*(b-a)*h/4
                top+=w*(weights*field(x,h,**args)[1]).sum()*(b-a)/2
                bottom-=w*(weights*field(x,0.,**args)[1]).sum()*(b-a)/2
                at=(a+b)/2;delta=min((b-a)/10,h/10)
                dx=(field(at+delta,h/2,**args)[0]-field(at-delta,h/2,**args)[0])/(2*delta)
                dz=(field(at,h/2+delta,**args)[1]-field(at,h/2-delta,**args)[1])/(2*delta)
                self.assertAlmostEqual(float(dx+dz),0.,places=9)
            self.assertAlmostEqual(top,-1.,places=13);self.assertAlmostEqual(bottom,1.,places=13)
            self.assertEqual(float(field(0.,h/2,**args)[0]),0.)
            self.assertEqual(float(field(length,h/2,**args)[0]),0.)
            self.assertAlmostEqual(total,energy(rho=rho,**args)['total_ohm'],places=14)

    def test_positive_height_is_required_and_interval_bound_is_conservative(self):
        args=dict(width=.15,length=.25,inlet_length=.1,inlet_start=0.,rho=.0002)
        bound=height_interval_upper(minimum_height=.025,maximum_height=.075,**args)
        for height in np.linspace(.025,.075,31):self.assertLessEqual(energy(height=height,**args)['total_ohm'],bound*(1+1e-14))
        with self.assertRaisesRegex(ValueError,'positive bounded'):height_interval_upper(minimum_height=0.,maximum_height=.075,**args)
        uniform=energy(width=1.,length=1.,inlet_length=1.,inlet_start=0.,height=1.,rho=1.)
        self.assertEqual(uniform['total_ohm'],1.);self.assertEqual(uniform['lateral_ohm'],0.)


if __name__=='__main__':unittest.main()
