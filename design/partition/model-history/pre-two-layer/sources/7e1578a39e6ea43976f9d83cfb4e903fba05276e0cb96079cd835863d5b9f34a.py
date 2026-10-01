"""Restricted continuous potential witnesses for finite wetted terminals.

A constant trial over possible contact metal is an admissible lower-bound
restriction. It does not declare that the real PCB pad is equipotential.
"""
import numpy as np
import shapely
from shapely.geometry import Polygon
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import splu


def restrict_wetted_terminals(conductor,terminals):
    """Tie every trial DOF touching each maximum wetted support.

    A terminal gives layer and maximum_wetting geometry. Intersected sheet
    triangles are made constant in their entirety. Any owned barrel flange
    intersecting that support has ALL its foil ports tied to the same value;
    the constant volume extension is then continuous through its full shell.
    This conservative trial restriction can only reduce the variational lower.
    """
    size=conductor.potential_matrix.shape[0]
    parent=np.arange(size)
    def root(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]];a=parent[a]
        return int(a)
    receipts=[]
    for terminal in terminals:
        layer=terminal['layer'];region=terminal['maximum_wetting']
        sheet=conductor.sheets[layer];P=conductor.projections[layer].tocsr()
        polygons=shapely.polygons(sheet.xy[sheet.triangles])
        touched=shapely.intersects(polygons,region)
        vertices=np.unique(sheet.triangles[touched])
        dofs=set(P[vertices].indices.tolist());barrels=[]
        for ib,(barrel,centre) in enumerate(conductor.barrels):
            if region.intersects(Polygon(barrel.interface_polygon(centre))):
                dofs.update(range(conductor.port_offsets[ib],conductor.port_offsets[ib+1]))
                barrels.append(ib)
        if not dofs:raise ValueError('wetted terminal has no represented physical copper')
        # Each declared terminal must retain its own potential trial variable.
        # Shared mesh support would lose the intended distinct-terminal witness.
        previous={root(d) for d in dofs}
        if any(previous.intersection(r['roots']) for r in receipts):
            raise ValueError('maximum wetted terminal trial supports overlap')
        representative=min(previous)
        for d in previous:parent[d]=representative
        receipts.append({'ref':terminal['ref'],'layer':layer,'roots':{representative},
            'tied_original_dofs':len(dofs),'tied_barrels':barrels,
            'maximum_wetting_geojson':shapely.geometry.mapping(region)})
    labels=np.array([root(i) for i in range(size)])
    _,groups=np.unique(labels,return_inverse=True)
    if groups[0]!=0:raise ValueError('restricted potential gauge is not preserved')
    Q=coo_matrix((np.ones(size),(np.arange(size),groups)),shape=(size,int(groups.max())+1)).tocsc()
    K=conductor.potential_matrix
    reduced=Q.T@K@Q
    # Binary Q is exact; enclose signed sparse accumulation using absolute
    # factors before cancellation. Charge differences from the gauge so the
    # physically constant trial remains a zero-energy field.
    maximum_group=int(np.bincount(groups).max())
    gamma=(32+4*maximum_group)*np.finfo(float).eps
    allowance=np.nextafter(gamma*np.asarray(Q.T@(abs(K)@np.ones(size))).ravel(),np.inf)
    n=len(allowance);ids=np.arange(n)
    reduced+=diags(allowance,format='csc')+coo_matrix((
        np.r_[-allowance,-allowance,allowance.sum()],
        (np.r_[ids,np.zeros(n,dtype=int),0],np.r_[np.zeros(n,dtype=int),ids,0])),shape=(n,n)).tocsc()
    conductor.projections=[P@Q for P in conductor.projections]
    conductor.potential_matrix=reduced.tocsc()
    conductor.potential_factor=splu(reduced[1:,1:].tocsc())
    for row in receipts:row.pop('roots')
    return {'status':'Restricted H1 trial only; no physical equipotential PCB claim',
        'original_dofs':size,'restricted_dofs':n,'terminals':receipts,
        'maximum_restriction_formation_allowance_S':float(max(allowance))}
