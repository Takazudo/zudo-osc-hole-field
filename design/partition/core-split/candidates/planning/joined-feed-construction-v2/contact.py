"""Deterministic finite angled terminal proposal; generates primitives, never CAD/native.
Coordinates: local foil z=0, z outward into gap. Pass actual outgoing unit axis.
Factory-capped via-in-pad required under any source patch crossing a drill.
"""
import math

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def add(a,b): return [x+y for x,y in zip(a,b)]
def scale(a,s): return [x*s for x in a]

def endpoint_primitives(axis, *, copper_axis_end_station_mm, current_A=1.0,
                        solder_height_mm=.05, core_radius_mm=.175,
                        hex_pitch_mm=.37, polygon_sides=64):
    v=list(map(float,axis));c=v[2];s=math.hypot(v[0],v[1])
    if not all(math.isfinite(x) for x in v+[copper_axis_end_station_mm,current_A,solder_height_mm]):raise ValueError('nonfinite')
    if abs(dot(v,v)-1)>1e-9 or not 0<c<1 or not s>0:raise ValueError('outgoing unit inclined axis required')
    if not(0<solder_height_mm<=.05 and core_radius_mm==.175 and hex_pitch_mm==.37 and polygon_sides==64):raise ValueError('unreviewed source class')
    e1=[-v[1]/s,v[0]/s,0.0];e2=[-c*v[0]/s,-c*v[1]/s,s]
    A=polygon_sides*core_radius_mm**2*math.sin(2*math.pi/polygon_sides)/2
    centres=[(hex_pitch_mm*(q+r/2),hex_pitch_mm*math.sqrt(3)*r/2) for q in range(-2,3) for r in range(-2,3) if max(abs(q),abs(r),abs(q+r))<=2]
    patches=[]
    for i,(u,w) in enumerate(centres):
        normal=[];foil=[];tip=[];upper=[]
        for k in range(polygon_sides):
            t=2*math.pi*k/polygon_sides
            q=add(scale(e1,u+core_radius_mm*math.cos(t)),scale(e2,w+core_radius_mm*math.sin(t)))
            f=add(q,scale(v,-q[2]/c));f[2]=0.0
            cut=add(f,scale(v,solder_height_mm/c));cut[2]=solder_height_mm
            end=add(q,scale(v,copper_axis_end_station_mm))
            if end[2]<=solder_height_mm:raise ValueError('normal end plane does not contain full tip cut')
            normal.append(q);foil.append(f);tip.append(cut);upper.append(end)
        patches.append({'id':f'core-{i+1:02d}','normal_centre_uv_mm':[u,w],
          'normal_section_vertices_mm':normal,'foil_vertices_mm':foil,
          'tip_vertices_mm':tip,'copper_end_vertices_mm':upper,
          'solder_solid':'convex hull of foil_vertices + tip_vertices; corresponding side edges parallel to axis',
          'copper_solid':'convex hull of tip_vertices + copper_end_vertices; normal core clipped by the foil-parallel tip plane',
          'normal_core_area_mm2':A,'foil_area_mm2':A/c,
          'current_A':current_A/19,'foil_normal_current_density_A_per_mm2':current_A*c/(19*A),
          'solder_current_density_vector_A_per_mm2':scale(v,current_A/(19*A))})
    return {'status':'PROPOSED FINITE CONTACT PRIMITIVES; no collision/process/native claim',
      'axis':v,'normal_basis':[e1,e2],'solder_height_mm':solder_height_mm,
      'copper_axis_end_station_mm':copper_axis_end_station_mm,'patches':patches,
      'full_wetted_land_xy_mm':[-2,-2,2,2],
      'port_sum_current_A':current_A,'port_sign':'Outgoing unit flux; negate all vectors/densities for incoming flux.',
      'interface_upper_ohm_per_end':2*4.5e-5*c/(19*A),
      'solder_upper_ohm_per_end':.0002*solder_height_mm/(19*A*c),
      'contact_pairing':'Join exactly these finite foil traces to a PCB operator. Include caps, real via/foil/spreading and full-wetted-support potential constraints there; no equipotential physical cut or empty-drill injection.'}

if __name__=='__main__':
    # Formula/primitive consistency checks only; no source-obstacle/candidate evaluation.
    c=.5445913286478836;a=.5933040689317951;b=.5927989259019525
    for ax in ([a,b,c],[a,-b,c],[-a,b,c],[-a,-b,c]):
        d=endpoint_primitives(ax,copper_axis_end_station_mm=2/c+2.5)
        assert len(d['patches'])==19
        assert abs(sum(p['foil_area_mm2']*p['foil_normal_current_density_A_per_mm2'] for p in d['patches'])-1)<1e-12
        for p in d['patches']:
            for f,t,q in zip(p['foil_vertices_mm'],p['tip_vertices_mm'],p['copper_end_vertices_mm']):
                assert f[2]==0 and t[2]==.05 and q[2]>.05
                assert max(abs(f[j]) for j in (0,1))<2
                assert abs(dot(q,ax)-(2/c+2.5))<1e-12
    print('PASS: four handednesses; nineteen finite supports; flux conservation; planar cuts and matched normal-plane ends. No geometry screen.')
