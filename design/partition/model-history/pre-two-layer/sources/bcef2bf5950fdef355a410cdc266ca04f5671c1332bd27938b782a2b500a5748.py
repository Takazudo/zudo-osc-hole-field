"""Finite strand/solder transfer trial for an unselected factory contact class.

This is a computable conditional geometry, not a supplier capability, actual
uniform pad injection, or a manufactured resistance measurement.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point,box,Polygon
from scipy.optimize import linear_sum_assignment
from scipy.sparse.linalg import spsolve
from scripts.pcbgen.sheet_mesh import Sheet,make_cells
from scripts.pcbgen.sheet_flux import FluxSheet
from scripts.pcbgen.conserved_flow import FlowForest


def specification():
    return json.loads(Path('design/partition/contact-transfer-proposal.json').read_text())['main_strand_class']


def main_contact_supports(centre):
    """Nineteen equal-area supports, in solid spaces of the source 5x5 array."""
    spec=specification();positions=spec['support_centres_relative_to_land_mm'];half=spec['square_support_side_mm']/2
    patches=[box(*(round(v,9) for v in (centre[0]+x-half,centre[1]+y-half,
                                      centre[0]+x+half,centre[1]+y+half))) for x,y in positions]
    union=shapely.union_all(patches)
    if abs(union.area-spec['strand_count']*(2*half)**2)>1e-10:raise ValueError('strand solder supports overlap')
    return patches


def extruded_vertical_current(z,height,top_density,bottom_density):
    """z=0 bottom, z=h top; div(j_xy)=top_density-bottom_density."""
    return -bottom_density-(top_density-bottom_density)*np.asarray(z)/height


def fan_geometry():
    """Two smoothstep transports with determinant 1 and disjoint horizontal cores.

    For each stage r(t)=a+(3t²-2t³)(b-a), z=H*t. Normal traces
    at both ends are uniform axial current because r'(0)=r'(1)=0.
    The coordinate z here follows the wire toward the PCB.
    """
    spec=specification();pitch=spec['root_hex_pitch_mm'];theta=math.radians(spec['root_hex_rotation_deg'])
    rotation=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
    root=np.array([(pitch*(q+r/2),pitch*math.sqrt(3)*r/2) for q in range(-2,3) for r in range(-2,3)
                   if max(abs(q),abs(r),abs(q+r))<=2])@rotation.T
    expanded=root*spec['expanded_hex_pitch_mm']/pitch
    targets=np.array(spec['support_centres_relative_to_land_mm'])
    _,order=linear_sum_assignment(np.sum((expanded[:,None]-targets[None])**2,axis=2))
    tips=targets[order]
    heights=[spec['initial_expansion_height_mm'],spec['main_fan_height_mm']]
    lengths=np.full(len(root),spec['redistribution_tip_height_mm']);excess=np.zeros(len(root));minimum=math.inf
    for a,b,height in zip((root,expanded),(expanded,tips),heights):
        delta=b-a;squares=np.sum(delta*delta,axis=1)
        # Jensen plus integral_0^1 (6t-6t²)^2 dt =6/5.
        lengths+=np.sqrt(height*height+1.2*squares)
        excess+=1.2*squares/height
        for i in range(len(a)):
            for j in range(i):
                start=a[i]-a[j];change=delta[i]-delta[j]
                w=float(np.clip(-start@change/(change@change),0.,1.)) if change@change else 0.
                minimum=min(minimum,float(np.linalg.norm(start+w*change)))
    radius=spec['minimum_copper_core_diameter_mm']/2
    if minimum<=2*radius or max(lengths)>spec['maximum_fanned_length_per_end_mm']:
        raise ValueError('conditional transported strand cores overlap or exceed source length')
    return {'root_xy_mm':root.tolist(),'expanded_xy_mm':expanded.tolist(),'tip_xy_mm':tips.tolist(),
        'strand_arclength_upper_mm':lengths.tolist(),'maximum_arclength_upper_mm':float(max(lengths)),
        'minimum_same_height_centre_separation_mm':minimum,'minimum_owned_core_gap_mm':minimum-2*radius,
        'transport_jacobian_determinant':1.,'stage_heights_mm':heights,
        'strand_added_bending_energy_length_mm':excess.tolist(),
        'normal_trace':'Each stage has zero endpoint transverse slope. Axial current and polygon section match the next stage and tip exactly.',
        'physical_scope':'Actual copper must contain these explicit horizontal transported core polygons. Nominal wire diameter alone does not qualify the bent geometry.'}


def main_strand_trial(pitch=.025):
    # Proposed lower strand diameter and upper hot material classes require
    # physical qualification. Nominal 27 AWG geometry alone is not a tolerance.
    spec=specification()
    radius=spec['minimum_copper_core_diameter_mm']/2;rho_copper=spec['hot_copper_resistivity_upper_ohm_mm'];rho_solder=spec['hot_solder_resistivity_upper_ohm_mm']
    transition_height=spec['redistribution_tip_height_mm'];solder_height=spec['solder_height_upper_mm'];fan_length=spec['maximum_fanned_length_per_end_mm'];count=spec['strand_count']
    section=Polygon([(round(x,9),round(y,9)) for x,y in Point(0,0).buffer(radius-.000001,quad_segs=16).exterior.coords])
    half=spec['square_support_side_mm']/2;support=box(-half,-half,half,half)
    sheet=Sheet(section,make_cells(section.bounds,pitch,pitch),rho_copper/transition_height,
                source_patches=[support])
    flux=FluxSheet(sheet,rho_copper/transition_height)
    if np.max(np.linalg.norm(sheet.xy,axis=1))>=radius:
        raise ValueError('strand trial leaves its guaranteed physical metal section')
    # Grid intersections can move a polygon edge by picometres. The trial
    # section is the actual conforming mesh union, still strictly inside the
    # guaranteed circular core. Transport this SAME section through the fan.
    section=shapely.union_all(sheet.polygons)
    section_area=section.area
    source=flux.area_current(section,1.)-flux.area_current(support,1.)
    rhs=flux.nodal_area_current(section,1.)-flux.nodal_area_current(support,1.)
    potential=np.zeros(len(sheet.xy));potential[1:]=spsolve(sheet.matrix[1:,1:],rhs[1:])
    result,current=flux.reconstruct(np.zeros(len(flux.edges)),potential,source)
    # The exact rational area sources have total 1-1=0. Preserve shared face
    # currents and enclose an exact spanning-tree conservation correction;
    # a small residual alone is not an admissible Thomson field certificate.
    ld=np.longdouble;local=flux.signs*current[flux.edge_ids]
    required=source.astype(ld)-np.sum(local.astype(ld),axis=1,dtype=ld)
    forest=FlowForest(flux.divergence)
    correction,width,_=forest.route(required,8*np.finfo(float).eps*np.sum(abs(source)))
    full=np.zeros(len(flux.edges),dtype=ld);full[flux.internal]=correction[:,0]
    error=np.zeros(len(flux.edges),dtype=ld);error[flux.internal[forest.edges]]=width[0]
    change=abs(full[flux.edge_ids])+error[flux.edge_ids]
    mass=abs(flux.mass).astype(ld)
    correction_energy=np.einsum('ti,tij,tj->',change,mass,change)
    trial_energy=np.einsum('ti,tij,tj->',local.astype(ld),flux.mass.astype(ld),local.astype(ld))
    absolute_energy=np.einsum('ti,tij,tj->',abs(local).astype(ld),mass,abs(local).astype(ld))
    certified_energy=(np.sqrt(max(trial_energy,0))+np.sqrt(correction_energy))**2
    certified_energy+=128*np.finfo(float).eps*absolute_energy
    certified_energy=float(np.nextafter(np.float64(certified_energy),np.inf))
    # f is the TOP incoming density, g the BOTTOM outgoing density.
    # div(j)=f-g, Jxy=j/h and Jz=-g-(f-g)*z/h; div(J)=0.
    # The vertical Joule term includes the positive f*g cross term.
    vertical=rho_copper*transition_height/3*(1/support.area+2/section_area)
    solder=rho_solder*solder_height/support.area
    transition=certified_energy+vertical
    fan=rho_copper*fan_length/section_area
    straight_tip=rho_copper*transition_height/section_area
    excess_transition=transition-straight_tip
    if excess_transition<0:raise ValueError('redistribution charge fell below straight-wire baseline')
    fan_geometry_receipt=fan_geometry()
    # Each strand carries I/19. The shear-field bending charge is explicit;
    # rho*L/A is not silently substituted for the actual transported trial.
    bending=rho_copper/section_area*sum(fan_geometry_receipt['strand_added_bending_energy_length_mm'])/count**2
    return {'status':'UNSELECTED conditional finite contact trial; physical geometry/material/interface qualification NOT RUN #65',
        'strand_count':count,'strand_minimum_diameter_mm':2*radius,
        'strand_current_section':'Contained conforming polygon section, uniform 1/19 A; the identical section is transported through the fan. Remaining physical strand copper carries zero trial current.',
        'strand_current_section_geojson':shapely.geometry.mapping(section),
        'minimum_effective_copper_area_mm2':count*section_area,
        'solder_support_size_mm':[.24,.24],'solder_height_upper_mm':solder_height,
        'copper_redistribution_height_mm':transition_height,'fan_length_upper_mm':fan_length,
        'rho_copper_hot_upper_ohm_mm':rho_copper,'rho_solder_hot_upper_ohm_mm':rho_solder,
        'one_terminal_fan_copper_ohm':fan/count,
        'one_terminal_copper_redistribution_ohm':transition/count,
        'one_terminal_tip_straight_wire_baseline_ohm':straight_tip/count,
        'one_terminal_added_redistribution_ohm':excess_transition/count,
        'one_terminal_added_fan_bending_ohm':bending,
        'one_terminal_solder_ohm':solder/count,
        'two_terminal_added_transfer_ohm':2*((excess_transition+solder)/count+bending),
        'assembled_bulk_wire_hot_ceiling_ohm_per_m':.013,
        'fan_copper_hot_upper_ohm_per_m':rho_copper*1000/(count*section_area),
        'wire_length_accounting':'Each <=4 mm fan includes its 0.1 mm redistribution tip and lies inside the existing 125 mm maximum branch-wire centreline length. The uniform copper baseline fits 13 mOhm/m. Add the explicit transported-core bending energy and tip redistribution above its straight-wire baseline to the termination charge. The full wire-length ceiling conservatively covers the fan projected length because actual arclength is longer.',
        'remaining_combined_termination_budget_ohm':.0002-2*((excess_transition+solder)/count+bending),
        'fan_geometry':fan_geometry_receipt,
        'interface_requirement':'Remaining positive termination allowance must cover actual metallurgical/interface transfer at BOTH ends; not assumed zero and not measured.',
        'pitch_mm':pitch,'maximum_current_residual_A':result['maximum_triangle_divergence_residual_A'],
        'tip_current_conservation_correction_energy_ohm':float(correction_energy),
        'tip_current_energy_numerical_addition_ohm':certified_energy-result['joule_upper_ohm'],
        'qualification_requirements':['19 nonoverlapping strand-core tubes within the declared fan length, with no unsupported sharp bend or reduced effective cross-section.',
            'Actual continuous solder support, hot resistivity/thickness and metallurgical interface limits; typical SAC305 literature values are not guarantees.',
            'All strand tips and supports fit solid native main-land copper outside all drill/barrel ownership regions; mechanical retention and anti-wicking qualification remain required.',
            'Actual external wire terminal voltage boundary and finite lead geometry; no equipotential PCB land or ring.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);parser.add_argument('--pitch-mm',type=float,default=.025)
    args=parser.parse_args();result=main_strand_trial(args.pitch_mm)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k.endswith('_ohm') or k.endswith('_ohm_per_m') or k=='maximum_current_residual_A'},indent=2))
