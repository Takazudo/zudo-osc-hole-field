"""PSD allowances for residual work and sums of current correction fields."""
import numpy as np


def residual_work_diagonal(field_maximum,residual_one_norm):
    """Gershgorin enclosure of sym(V.T R), without retaining all columns."""
    v=np.asarray(field_maximum,dtype=float);r=np.asarray(residual_one_norm,dtype=float)
    if np.any(v<0) or np.any(r<0):raise ValueError('negative residual-work envelope')
    value=(v*np.sum(r)+r*np.sum(v))/2
    return np.nextafter(value*(1+16*len(v)*np.finfo(float).eps),np.inf)


def conserving_upper(trial_gram,correction_energy):
    """Young bound for every linear combination of the corrected trial basis."""
    gram=(trial_gram+trial_gram.T)/2
    E=len(gram)*np.asarray(correction_energy,dtype=float)
    if np.any(E<0):raise ValueError('negative current correction energy')
    eta=float(np.sqrt(E.sum()/max(np.trace(gram),np.finfo(float).tiny)))
    if not eta:return gram,{'young_eta':0.,'maximum_added_diagonal_ohm':0.}
    result=(1+eta)*gram+np.diag((1+1/eta)*E)
    return result,{'young_eta':eta,'maximum_added_diagonal_ohm':float(np.max(np.diag(result-gram))),
                  'maximum_correction_energy_ohm':float(np.max(correction_energy))}
