"""Row-specific sparse contraction enclosures for a fixed-gauge trial field.

Only the residual-work product V.T R omits its exactly zero gauge coefficient.
The separate full equation-residual gate must still include that row.
"""
import numpy as np


class ResidualWork:
    def __init__(self, matrix):
        self.matrix = matrix
        self.absolute = abs(matrix)
        # CSC matvec accumulates contributions to rows; a dense gauge COLUMN
        # does not give every other row the gauge row's operation count.
        row_counts = np.diff(matrix.tocsr().indptr)
        self.operations = 2*row_counts + 64
        ld = np.longdouble
        product = self.operations.astype(ld) * ld(np.finfo(float).eps)
        if np.any(product >= .5): raise ValueError('sparse contraction error count is unsupported')
        self.gamma = product / (1-product)

    def one_norm(self, field, rhs, source_relative_error=0.):
        field, rhs = np.asarray(field, dtype=float), np.asarray(rhs, dtype=float)
        if field.shape != rhs.shape or field.ndim != 2 or field.shape[0] != self.matrix.shape[0]:
            raise ValueError('residual-work field/source shape mismatch')
        if np.any(field[0] != 0.): raise ValueError('residual-work gauge coefficient is not exactly zero')
        if not np.isfinite(field).all() or not np.isfinite(rhs).all() or not np.isfinite(source_relative_error) or source_relative_error < 0:
            raise ValueError('finite residual-work inputs required')
        ld = np.longdouble; eps = ld(np.finfo(float).eps); tiny = ld(np.finfo(float).tiny)
        evaluated = self.matrix @ field
        residual = evaluated-rhs
        positive = self.absolute @ abs(field)
        if not np.isfinite(evaluated).all() or not np.isfinite(positive).all():
            raise ValueError('sparse contraction overflow')
        operations = self.operations[:, None].astype(ld)
        gamma = self.gamma[:, None]
        underflow = operations*tiny
        # First bound the true positive absolute dot product; its rounded
        # evaluation cannot be silently assumed upward. No later multiplier
        # can amplify an uncharged product-underflow term.
        positive_upper = (positive.astype(ld)+underflow)/(1-gamma)
        positive_upper *= 1+8*np.finfo(ld).eps
        contraction = gamma*positive_upper+underflow
        subtraction = eps/(1-eps)*(abs(evaluated).astype(ld)+abs(rhs).astype(ld))+tiny
        source = ld(source_relative_error)*abs(rhs).astype(ld)
        total = abs(residual).astype(ld)+contraction+subtraction+source
        # v_0 is identically zero for EVERY profile, so every term involving
        # residual row 0 vanishes in V.T R, including its formation enclosure.
        count = len(total)-1
        summation_gamma = (count+16)*np.finfo(ld).eps
        norm = np.sum(total[1:], axis=0, dtype=ld)/(1-summation_gamma)
        result = np.nextafter(np.asarray(norm, dtype=float), np.inf)
        return result, {'full_equation_residual_A': float(abs(residual).max()),
            'maximum_row_operation_count': int(max(self.operations)),
            'gauge_row_operation_count': int(self.operations[0]),
            'maximum_nongauge_row_operation_count': int(max(self.operations[1:])),
            'maximum_evaluated_nongauge_residual_L1_A': float(np.sum(abs(residual[1:]),axis=0).max()),
            'maximum_matvec_roundoff_L1_A': float(np.sum(contraction[1:],axis=0,dtype=ld).max()),
            'maximum_subtraction_roundoff_L1_A': float(np.sum(subtraction[1:],axis=0,dtype=ld).max()),
            'maximum_source_roundoff_L1_A': float(np.sum(source[1:],axis=0,dtype=ld).max()),
            'gauge_work_omitted_only_because_trial_coefficient_is_exact_zero': True}
