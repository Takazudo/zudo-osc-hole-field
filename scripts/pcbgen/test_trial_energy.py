"""Matrix allowances must cover nonstationary and corrected physical trials."""
import unittest
import numpy as np
from scripts.pcbgen.trial_energy import residual_work_diagonal,conserving_upper


class TrialEnergyTests(unittest.TestCase):
    def test_residual_work_encloses_actual_nonstationary_grams(self):
        rng=np.random.default_rng(3801);a=rng.normal(size=(19,19));K=a.T@a+np.eye(19)
        B=rng.normal(size=(19,5));V=np.linalg.solve(K,B)+.01*rng.normal(size=B.shape)
        residual=K@V-B;diagonal=residual_work_diagonal(abs(V).max(axis=0),abs(residual).sum(axis=0))
        stationary=(B.T@V+V.T@B)/2
        primal=B.T@V+V.T@B-V.T@K@V;energy=V.T@K@V
        self.assertGreaterEqual(np.linalg.eigvalsh(primal-(stationary-np.diag(diagonal))).min(),-1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(stationary+np.diag(diagonal)-energy).min(),-1e-12)

    def test_young_psd_bound_covers_shared_correction_cross_terms(self):
        rng=np.random.default_rng(3819);field=rng.normal(size=(31,4));correction=.001*rng.normal(size=field.shape)
        gram=field.T@field;e=np.sum(correction**2,axis=0)
        upper,receipt=conserving_upper(gram,e)
        actual=(field+correction).T@(field+correction)
        self.assertGreater(np.linalg.eigvalsh(upper-actual).min(),0)
        self.assertGreater(receipt['young_eta'],0)


if __name__=='__main__':unittest.main()
