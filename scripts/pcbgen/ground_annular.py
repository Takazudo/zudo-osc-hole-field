"""Finite polar annular copper and a single shared sector barrel network.

The unknown stack depths use full board thickness for each adjacent axial
link. Barrel angular links are omitted; this removes useful conductance.
Plane meshes must exclude the modeled disk before adding outer-rim ports.
"""
import math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu


def polar_network(r_inner,r_outer,sheet,rho,barrel_copper,board_thickness,
                  angles,ports,radial_cells=4):
    """Return port admittance for finite annular sectors on active layers.

    ports is [(layer, angle, external_strip_R, fixed_arc_width), ...]. Angles include every
    physical port angle. Copper support and strip ownership are caller gates.
    No barrel sector or annular copper conductance is independently repeated.
    """
    if len({p[0] for p in ports})!=len(ports):raise ValueError('one fixed outer-rim port per layer required')
    angles=sorted(set(float(a)%(2*math.pi) for a in angles))
    ntheta=len(angles);layers=sorted({p[0] for p in ports});nr=radial_cells
    edges=np.geomspace(r_inner,r_outer,nr+1);centres=np.sqrt(edges[:-1]*edges[1:])
    deltas=[(angles[(i+1)%ntheta]-angles[i])%(2*math.pi) for i in range(ntheta)]
    widths=[(deltas[i-1]+deltas[i])/2 for i in range(ntheta)]
    # Each layer has one barrel-face angular row plus finite annular rows.
    polar_size=len(layers)*(nr+1)*ntheta;size=polar_size+sum(p[2]>0 for p in ports)+len(ports);diagonal=np.zeros(size);rows=[];columns=[];values=[]
    def node(layer,radial,angular):return layers.index(layer)*(nr+1)*ntheta+radial*ntheta+angular
    def link(a,b,resistance):
        if resistance<=0:raise ValueError('polar conductor has nonpositive finite R')
        g=1/resistance;rows.extend((a,b));columns.extend((b,a));values.extend((-g,-g));diagonal[a]+=g;diagonal[b]+=g
    for layer in layers:
        for i,theta_width in enumerate(widths):
            link(node(layer,0,i),node(layer,1,i),sheet*math.log(centres[0]/r_inner)/theta_width)
            for j in range(nr-1):link(node(layer,j+1,i),node(layer,j+2,i),sheet*math.log(centres[j+1]/centres[j])/theta_width)
        for j in range(nr):
            radial_log=math.log(edges[j+1]/edges[j])
            for i,delta in enumerate(deltas):link(node(layer,j+1,i),node(layer,j+1,(i+1)%ntheta),sheet*delta/radial_log)
    for a,b in zip(layers,layers[1:]):
        # Active layers may skip an inner layer: charging full thickness still
        # bounds that physical span, without assuming a selected dielectric.
        for i,width in enumerate(widths):link(node(a,0,i),node(b,0,i),rho*board_thickness/(barrel_copper*r_inner*width))
    terminal_nodes=[];next_patch=polar_size
    def angular_overlap(centre,left,right,port_centre,port_width):
        total=0.
        for shift in (-2*math.pi,0.,2*math.pi):
            lo=max(centre-left,port_centre+shift-port_width/2);hi=min(centre+right,port_centre+shift+port_width/2)
            total+=max(0.,hi-lo)
        return min(left+right,total)
    for i,(layer,angle,access,arc_width) in enumerate(ports):
        if not 0<arc_width<=2*math.pi or access<0:raise ValueError('invalid finite outer-rim patch')
        terminal=size-len(ports)+i;patch=next_patch if access>0 else terminal;next_patch+=int(access>0);terminal_nodes.append(terminal)
        # The fixed physical arc is partitioned across sectors as N changes.
        # Its one external strip is charged once after their shared patch.
        for angular in range(ntheta):
            overlap=angular_overlap(angles[angular],deltas[angular-1]/2,deltas[angular]/2,angle%(2*math.pi),arc_width)
            if overlap>1e-12:link(node(layer,nr,angular),patch,sheet*math.log(r_outer/centres[-1])/overlap)
        if access>0:link(patch,terminal,access)
    rows.extend(range(size));columns.extend(range(size));values.extend(diagonal);matrix=coo_matrix((values,(rows,columns)),shape=(size,size)).tocsc();interior=np.arange(size-len(ports));terminals=np.asarray(terminal_nodes)
    interior_matrix=matrix[interior][:,interior];coupling=matrix[interior][:,terminals].toarray();factor=splu(interior_matrix);response=factor.solve(coupling);admittance=matrix[terminals][:,terminals].toarray()-coupling.T@response
    if not np.allclose(admittance,admittance.T,atol=1e-10) or np.max(np.abs(admittance.sum(axis=1)))>1e-8:raise ValueError('polar reduction lost reciprocity/current conservation')
    return admittance,{'angular_sectors':ntheta,'radial_cells':nr,'inner_radius_mm':r_inner,'outer_radius_mm':r_outer,'active_layers':layers,'barrel_angular_links':'omitted: unknown minimum axial copper-band height','axial_link_length_mm':board_thickness,'single_physical_barrel_sector_columns':ntheta,'finite_polar_node_count':size,'admittance_S':admittance.tolist()}


def two_terminal_resistance(admittance):
    if admittance.shape!=(2,2):raise ValueError('two terminal benchmark expected')
    return 1/float(admittance[0,0])
