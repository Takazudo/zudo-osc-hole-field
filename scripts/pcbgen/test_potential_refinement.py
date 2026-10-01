"""Retained C1450 cancellation case, with the original numerical gate."""
import json
import unittest
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import splu
from scripts.pcbgen.potential_refinement import refine


class PotentialRefinementTests(unittest.TestCase):
    def test_actual_failed_row_neighborhood(self):
        r=json.loads(Path('scripts/pcbgen/fixtures/potential-c1450-residual.json').read_text())
        matrix=csr_matrix(r['matrix']);rhs=np.asarray(r['rhs']);initial=np.asarray(r['initial'])
        self.assertGreater(np.max(abs(matrix@initial-rhs)),1e-8)
        factor=splu(matrix[1:,1:].tocsc())
        field,report=refine(matrix,rhs,factor,initial=initial)
        self.assertGreater(report['last_pre_correction_extended_residual_A'],1e-8)
        self.assertEqual(report['corrections'],1)
        self.assertLess(np.max(abs(matrix@field-rhs)),1e-8)
        self.assertLess(np.max(abs(matrix.astype(np.longdouble)@field.astype(np.longdouble)-rhs)),1e-8)
        self.assertEqual(field[0,0],0.)


if __name__=='__main__':unittest.main()
