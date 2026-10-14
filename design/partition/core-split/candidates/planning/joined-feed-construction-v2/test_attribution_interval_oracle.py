"""Independent exact-rational oracles on bounded synthetic matrices only.

These checks validate enclosure logic, never production fit or real operators.
The oracle uses Fraction Gaussian elimination, not the certificate recurrence.
"""
from fractions import Fraction as Q
import unittest

import numpy as np
import scipy.sparse as sp

import attribution_resolution as V
import attribution_uniqueness as U
from attribution_transport import Budget


def exact(x):
    return Q(*x.as_integer_ratio()) if hasattr(x, 'as_integer_ratio') else Q(int(x))


def inverse(values):
    n = len(values)
    rows = [[exact(v) for v in row] + [Q(i == j) for j in range(n)]
            for i, row in enumerate(values)]
    for k in range(n):
        pivot = next(i for i in range(k, n) if rows[i][k])
        rows[k], rows[pivot] = rows[pivot], rows[k]
        divisor = rows[k][k]
        rows[k] = [x / divisor for x in rows[k]]
        for i in range(n):
            if i != k:
                multiple = rows[i][k]
                rows[i] = [x - multiple*y for x, y in zip(rows[i], rows[k])]
    return [row[n:] for row in rows]


def infnorm(rows):
    return max(sum(map(abs, row)) for row in rows)


class ExactIntervalOracles(unittest.TestCase):
    def enclosed(self, interval, value):
        self.assertLessEqual(exact(interval[0]), value)
        self.assertGreaterEqual(exact(interval[1]), value)

    def test_rounding_and_subnormal_arithmetic(self):
        tiny = np.nextafter(0., 1.)
        values = [tiny, -tiny, 0., .1, -.3, 1e-200, 1e100]
        for a in values:
            for b in values:
                self.enclosed(U.add((a,a), (b,b)), exact(a)+exact(b))
                self.enclosed(U.sub((a,a), (b,b)), exact(a)-exact(b))
                self.enclosed(U.mul((a,a), (b,b)), exact(a)*exact(b))
        for a in values:
            for b in (.1, 3., 1e100):
                self.enclosed(U.div_positive((a,a), (b,b)), exact(a)/exact(b))

    def test_exact_inverse_and_bordered_schur_random_integer_cases(self):
        rng = np.random.default_rng(93451)
        for _ in range(30):
            m = rng.integers(-3,4,(5,5))
            a = m.T@m + np.eye(5,dtype=int)*2
            b = rng.integers(-3,4,(5,2))
            d = np.eye(2,dtype=int)*20
            cert = U.certify(sp.csr_matrix(a,dtype=float), {'oracle':True}, {'oracle':True},
                             border=(b.astype(float),d.astype(float)))
            inv = inverse(a)
            self.assertGreaterEqual(exact(cert['inverse_infinity_upper']), infnorm(inv))
            for i in range(2):
                for j in range(2):
                    value = exact(d[i,j])-sum(exact(b[p,i])*inv[p][q]*exact(b[q,j])
                                              for p in range(5) for q in range(5))
                    self.enclosed(cert['schur_intervals'][i][j], value)

    def test_coupled_block_inverse_and_selected_residual_bound(self):
        a = np.array([[3.,-1.],[-1.,2.]])
        b = np.array([[-1.],[-.5]])
        d = np.array([[2.]])
        certs = {}
        for tag in ('KA','KB'):
            certs[tag] = U.certify(sp.csr_matrix(a), {'board':tag}, {'board':tag}, border=(b,d))
            certs[tag]['B_infinity_upper'], certs[tag]['BT_infinity_upper'] = V.matrix_norms(b)
        coupled = U.certify_coupled(certs['KA']['schur_intervals'],certs['KB']['schur_intervals'],.25,[True],U.Work())
        h = np.zeros((6,6))
        h[:2,:2] = h[2:4,2:4] = a
        h[:2,4] = h[4,:2] = b[:,0]
        h[2:4,5] = h[5,2:4] = b[:,0]
        h[4:,4:] = [[6.,-4.],[-4.,6.]]
        inv = inverse(h)
        bound = V.network_inverse_bound(certs,coupled)
        self.assertGreaterEqual(exact(bound), infnorm(inv))
        x = np.array(['.1000000000000000001','.2','.3','.4','.5','.6'],dtype=np.longdouble)
        rhs = np.array([0.,0.,1.,0.,0.,0.])
        residual = [exact(rhs[i])-sum(exact(h[i,j])*exact(x[j]) for j in range(6)) for i in range(6)]
        reported = 0.
        for side in range(2):
            wire = U.mul(U.sub(V.pair(x[4+side]),V.pair(x[5-side])),(4.,4.))
            reported = max(reported,V.residual_bound(sp.csr_matrix(a),b,d,x[side*2:side*2+2],
                           x[4+side:5+side],rhs[side*2:side*2+2],[wire],Budget()))
        self.assertGreaterEqual(exact(reported),max(map(abs,residual)))
        delta = U.upper_mul(bound,reported)
        truth = [sum(inv[i][j]*exact(rhs[j]) for j in range(6)) for i in range(6)]
        self.assertGreaterEqual(exact(delta),max(abs(truth[i]-exact(x[i])) for i in range(6)))

    def test_longdouble_pair_and_local_functional_enclosures(self):
        x = np.array(['0.','.1000000000000000001','.3'],dtype=np.longdouble)
        for value in x:
            self.enclosed(V.pair(value),exact(value))
        m = sp.csr_matrix([[2.,-1.,-1.],[-1.,1.,0.],[-1.,0.,1.]])
        fixed = np.array([True,False,False])
        delta = .001
        energy = V.energy_interval(m,np.arange(3),x,delta,fixed,Budget())
        support = [(np.array([0,1]),np.array([.25,.75]))]
        terminal = np.array([np.longdouble('.4')])
        reaction = V.reaction_interval(m,np.array([0]),x,delta,fixed,support,terminal,.125,Budget())
        for sa in (-1,1):
            for sb in (-1,1):
                for st in (-1,1):
                    p = [Q(0),exact(x[1])+sa*exact(delta),exact(x[2])+sb*exact(delta)]
                    t = exact(terminal[0])+st*exact(delta)
                    e = sum(exact(m[i,j])*p[i]*p[j] for i in range(3) for j in range(3))
                    current = -p[1]-p[2]+Q(1,4)*(Q(3,4)*p[1]-t)/Q(1,8)
                    self.enclosed(energy,e)
                    self.enclosed(reaction,current)


if __name__ == '__main__':
    unittest.main()
