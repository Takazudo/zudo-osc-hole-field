"""Exact full-section foil-cut profiles; no actual geometry/process admission.

I_into>0 injects current into the conductor. Outward current is -I_into.
The only potential ansatz here is continuous P1 along the cut, constant through
foil depth. No area source, vertical source lift or arbitrary3D quadrature is
represented. Boundary topology and actual material/geometry require their own
source-bound witnesses; these helpers check the supplied finite geometry.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from types import MappingProxyType

POTENTIAL_ANSATZ='continuous_p1_constant_through_foil_depth'
CARDINAL=((F(1),F(0)),(F(-1),F(0)),(F(0),F(1)),(F(0),F(-1)))


def exact(value):
    if isinstance(value,bool):raise ValueError('finite exact numeric scalar required')
    try:return F(value)
    except (TypeError,ValueError,OverflowError,ZeroDivisionError) as exc:
        raise ValueError('finite exact numeric scalar required') from exc


def pair(values):
    if len(values)!=2:raise ValueError('two coordinates required')
    return tuple(map(exact,values))


def identity(value):
    if not isinstance(value,str) or not value.strip():raise ValueError('nonempty source identity required')
    return value


@dataclass(frozen=True)
class FoilCut:
    region_id: str
    cut_id: str
    foil_layer: str
    endpoints_mm: tuple
    depth_mm: tuple
    outward_normal_xy: tuple
    current_into_A: F
    kind: str='full_section_foil_cut'

    def __post_init__(self):
        identity(self.region_id);identity(self.cut_id)
        if self.kind!='full_section_foil_cut':raise ValueError('area electrode/source lift is not a foil cut')
        if self.foil_layer not in ('F.Cu','In1.Cu','In2.Cu','B.Cu'):raise ValueError('explicit physical foil required')
        if len(self.endpoints_mm)!=2:raise ValueError('two complete cut endpoints required')
        ends=tuple(pair(p) for p in self.endpoints_mm);depth=pair(self.depth_mm);normal=pair(self.outward_normal_xy)
        delta=tuple(ends[1][i]-ends[0][i] for i in range(2))
        if sum(d!=0 for d in delta)!=1:raise ValueError('positive axis-aligned cut width required')
        if depth[1]<=depth[0]:raise ValueError('positive complete foil depth required')
        if normal not in CARDINAL or sum(delta[i]*normal[i] for i in range(2)):
            raise ValueError('cardinal outward normal perpendicular to cut required')
        object.__setattr__(self,'endpoints_mm',ends);object.__setattr__(self,'depth_mm',depth)
        object.__setattr__(self,'outward_normal_xy',normal);object.__setattr__(self,'current_into_A',exact(self.current_into_A))

    @property
    def tangent_axis(self):return int(self.endpoints_mm[0][0]==self.endpoints_mm[1][0])
    @property
    def interval(self):return tuple(sorted(p[self.tangent_axis] for p in self.endpoints_mm))
    @property
    def width_mm(self):return self.interval[1]-self.interval[0]
    @property
    def thickness_mm(self):return self.depth_mm[1]-self.depth_mm[0]
    @property
    def outward_density_A_per_mm2(self):return -self.current_into_A/(self.width_mm*self.thickness_mm)
    @property
    def support_key(self):
        return self.foil_layer,self.depth_mm,tuple(sorted(self.endpoints_mm))

    def coordinate(self,point):
        p=pair(point);axis=self.tangent_axis
        if p[1-axis]!=self.endpoints_mm[0][1-axis]:raise ValueError('face is not on the complete cut plane')
        return p[axis]


@dataclass(frozen=True)
class CompiledCut:
    cut: FoilCut
    faces: tuple
    nodal_load_A: dict
    coordinates: dict

    def trace_values(self,values,ansatz):
        if ansatz!=POTENTIAL_ANSATZ:raise ValueError('only explicit depth-constant continuous P1 potential allowed')
        if set(values)!=set(self.nodal_load_A):raise ValueError('complete exact boundary potential node set required')
        return {key:exact(value) for key,value in values.items()}

    def weak_load(self,values,*,ansatz):
        v=self.trace_values(values,ansatz)
        return sum((coefficient*v[key] for key,coefficient in self.nodal_load_A.items()),F())

    def potential_at(self,coordinate,values,*,ansatz):
        v=self.trace_values(values,ansatz);x=exact(coordinate)
        for face in self.faces:
            lo,hi=face['interval'];a,b=face['nodes']
            if lo<=x<=hi:return ((hi-x)*v[a]+(x-lo)*v[b])/(hi-lo)
        raise ValueError('potential requested outside complete cut')


def compile_cut(cut,faces):
    """Exact full-face coverage and weak-load/current coefficients.

    Faces supply their adjacent interior point and singleton incidence as
    geometry/topology evidence. The future mesh adapter must derive these from
    actual mesh incidence; this primitive does not certify an unseen mesh.
    """
    if not isinstance(cut,FoilCut) or not faces:raise ValueError('typed nonempty foil cut required')
    rows=[];face_ids=set();node_coordinates={};coordinate_nodes={}
    for face in faces:
        face_id=identity(face['id'])
        if face_id in face_ids:raise ValueError('duplicate boundary face')
        face_ids.add(face_id)
        if type(face['boundary_incidence']) is not int or face['boundary_incidence']!=1:
            raise ValueError('a complete exterior boundary face is required')
        if (face['foil_layer']!=cut.foil_layer or pair(face['depth_mm'])!=cut.depth_mm
                or pair(face['outward_normal_xy'])!=cut.outward_normal_xy):
            raise ValueError('face foil/depth/normal differs from complete cut')
        if len(face['vertices'])!=2:raise ValueError('two boundary face endpoints required')
        entries=[]
        for name,xy in face['vertices']:
            identity(name);point=pair(xy);coordinate=cut.coordinate(point)
            if name in node_coordinates and node_coordinates[name]!=coordinate:raise ValueError('node has conflicting physical coordinates')
            if coordinate in coordinate_nodes and coordinate_nodes[coordinate]!=name:raise ValueError('P1 trace split at an unshared endpoint')
            node_coordinates[name]=coordinate;coordinate_nodes[coordinate]=name;entries.append((coordinate,name))
        entries.sort();(lo,a),(hi,b)=entries
        if lo>=hi or lo<cut.interval[0] or hi>cut.interval[1]:raise ValueError('partial/degenerate mesh face is not accepted')
        interior=pair(face['adjacent_interior_mm']);origin=cut.endpoints_mm[0]
        if sum((interior[i]-origin[i])*cut.outward_normal_xy[i] for i in range(2))>=0:
            raise ValueError('outward normal disagrees with adjacent conductor side')
        fraction=(hi-lo)/cut.width_mm
        rows.append({'id':face_id,'interval':(lo,hi),'nodes':(a,b),
                     'outward_current_A':-cut.current_into_A*fraction,'fraction':fraction})
    rows.sort(key=lambda x:x['interval'])
    if rows[0]['interval'][0]!=cut.interval[0] or rows[-1]['interval'][1]!=cut.interval[1]:
        raise ValueError('cut coverage misses an endpoint')
    if any(a['interval'][1]!=b['interval'][0] for a,b in zip(rows,rows[1:])):
        raise ValueError('cut coverage has a gap or overlap')
    weights={name:F() for name in node_coordinates}
    for row in rows:
        for node in row['nodes']:weights[node]+=cut.current_into_A*row['fraction']/2
    if sum(weights.values(),F())!=cut.current_into_A or sum((x['outward_current_A'] for x in rows),F())!=-cut.current_into_A:
        raise ValueError('complete cut current/load balance failed')
    return CompiledCut(cut,tuple(MappingProxyType(row) for row in rows),MappingProxyType(weights),MappingProxyType(node_coordinates))


def glue_cuts(left,right,left_values,right_values,*,ansatz):
    """Full normal-current and continuous potential traces, not net I alone."""
    a,b=left.cut,right.cut
    if a.region_id==b.region_id or a.cut_id==b.cut_id:raise ValueError('distinct region/cut identities required')
    if a.support_key!=b.support_key:raise ValueError('full physical section differs; an adapter is required')
    if tuple(-n for n in a.outward_normal_xy)!=b.outward_normal_xy:raise ValueError('opposite domain outward normals required')
    if a.current_into_A+b.current_into_A or a.outward_density_A_per_mm2+b.outward_density_A_per_mm2:
        raise ValueError('pointwise normal currents do not match')
    # Equal linear traces on the union of both breakpoint sets imply equality
    # everywhere along the cut, and the ansatz extends this through full depth.
    positions=set(left.coordinates.values())|set(right.coordinates.values())
    for x in positions:
        if left.potential_at(x,left_values,ansatz=ansatz)!=right.potential_at(x,right_values,ansatz=ansatz):
            raise ValueError('potential traces are not continuous on the full cut')
    work=left.weak_load(left_values,ansatz=ansatz)+right.weak_load(right_values,ansatz=ansatz)
    if work:raise ValueError('matched internal cut work did not cancel')
    return {'matched_full_normal_trace':True,'matched_depth_constant_potential_trace':True,'internal_weak_work_W':work}


@dataclass(frozen=True)
class RectangularFoil:
    """Analytic reference region, not a selected physical PCB component."""
    region_id: str
    foil_layer: str
    x_mm: tuple
    y_mm: tuple
    depth_mm: tuple
    rho_ohm_mm: F
    current_A: F
    flow_axis: int=0

    def __post_init__(self):
        identity(self.region_id)
        if self.foil_layer not in ('F.Cu','In1.Cu','In2.Cu','B.Cu') or type(self.flow_axis) is not int or self.flow_axis not in (0,1):
            raise ValueError('physical foil and planar flow axis required')
        for name in ('x_mm','y_mm','depth_mm'):
            interval=pair(getattr(self,name))
            if interval[0]>=interval[1]:raise ValueError('positive rectangular foil extent required')
            object.__setattr__(self,name,interval)
        object.__setattr__(self,'rho_ohm_mm',exact(self.rho_ohm_mm));object.__setattr__(self,'current_A',exact(self.current_A))
        if self.rho_ohm_mm<=0:raise ValueError('positive homogeneous reference resistivity required')

    @property
    def planar(self):return self.x_mm,self.y_mm
    @property
    def length_mm(self):p=self.planar[self.flow_axis];return p[1]-p[0]
    @property
    def cross_area_mm2(self):p=self.planar[1-self.flow_axis];return (p[1]-p[0])*(self.depth_mm[1]-self.depth_mm[0])
    @property
    def resistance_ohm(self):return self.rho_ohm_mm*self.length_mm/self.cross_area_mm2
    @property
    def energy_W(self):return self.resistance_ohm*self.current_A**2

    def voltage(self,xy,entrance_voltage=0):
        xy=pair(xy)
        if any(not interval[0]<=x<=interval[1] for x,interval in zip(xy,self.planar)):
            raise ValueError('potential requested outside reference foil')
        return exact(entrance_voltage)-self.rho_ohm_mm*self.current_A*(xy[self.flow_axis]-self.planar[self.flow_axis][0])/self.cross_area_mm2

    def cut(self,side):
        if type(side) is not int or side not in (0,1):raise ValueError('entrance0 or exit1 required')
        ends=[]
        for transverse in self.planar[1-self.flow_axis]:
            point=[F(),F()];point[self.flow_axis]=self.planar[self.flow_axis][side];point[1-self.flow_axis]=transverse;ends.append(tuple(point))
        normal=[0,0];normal[self.flow_axis]=2*side-1
        return FoilCut(self.region_id,self.region_id+(':entrance' if side==0 else ':exit'),self.foil_layer,
                       tuple(ends),self.depth_mm,tuple(normal),self.current_A*(1-2*side))


def disjoint_energy(regions):
    """Add only explicitly disjoint complete analytic volumes, each once."""
    if not regions or len({r.region_id for r in regions})!=len(regions):raise ValueError('nonempty unique energy regions required')
    for i,a in enumerate(regions):
        for b in regions[i+1:]:
            intersection=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip((a.x_mm,a.y_mm,a.depth_mm),(b.x_mm,b.y_mm,b.depth_mm))]
            if all(length>0 for length in intersection):raise ValueError('positive-volume energy overlap')
    return sum((r.energy_W for r in regions),F())
