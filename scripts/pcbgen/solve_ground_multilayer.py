"""Whole-cell native-copper multilayer AGND resistance extraction.

Task-local dependencies: NumPy, SciPy, Shapely. No board files are modified.
Native topology and physical plating/process qualifications remain separate.
"""
from __future__ import annotations
import argparse,json,math,time
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon,Point,LineString
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu

def solve(mesh,output,pitch,source):
    started=time.monotonic();data=json.loads(mesh.read_text());req=json.loads(source.read_text())['load_distribution']['jack_terminal_transfer'];layers=['F.Cu','In1.Cu','B.Cu'];nx=math.floor(data['nx']*data['pitch_mm']/pitch);ny=math.floor(data['ny']*data['pitch_mm']/pitch);xx,yy=np.meshgrid(data['x0_mm']+np.arange(nx)*pitch,data['y0_mm']+np.arange(ny)*pitch);boxes=shapely.box(xx,yy,xx+pitch,yy+pitch)
    holes=[]
    for hole in data.get('drilled_holes',[]):
        x,y=hole['x_mm'],hole['y_mm'];sx,sy=hole['size_mm'];diameter=min(sx,sy);length=abs(sx-sy);angle=math.radians(hole['angle_deg']+(90 if sy>sx else 0));ux,uy=math.cos(angle),math.sin(angle)
        shape=LineString([(x-ux*length/2,y-uy*length/2),(x+ux*length/2,y+uy*length/2)]) if length else Point(x,y)
        # Circumscribed 128-sided holes remove at least the actual circular
        # drill, rather than treating an inscribed polygon corner as copper.
        holes.append(shape.buffer(diameter/2/math.cos(math.pi/128),quad_segs=32))
    drilled=shapely.union_all(holes)
    masks=[];normalizations=[];membership_audits=[];boundary_epsilon=2e-6 # 2 nm: twice KiCad IU resolution
    for layer in layers:
        polys=[Polygon(p['shell'],p['holes']) for p in data['filled_contours'][layer]]
        if not polys:raise ValueError('missing native filled AGND layer '+layer)
        normalized=[];slits=[]
        for poly in polys:
            if poly.is_valid:normalized.append(poly);continue
            converted=shapely.make_valid(poly,method='linework');parts=list(shapely.get_parts(converted));areas=[p for p in parts if p.geom_type in ('Polygon','MultiPolygon')];lines=[p for p in parts if p.geom_type in ('LineString','MultiLineString')];area=shapely.union_all(areas)
            original_edges=shapely.union_all([LineString(poly.exterior.coords)]+[LineString(r.coords) for r in poly.interiors]);normalized_edges=shapely.union_all([area.boundary]+lines)
            missing=float(shapely.difference(original_edges,normalized_edges).length);added=float(shapely.difference(normalized_edges,original_edges).length)
            if abs(poly.area-area.area)>1e-6 or poly.bounds!=area.bounds or missing>1e-6 or added>1e-6:raise ValueError('native slit normalization changed area/bounds/segments')
            old_points={tuple(p) for p in shapely.get_coordinates(poly)};new_points={tuple(p) for p in shapely.get_coordinates(converted)}
            if not new_points<=old_points:raise ValueError('native slit normalization introduced a new boundary point')
            normalized.append(area);slits.extend(lines);normalizations.append({'layer':layer,'reason':shapely.is_valid_reason(poly),'area_delta_mm2':area.area-poly.area,'missing_boundary_length_mm':missing,'new_boundary_length_mm':added,'zero_area_linework_mm':sum(l.length for l in lines),'all_normalized_vertices_from_native_source':True})
        painted=shapely.union_all(normalized)
        samples=data.get('native_membership_samples',{}).get(layer,[])
        if not samples:raise ValueError('native point-membership evidence missing')
        points=shapely.points([[s['x_mm'],s['y_mm']] for s in samples]);shapely.prepare(painted);observed=np.asarray(shapely.covers(painted,points));expected=np.array([s['inside'] for s in samples]);mismatch=observed!=expected
        edges=shapely.union_all([painted.boundary]+slits);distances=np.asarray(shapely.distance(edges,points[mismatch]));maximum=float(distances.max()) if len(distances) else 0.
        if maximum>boundary_epsilon:raise ValueError('interior membership mismatch after native slit normalization; maximum boundary distance '+str(maximum))
        failures=[{**samples[i],'normalized_inside':bool(observed[i]),'distance_to_boundary_or_slit_mm':float(distance)} for i,distance in zip(np.flatnonzero(mismatch),distances)]
        membership_audits.append({'layer':layer,'native_sample_count':len(samples),'boundary_convention_mismatches':int(mismatch.sum()),'maximum_mismatch_boundary_distance_mm':maximum,'sample_failing_points':failures[:8],'all_interior_samples_agree':True,'boundary_epsilon_mm':boundary_epsilon})
        # This negative inclusion tolerance is solely a conservative mesh
        # filter. It moves no KiCad geometry and cannot widen a slit.
        actual=[Polygon(p['shell'],p['holes']) for p in data.get('actual_AGND_pad_track_polygons',{}).get(layer,[])]
        if not actual or not all(p.is_valid for p in actual):raise ValueError('actual native AGND pad/track copper missing or invalid')
        painted=shapely.union_all([painted,*actual])
        copper=shapely.buffer(shapely.difference(painted,drilled),-boundary_epsilon);shapely.prepare(copper);cells=np.asarray(shapely.covers(copper,boxes))
        if slits:cells &= ~np.asarray(shapely.intersects(shapely.union_all(slits),boxes))
        masks.append(cells)
    mask=np.stack(masks);index=np.full(mask.shape,-1,dtype=np.int64);index[mask]=np.arange(mask.sum());n=int(mask.sum());rho=1.7241e-5*(1+.003947*(req['calculation_temperature_C']-20));sheet=rho/req['plane_copper_thickness_mm'];diag=np.zeros(n);ra=[];ca=[];va=[]
    def links(a,b,g):
        a=np.asarray(a,dtype=np.int64);b=np.asarray(b,dtype=np.int64);g=np.broadcast_to(g,a.shape);ra.extend((a,b));ca.extend((b,a));va.extend((-g,-g));np.add.at(diag,a,g);np.add.at(diag,b,g)
    for k in range(3):
        for dy,dx in ((0,1),(1,0)):
            a=index[k,:ny-dy,:nx-dx];b=index[k,dy:,dx:];ok=(a>=0)&(b>=0);links(a[ok],b[ok],1/sheet)
    def nearest(layer,x,y,radius=2.):
        fx=(x-data['x0_mm'])/pitch-.5;fy=(y-data['y0_mm'])/pitch-.5;ix,iy=round(fx),round(fy);reach=math.ceil(radius/pitch);choices=[]
        for cy in range(max(0,iy-reach),min(ny,iy+reach+1)):
            for cx in range(max(0,ix-reach),min(nx,ix+reach+1)):
                if index[layer,cy,cx]>=0:choices.append(((cx-fx)**2+(cy-fy)**2,int(index[layer,cy,cx])))
        if not choices:return None
        error,node=min(choices)
        return node,math.sqrt(error)*pitch
    bridges=0;missing_bridges=0
    for bridge in data['plated_bridges']:
        anchors=[nearest(k,bridge['x_mm'],bridge['y_mm'],max(2.,bridge['drill_mm']/2+2*pitch)) for k in range(3)]
        resistance=rho*1.6/(math.pi*bridge['drill_mm']*req['minimum_finished_via_barrel_copper_mm'])
        # Charge the full 1.6mm barrel for EACH adjacent layer link: a
        # conservative excess over actual layer-to-layer barrel lengths.
        for k in range(2):
            if anchors[k] and anchors[k+1]:links([anchors[k][0]],[anchors[k+1][0]],1/resistance);bridges+=1
            else:missing_bridges+=1
    sinks=[]
    for land in data['lands']:
        if not land['plane_connected']:raise ValueError('native main AGND terminal remains isolated')
        anchor=nearest(2,land['x_mm'],land['y_mm'])
        if not anchor or anchor[1]>2*pitch:raise ValueError('main land cannot be represented at this resolution')
        sinks.append(anchor[0]);diag[anchor[0]]+=1e12 # ideal AWG14 node at one copper cell, not whole land
    ra.append(np.arange(n));ca.append(np.arange(n));va.append(diag);matrix=coo_matrix((np.concatenate(va),(np.concatenate(ra),np.concatenate(ca))),shape=(n,n)).tocsc();_,labels=connected_components(matrix,directed=False);sink_labels={labels[s] for s in sinks};keep=np.isin(labels,list(sink_labels));mapping=np.full(n,-1,dtype=np.int64);mapping[keep]=np.arange(keep.sum());reduced=matrix[keep][:,keep];factor=splu(reduced);ports=[]
    for port in data['ports']:
        if not port['plane_connected']:raise ValueError('native GH AGND contact remains isolated '+port['ref']+':'+port['pad'])
        options=[nearest(layers.index(layer),port['x_mm'],port['y_mm']) for layer in port['pad_copper_layers'] if layer in layers];options=[a for a in options if a and a[1]<=2*pitch]
        if not options:raise ValueError('GH contact cannot be represented at this resolution')
        node,error=min(options,key=lambda a:a[1])
        if not keep[node]:raise ValueError('GH contact mesh does not reach main terminals: '+str({'ref':port['ref'],'pad':port['pad'],'anchor_snap_mm':error,'native_connected':port['plane_connected'],'raster_component':int(labels[node])}))
        rhs=np.zeros(keep.sum());rhs[mapping[node]]=1.;v=factor.solve(rhs);residual=float(np.max(np.abs(reduced@v-rhs)))
        if residual>1e-6:raise ValueError('multilayer solver residual exceeds gate')
        ports.append({'ref':port['ref'],'pad':port['pad'],'common_plane_ohm':float(v[mapping[node]]),'snap_error_mm':error,'residual_A':residual})
    worst=max(p['common_plane_ohm'] for p in ports);report={'status':'NUMERICAL EXTRACTION; mesh convergence and hot qualification required','board_sha256':data['board_sha256'],'mesh_pitch_mm':pitch,'whole_cells_in_native_copper_per_layer':dict(zip(layers,[int(m.sum()) for m in masks])),'raster_inclusion':'Exact Shapely covers for full square cells against native filled shells and holes; no partial cell is treated as copper. Source polygon segments are preserved by audited slit linework normalization. Whole-cell inclusion uses a conservative2nm erosion and circumscribed drilled-hole exclusion; endpoint snapping remains a numerical limit.','plated_layer_links':bridges,'unrepresented_layer_links':missing_bridges,'minimum_finished_barrel_copper_mm':req['minimum_finished_via_barrel_copper_mm'],'plane_copper_mm':req['plane_copper_thickness_mm'],'temperature_C':req['calculation_temperature_C'],'resistivity_ohm_mm':rho,'barrel_model':'Full1.6mm plated length charged for every adjacent layer link; actual native drill diameter, minimum25um wall. Native AGND THT pads and vias only.','worst_common_branch_plane_ohm':worst,'remaining_K_common_budget_ohm':.0005-worst,'passes_branch_alone_screen':worst<.0005,'ports':ports,'runtime_sec':round(time.monotonic()-started,3),'physical_hot_plating_wire_solder_qualification':'NOT RUN #65','K_actual_extraction':'NOT RUN #43; finite residual allocation must be checked there','GH_access_scope':'Individual access vias/traces are not omitted from current-sharing analysis; this common-plane model does not alone establish the GH contact bound.'};report['native_slit_normalization']=normalizations;report['native_point_membership']=membership_audits;report['conservative_boundary_inclusion_epsilon_mm']=boundary_epsilon;report['ambiguous_slit_cells_excluded']=True;output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(f'Multilayer{pitch}mm: {worst*1000:.6f}mOhm; K remaining{(.0005-worst)*1000:.6f}mOhm; cells{n}; runtime{report["runtime_sec"]}s')

def main():
    raise SystemExit("Historical unsupported ground screen: CLI retired; no acceptance proof. See ground-extraction-handoff.json and the unresolved issue #38 successor.")
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);p.add_argument('--pitch-mm',type=float,default=.5);p.add_argument('--source',type=Path,default=Path('design/partition/partition-input.json'));a=p.parse_args();solve(a.mesh,a.output,a.pitch_mm,a.source)
if __name__=='__main__':main()
