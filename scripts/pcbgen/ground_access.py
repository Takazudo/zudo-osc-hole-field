"""Finite conductor-contained access paths for the resistance mesh.

All returned paths are analytical current strips inside existing copper;
this module writes no traces or board geometry.
"""
import math
import shapely
from shapely.geometry import LineString,Point

def strip(copper,start,end,sheet,max_width=.25,flat=False):
    if math.dist(start,end)<1e-10:return {'ohm':0.,'length_mm':0.,'width_mm':max_width,'points':[start,end]}
    paths=([start,end],[start,(start[0],end[1]),end],[start,(end[0],start[1]),end])
    best=None
    for points in paths:
        points=[p for i,p in enumerate(points) if i==0 or p!=points[i-1]];line=LineString(points);width=max_width
        while width>=.02:
            # Round joins retain material at every corner. The complete
            # capsule, including both endpoints, must stay inside copper.
            if shapely.covers(copper,line.buffer(width/2,quad_segs=8,cap_style='flat' if flat else 'round')):
                proposal={'ohm':sheet*line.length/width,'length_mm':line.length,'width_mm':width,'points':points}
                if best is None or proposal['ohm']<best['ohm']:best=proposal
                break
            width/=2
    return best

def annular_access(copper,hole,bridge,end,sheet):
    centre=(bridge['x_mm'],bridge['y_mm']);distance=math.dist(centre,end)
    if not distance:return None
    direction=((end[0]-centre[0])/distance,(end[1]-centre[1])/distance)
    ray=LineString([centre,end]);inside=shapely.intersection(ray,hole)
    if inside.is_empty:return None
    exit_radius=max(math.dist(centre,p) for p in shapely.get_coordinates(inside))
    annulus=bridge['annular_width_mm']-.002 # native pad polygon is an inside1um approximation
    if annulus<=.004:return None
    # A supported complete annular band is required. The 4um inner
    # tolerance covers the exported inside-polygon and hole envelopes;
    # its finite radial transfer is charged explicitly.
    inner=hole.buffer(.004,quad_segs=32);outer=hole.buffer(annulus,quad_segs=32)
    support=shapely.difference(outer,inner)
    if not shapely.covers(copper,support):return None
    radius=min(distance,exit_radius+annulus/2);start=(centre[0]+direction[0]*radius,centre[1]+direction[1]*radius)
    path=strip(copper,start,end,sheet,max_width=min(.25,annulus/2))
    if path is None:return None
    # Charge half-circumference redistribution around the minimum annulus,
    # rather than making its plated barrel an ideal in-plane junction.
    ring=sheet*(hole.length+2*math.pi*annulus)/(annulus-.004)+sheet*.004/.02
    return {**path,'annular_ohm':ring,'ohm':path['ohm']+ring,'annular_width_mm':annulus,'hole_exit_radius_mm':exit_radius,'metal_start_mm':start,'complete_annular_band_contained':True,'radial_tolerance_mm':.004,'annular_bound':'full supported ring circumference plus finite 4um radial transfer'}

def rim_access(actual,retained,disk,centre,radius,end,sheet,width=.1):
    """Fixed right-facing rim arc, finite owned radial wedge and flat strip.

    The annular disk belongs to the polar model. The outside wedge/strip is
    paid once; callers reject overlap between different access conductors.
    """
    from shapely.geometry import Polygon
    outer=radius+.075;half=math.asin(width/(2*outer));angle_width=2*half
    # A complete native band certifies the <=polygon-envelope radial gap
    # between the analytic rim and the conservative excluded disk.
    rim_gap=radius*(1/math.cos(math.pi/128)-1)+2e-6
    inner=radius+rim_gap
    steps=32;angles=[-half+2*half*i/steps for i in range(steps+1)]
    coordinates=[(centre[0]+outer*math.cos(a),centre[1]+outer*math.sin(a)) for a in angles]+[(centre[0]+inner*math.cos(a),centre[1]+inner*math.sin(a)) for a in reversed(angles)]
    wedge=Polygon(coordinates)
    if not shapely.covers(actual,wedge):return None
    start=(centre[0]+outer*math.cos(half),centre[1]);paths=([start,end],[start,(start[0],end[1]),end],[start,(end[0],start[1]),end]);best=None
    for points in paths:
        points=[p for i,p in enumerate(points) if i==0 or p!=points[i-1]]
        if len(points)<2:continue
        line=LineString(points);tube=line.buffer(width/2,cap_style='flat',join_style='round',quad_segs=16)
        if not shapely.covers(retained,tube):continue
        geometry=shapely.union_all([wedge,tube]);corners=max(0,len(points)-2)
        resistance=sheet*math.log(outer/radius)/angle_width+sheet*line.length/width+corners*sheet*math.pi/2
        proposal={'ohm':resistance,'strip_length_mm':line.length,'strip_width_mm':width,'fixed_outer_rim_angle_rad':0.,'fixed_outer_rim_arc_width_rad':angle_width,'modeled_arc_chord_width_mm':2*radius*math.sin(half),'points':points,'radial_wedge_outer_radius_mm':outer,'finite_polygon_gap_mm':rim_gap,'corner_bound_ohm':corners*sheet*math.pi/2,'geometry':geometry}
        if best is None or resistance<best['ohm']:best=proposal
    return best
