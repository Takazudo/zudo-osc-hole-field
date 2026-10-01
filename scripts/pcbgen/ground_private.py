"""Shared native GH courtyard copper; one barrel per physical via."""
import math
import numpy as np
import shapely
from shapely.geometry import Point,box
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
from scripts.pcbgen.ground_access import strip,annular_access

def alternative_conductance(impedance,wire_ohm,omit=None):
    z=np.asarray(impedance,dtype=float)
    indices=[i for i in range(len(z)) if i!=omit]
    if not indices:return 0.
    matrix=z[np.ix_(indices,indices)]+np.eye(len(indices))*wire_ohm
    return float(np.ones(len(indices))@np.linalg.solve(matrix,np.ones(len(indices))))

def header_network(ref,copper,court,ports,bridge,hole,common_anchor,pitch,sheet,barrel):
    copper=shapely.intersection(copper,court);x0,y0,x1,y1=court.bounds
    nx=math.floor((x1-x0)/pitch);ny=math.floor((y1-y0)/pitch)
    xx,yy=np.meshgrid(x0+np.arange(nx)*pitch,y0+np.arange(ny)*pitch)
    cells=shapely.box(xx,yy,xx+pitch,yy+pitch);mask=np.asarray(shapely.covers(copper,cells));index=np.full(mask.shape,-1,dtype=int);index[mask]=np.arange(mask.sum());n=int(mask.sum())
    if not n:raise ValueError('empty private whole-cell mesh '+ref)
    xy=np.column_stack(((xx+pitch/2)[mask],(yy+pitch/2)[mask]));diag=np.zeros(n);rows=[];cols=[];values=[]
    for dy,dx in ((0,1),(1,0)):
        a=index[:ny-dy,:nx-dx];b=index[dy:,dx:];ok=(a>=0)&(b>=0);a=a[ok];b=b[ok];g=1/sheet
        rows.extend(a);cols.extend(b);values.extend([-g]*len(a));rows.extend(b);cols.extend(a);values.extend([-g]*len(a));np.add.at(diag,a,g);np.add.at(diag,b,g)
    choices=[]
    centre=(bridge['x_mm'],bridge['y_mm'])
    for node in np.argsort(np.linalg.norm(xy-np.asarray(centre),axis=1))[:100]:
        proof=annular_access(copper,hole,bridge,tuple(xy[node]),sheet)
        if proof:choices.append((proof['ohm'],int(node),proof))
    if not choices:raise ValueError('no contained private annular-to-cell path '+ref)
    private_R,via_node,via_proof=min(choices,key=lambda x:x[0]);shared_R=private_R+barrel+common_anchor['access']['ohm'];diag[via_node]+=1/shared_R
    rows.extend(range(n));cols.extend(range(n));values.extend(diag);matrix=coo_matrix((values,(rows,cols)),shape=(n,n)).tocsc();_,labels=connected_components(matrix,directed=False);keep=labels==labels[via_node];mapping=np.full(n,-1,dtype=int);mapping[keep]=np.arange(keep.sum());matrix=matrix[keep][:,keep];factor=splu(matrix);electrodes=[]
    for port in ports:
        start=(port['x_mm'],port['y_mm']);patch=box(start[0]-.125,start[1]-.125,start[0]+.125,start[1]+.125)
        if not shapely.covers(copper,patch):raise ValueError('fixed 0.25mm GH contact patch not inside actual native copper '+ref+':'+port['pad'])
        choices=[]
        for node in np.argsort(np.linalg.norm(xy-np.asarray(start),axis=1))[:100]:
            if not keep[node]:continue
            proof=strip(copper,start,tuple(xy[node]),sheet,max_width=.25)
            if proof:choices.append((proof['ohm'],int(node),proof))
        if not choices:raise ValueError('private mesh lacks a contained pad-to-shared-via path '+ref+':'+port['pad'])
        resistance,node,proof=min(choices,key=lambda x:x[0]);electrodes.append({'pad':port['pad'],'node':node,'fixed_patch_centre_mm':start,'fixed_patch_size_mm':.25,'coupling_ohm':resistance,'coupling_path':proof})
    impedance=np.empty((len(ports),len(ports)));maximum_residual=0.
    for column,electrode in enumerate(electrodes):
        rhs=np.zeros(keep.sum());rhs[mapping[electrode['node']]]=1.;voltage=factor.solve(rhs);residual=float(np.max(np.abs(matrix@voltage-rhs)));maximum_residual=max(maximum_residual,residual)
        for row,other in enumerate(electrodes):impedance[row,column]=voltage[mapping[other['node']]]
        impedance[column,column]+=electrode['coupling_ohm']
    if maximum_residual>1e-6 or not np.allclose(impedance,impedance.T,rtol=1e-8,atol=1e-10):raise ValueError('private impedance residual/reciprocity failed '+ref)
    return {'ref':ref,'pads':[p['pad'] for p in ports],'physical_via_uuid':bridge['uuid'],'shared_barrel_ohm':barrel,'shared_exit_access_ohm':private_R+common_anchor['access']['ohm'],'private_exit_annular_path':via_proof,'common_exit_annular_path':common_anchor['access'],'common_interface_node':common_anchor['node'],'impedance_matrix_ohm':impedance.tolist(),'electrodes':electrodes,'mesh_pitch_mm':pitch,'mesh_component_cells':int(keep.sum()),'residual_A':maximum_residual,'scope':'One native B courtyard mesh and one physical barrel, retained once for all header contacts. Fixed native contact patches, finite coupling and actual In1 annular exit. Matrix includes shared access and mutual coupling; it is not a list of independent barrel resistors.'}
