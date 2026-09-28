"""Native courtyard interfaces and finite plated/foil access resistance.

This is a numerical draft extraction, conditional on the stated material and
solder-process requirements. It never edits a PCB or qualifies hardware.
"""
from __future__ import annotations
import argparse,json,math,time,sys,hashlib
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon,Point,LineString,box
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.ground_access import strip,annular_access,rim_access
from scripts.pcbgen.ground_private import alternative_conductance
from scripts.pcbgen.ground_annular import polar_network

LAYERS=('F.Cu','In1.Cu','B.Cu')
EPS=2e-6

def area_geometry(items):
    parts=[];audits=[]
    for item in items:
        poly=Polygon(item['shell'],item['holes'])
        if poly.is_valid:parts.append(poly);continue
        fixed=shapely.make_valid(poly,method='linework');areas=[p for p in shapely.get_parts(fixed) if p.geom_type in ('Polygon','MultiPolygon')];lines=[p for p in shapely.get_parts(fixed) if p.geom_type in ('LineString','MultiLineString')];area=shapely.union_all(areas)
        before=shapely.union_all([LineString(poly.exterior.coords),*[LineString(r.coords) for r in poly.interiors]]);after=shapely.union_all([area.boundary,*lines])
        if abs(poly.area-area.area)>1e-6 or poly.bounds!=area.bounds or shapely.difference(before,after).length>1e-6 or shapely.difference(after,before).length>1e-6:raise ValueError('original native ring normalization changed material boundary')
        if not {tuple(p) for p in shapely.get_coordinates(fixed)}<={tuple(p) for p in shapely.get_coordinates(poly)}:raise ValueError('ring normalization introduced boundary vertices')
        audits.append({'area_delta_mm2':area.area-poly.area,'serialized_seam_length_mm':sum(p.length for p in lines),'boundary_and_vertex_equivalence':True});parts.append(area)
    return shapely.union_all(parts),audits

def solve(mesh_path,output,pitch,source):
    started=time.monotonic();data=json.loads(mesh_path.read_text());req=json.loads(source.read_text())['load_distribution']['jack_terminal_transfer'];material_path=source.with_name('ground-material-evidence.json');material=json.loads(material_path.read_text())['retained_reference_values'];rho=material['annealed_copper_volume_resistivity_20C_ohm_mm']*(1+material['volume_temperature_coefficient_per_C']*(req['calculation_temperature_C']-20));sheet=rho/req['plane_copper_thickness_mm'];nx=math.floor(data['nx']*data['pitch_mm']/pitch);ny=math.floor(data['ny']*data['pitch_mm']/pitch);xx,yy=np.meshgrid(data['x0_mm']+np.arange(nx)*pitch,data['y0_mm']+np.arange(ny)*pitch);cells=shapely.box(xx,yy,xx+pitch,yy+pitch)
    holes=[];hole_by_location={}
    for h in data['drilled_holes']:
        x,y=h['x_mm'],h['y_mm'];sx,sy=h['size_mm'];d=min(sx,sy);length=abs(sx-sy);a=math.radians(h['angle_deg']+(90 if sy>sx else 0));ux,uy=math.cos(a),math.sin(a);shape=LineString([(x-ux*length/2,y-uy*length/2),(x+ux*length/2,y+uy*length/2)]) if length else Point(x,y);shape=shape.buffer(d/2/math.cos(math.pi/128),quad_segs=32);holes.append(shape);hole_by_location[(x,y)]=shape
    drilled=shapely.union_all(holes);courts={ref:box(*rect) for ref,rect in data['GH_private_courtyards'].items()};private=shapely.union_all(list(courts.values()));coppers=[];masks=[];geometry_audits=[]
    for layer in LAYERS:
        native,_=area_geometry(data['filled_contours'][layer]);original,normalization=area_geometry(data['fractured_contours'][layer]);delta=shapely.symmetric_difference(native,original).area;envelope=original.boundary.length*EPS+1e-6
        if delta>envelope:raise ValueError('Unfracture changed material outside2nm area envelope')
        painted=shapely.intersection(native,original);samples=data['native_membership_samples'][layer];points=shapely.points([[s['x_mm'],s['y_mm']] for s in samples]);shapely.prepare(painted);expected=np.array([s['inside'] for s in samples]);seen=np.asarray(shapely.covers(painted,points));bad=seen!=expected;distances=shapely.distance(painted.boundary,points[bad]);maximum=float(np.max(distances)) if len(distances) else 0.
        if maximum>EPS:raise ValueError('original/native material membership differs in interior')
        actual,_=area_geometry(data['actual_AGND_pad_track_polygons'][layer]);copper=shapely.buffer(shapely.difference(shapely.union_all([painted,actual]),drilled),-EPS);shapely.prepare(copper);coppers.append(copper);mask=np.asarray(shapely.covers(copper,cells))
        # The finite pad/strip ownership cut is applied after all native layers are built.
        masks.append(mask);geometry_audits.append({'layer':layer,'original_normalization':normalization,'native_symmetric_difference_mm2':delta,'area_envelope_mm2':envelope,'native_membership_samples':len(samples),'boundary_convention_mismatches':int(bad.sum()),'maximum_mismatch_boundary_distance_mm':maximum,'serialized_seams_are_not_material_voids':True})
    owned_paths=[];private_ports=[]
    for port in data['ports']:
        pad,_=area_geometry(port['native_B_pad_polygons']);pad=pad.buffer(.001);court=courts[port['ref']];x,y=port['x_mm'],port['y_mm'];x0,y0,x1,y1=court.bounds;choices=[]
        for cut in ((x,y0),(x,y1),(x0,y),(x1,y)):
            proof=strip(coppers[2],(x,y),cut,sheet,max_width=.25,flat=True)
            if not proof or proof['width_mm']!=.25:continue
            domain=shapely.union_all([pad,LineString(proof['points']).buffer(.125,cap_style='flat')])
            if any(shapely.intersection(domain,other).area>1e-8 for other in owned_paths):continue
            choices.append((proof['ohm'],cut,proof,domain))
        if not choices:raise ValueError('no exclusive contained pad-to-courtyard strip '+port['ref']+':'+port['pad'])
        resistance,cut,proof,domain=min(choices,key=lambda v:v[0]);owned_paths.append(domain);private_ports.append({'ref':port['ref'],'pad':port['pad'],'fixed_cut_mm':cut,'private_access_ohm':resistance,'private_path':proof,'native_pad_polygon_area_mm2':pad.area})
    private=shapely.union_all(owned_paths);common_coppers=[coppers[0],coppers[1],shapely.difference(coppers[2],private)]
    polar_disks={};polar_radius={}
    for bridge in data['plated_bridges']:
        drill=next(h for h in data['drilled_holes'] if h['x_mm']==bridge['x_mm'] and h['y_mm']==bridge['y_mm'])
        if abs(drill['size_mm'][0]-drill['size_mm'][1])>1e-9:raise ValueError('polar branch requires actual circular drilled hole '+bridge['uuid'])
        radius=bridge['drill_mm']/2+.07
        if .07>=bridge['annular_width_mm']-.004:raise ValueError('native annulus does not support fixed 70um polar radial domain')
        polar_radius[bridge['uuid']]=radius;polar_disks[bridge['uuid']]=Point(bridge['x_mm'],bridge['y_mm']).buffer(radius/math.cos(math.pi/128),quad_segs=32)
    all_disks=shapely.union_all(list(polar_disks.values()));retained_coppers=[shapely.difference(copper,all_disks) for copper in common_coppers];masks=[np.asarray(shapely.covers(copper,cells)) for copper in retained_coppers]
    mask=np.stack(masks);index=np.full(mask.shape,-1,dtype=np.int64);index[mask]=np.arange(mask.sum());n=int(mask.sum());diag=np.zeros(n);ra=[];ca=[];va=[]
    def links(a,b,g):
        a=np.asarray(a,dtype=np.int64);b=np.asarray(b,dtype=np.int64);g=np.broadcast_to(g,a.shape);ra.extend((a,b));ca.extend((b,a));va.extend((-g,-g));np.add.at(diag,a,g);np.add.at(diag,b,g)
    for layer in range(3):
        for dy,dx in ((0,1),(1,0)):
            a=index[layer,:ny-dy,:nx-dx];b=index[layer,dy:,dx:];ok=(a>=0)&(b>=0);links(a[ok],b[ok],1/sheet)
    def candidates(layer,x,y,radius=2.,limit=40):
        ix=round((x-data['x0_mm'])/pitch-.5);iy=round((y-data['y0_mm'])/pitch-.5);reach=math.ceil(radius/pitch);found=[]
        for row in range(max(0,iy-reach),min(ny,iy+reach+1)):
            for col in range(max(0,ix-reach),min(nx,ix+reach+1)):
                node=int(index[layer,row,col])
                if node<0:continue
                at=(data['x0_mm']+(col+.5)*pitch,data['y0_mm']+(row+.5)*pitch);found.append((math.dist((x,y),at),node,at,row,col))
        return sorted(found)[:limit]

    def touches_other_plane_cells(layer,geometry,row,col):
        if geometry.is_empty:return False
        lo_x,lo_y,hi_x,hi_y=geometry.bounds
        r0=max(0,math.floor((lo_y-data['y0_mm'])/pitch));r1=min(ny,math.ceil((hi_y-data['y0_mm'])/pitch)+1);c0=max(0,math.floor((lo_x-data['x0_mm'])/pitch));c1=min(nx,math.ceil((hi_x-data['x0_mm'])/pitch)+1)
        for rr in range(r0,r1):
            for cc in range(c0,c1):
                if (rr,cc)==(row,col) or index[layer,rr,cc]<0:continue
                if shapely.intersection(geometry,cells[rr,cc]).area>1e-8:return True
        return False
    def own_coupling(layer,proof,row,col):
        if proof['length_mm']==0:return shapely.GeometryCollection()
        tube=LineString(proof['points']).buffer(proof['width_mm']/2,cap_style='flat',join_style='round');owned=shapely.difference(tube,cells[row,col])
        if touches_other_plane_cells(layer,owned,row,col) or shapely.intersection(owned,occupied[layer]).area>1e-8:return None
        return owned
    bridge_audits=[];anchors={};link_count=0;occupied=[shapely.GeometryCollection() for _ in range(3)]
    for bridge in data['plated_bridges']:
        if bridge.get('full_through_span') is not True:raise ValueError('plated bridge full layer span unproved')
        radius=polar_radius[bridge['uuid']];disk=polar_disks[bridge['uuid']];hole=hole_by_location[(bridge['x_mm'],bridge['y_mm'])];entry=[]
        band=Point(bridge['x_mm'],bridge['y_mm']).buffer(radius+.002,quad_segs=128).difference(hole.buffer(.004,quad_segs=128))
        for layer in range(3):
            best=None
            if not shapely.covers(common_coppers[layer],band):entry.append(None);continue
            for distance,node,at,row,col in candidates(layer,bridge['x_mm'],bridge['y_mm'],max(2.,radius+2*pitch),100):
                proof=rim_access(common_coppers[layer],retained_coppers[layer],disk,(bridge['x_mm'],bridge['y_mm']),radius,at,sheet)
                if not proof:continue
                # Each outside conductor has one owner. The paid transfer
                # inside its existing target cell is represented once there.
                geometry=proof.pop('geometry');owned=shapely.difference(geometry,cells[row,col])
                if touches_other_plane_cells(layer,owned,row,col) or shapely.intersection(owned,occupied[layer]).area>1e-8:continue
                if best is None or proof['ohm']<best['access']['ohm']:best={'node':node,'at_mm':at,'distance_mm':distance,'access':proof,'owned_geometry':owned}
            if best:
                occupied[layer]=shapely.union_all([occupied[layer],best.pop('owned_geometry')])
            entry.append(best)
        active=[i for i,e in enumerate(entry) if e]
        reduction=None
        if len(active)>=2:
            ports=[(i,0.,entry[i]['access']['ohm'],entry[i]['access']['fixed_outer_rim_arc_width_rad']) for i in active]
            theta=[2*math.pi*i/16 for i in range(16)];admittance,reduction=polar_network(bridge['drill_mm']/2,radius,sheet,rho,req['minimum_finished_via_barrel_copper_mm'],data['board_thickness_mm'],theta,ports,4)
            for ia,a in enumerate(active):
                for ib,b in enumerate(active[ia+1:],ia+1):
                    g=-admittance[ia,ib]
                    if g< -1e-8:raise ValueError('polar reduction is not passive')
                    if g>1e-12:links([entry[a]['node']],[entry[b]['node']],g);link_count+=1
        anchors[bridge['uuid']]=entry;bridge_audits.append({'uuid':bridge['uuid'],'anchors':entry,'polar_shared_barrel':reduction,'full_through_span':True})
    # Fixed physical electrodes and cuts are independent of raster pitch.
    # Their finite geometry-contained coupling strips are charged, never snapped.
    sinks=[]
    for land in data['lands']:
        fixed=(land['x_mm']+.35,land['y_mm']+.35)
        patch=box(fixed[0]-.125,fixed[1]-.125,fixed[0]+.125,fixed[1]+.125)
        if not shapely.covers(retained_coppers[2],patch):raise ValueError('fixed solder contact patch intersects excluded polar/owned domain')
        choices=[]
        for distance,node,at,row,col in candidates(2,*fixed,3.,200):
            proof=strip(retained_coppers[2],fixed,at,sheet,max_width=.25,flat=True)
            if proof:
                owned=own_coupling(2,proof,row,col)
                if owned is not None:choices.append((proof['ohm'],node,at,proof,owned))
        if not choices:raise ValueError('no finite main-land patch-to-mesh path')
        resistance,node,at,proof,owned=min(choices,key=lambda v:v[0]);occupied[2]=shapely.union_all([occupied[2],owned]);sinks.append({'ref':land['ref'],'node':node,'physical_contact_patch_centre_mm':fixed,'physical_contact_patch_size_mm':.25,'mesh_coupling':proof,'mesh_coupling_ohm':resistance,'interface_basis':'Fixed native copper patch inside conditional full 4x4 solder coverage; finite pad spreading and transfer retained. Wire termination 0.2mOhm separate.'})
    interfaces=[];private_networks=[];by_ref={}
    for port in private_ports:
        cut=tuple(port['fixed_cut_mm']);choices=[];contained_candidates=0;ownership_rejected=0
        for distance,node,at,row,col in candidates(2,*cut,3.,200):
            proof=strip(retained_coppers[2],cut,at,sheet,max_width=.25,flat=True)
            if proof and proof['width_mm']==.25:
                contained_candidates+=1
                owned=own_coupling(2,proof,row,col)
                if owned is not None:choices.append((proof['ohm'],node,at,proof,owned))
                else:ownership_rejected+=1
        if not choices:raise ValueError(f'finite courtyard cut has no exclusive retained-cell access {port["ref"]}:{port["pad"]}; cut={cut}; native-contained candidates={contained_candidates}; plane/access-ownership rejected={ownership_rejected}')
        coupling,node,at,proof,owned=min(choices,key=lambda v:v[0]);occupied[2]=shapely.union_all([occupied[2],owned]);row={**port,'node':node,'fixed_interface_patch_size_mm':.25,'common_coupling_ohm':coupling,'common_coupling_path':proof,'interface_kind':'Actual native courtyard boundary; only owned full pad and disjoint paid strip removed from common B'};interfaces.append(row);by_ref.setdefault(port['ref'],[]).append(row)
    board_branch='JL' if 'left' in data['board'] else 'JR';connector_source=source.parents[1]/'reports/connectors.json';connector_data=json.loads(connector_source.read_text());main_refs={h['pcb_reference'] for h in connector_data['headers'] if h['id'].startswith(board_branch+'-K-')}
    for ref,ports in by_ref.items():
        if ref not in main_refs:continue
        private_networks.append({'ref':ref,'pads':[p['pad'] for p in ports],'impedance_matrix_ohm':np.diag([p['private_access_ohm'] for p in ports]).tolist(),'scope':'Disjoint owned pad/strip conductors; all physical shared barrels and remaining native sheet copper are in the one common graph.'})
    ra.append(np.arange(n));ca.append(np.arange(n));va.append(diag);base=coo_matrix((np.concatenate(va),(np.concatenate(ra),np.concatenate(ca))),shape=(n,n)).tocsc();_,labels=connected_components(base,directed=False);cases=[]
    for selected in [sinks,*[[s] for s in sinks]]:
        sink_labels={labels[s['node']] for s in selected};keep=np.isin(labels,list(sink_labels));mapping=np.full(n,-1,dtype=np.int64);mapping[keep]=np.arange(keep.sum());matrix=base[keep][:,keep].tocsc();extra=np.zeros(keep.sum())
        for sink in selected:extra[mapping[sink['node']]]+=1/max(sink['mesh_coupling_ohm'],1e-12)
        from scipy.sparse import diags
        matrix+=diags(extra);factor=splu(matrix);rows=[];memo={}
        for interface in interfaces:
            node=interface['node']
            if not keep[node]:
                failure={'status':'NOT SOLVED: conservative mesh disconnected; no resistance acceptance','board_sha256':data['board_sha256'],'mesh_pitch_mm':pitch,'failed_GH_ref':interface['ref'],'failed_GH_pad':interface['pad'],'fixed_interface_centre_mm':interface['fixed_cut_mm'],'selected_main_lands':[s['ref'] for s in selected],'GH_component_cells':int(np.count_nonzero(labels==labels[node])),'main_component_cells':[int(np.count_nonzero(labels==labels[s['node']])) for s in selected],'plated_layer_links':link_count,'bridge_anchor_counts_by_layer':[sum(b['anchors'][l] is not None for b in bridge_audits) for l in range(3)],'interfaces':interfaces,'bridges':bridge_audits,'geometry_audits':geometry_audits,'runtime_sec':round(time.monotonic()-started,3),'model_source_sha256':{name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('solve_ground_interfaces.py','ground_access.py','ground_private.py','ground_annular.py')}}
                output.write_text(json.dumps(failure,indent=2,sort_keys=True)+'\n')
                raise ValueError('conservative mesh disconnected at '+interface['ref']+':'+interface['pad']+' to '+','.join(s['ref'] for s in selected))
            if node not in memo:
                rhs=np.zeros(keep.sum());rhs[mapping[node]]=1.;v=factor.solve(rhs);residual=float(np.max(np.abs(matrix@v-rhs)))
                if residual>1e-6:raise ValueError('resistance solve residual exceeds gate')
                memo[node]=(float(v[mapping[node]]),residual)
            resistance,residual=memo[node];resistance+=interface['common_coupling_ohm'];rows.append({'ref':interface['ref'],'pad':interface['pad'],'common_plane_and_main_transfer_ohm':resistance,'common_interface_coupling_ohm':interface['common_coupling_ohm'],'mesh_plane_and_main_contact_coupling_ohm':resistance-interface['common_coupling_ohm'],'private_access_ohm':interface['private_access_ohm'],'full_path_screen_ohm':resistance+interface['private_access_ohm'],'residual_A':residual})
        cases.append({'main_lands':[s['ref'] for s in selected],'worst_common_ohm':max(r['common_plane_and_main_transfer_ohm'] for r in rows),'worst_full_path_screen_ohm':max(r['full_path_screen_ohm'] for r in rows),'ports':rows})
    partition=json.loads(source.with_name('partition.json').read_text());branch='JL' if 'left' in str(mesh_path) else 'JR';contract=partition['power']['GH_normal_return_bounds'][branch]
    count=sum(len(g['pads']) for g in private_networks)
    if count!=contract['return_contact_count']:raise ValueError('shared header count differs from exact source GH contract')
    def worst_current(K_access):
        candidates=[]
        for group_index,group in enumerate(private_networks):
            for omitted,pad in enumerate(group['pads']):
                conductance=contract['dedicated_ground_wire_count']/contract['dedicated_ground_wire_max_ohm']
                for i,other in enumerate(private_networks):conductance+=alternative_conductance(other['impedance_matrix_ohm'],contract['maximum_other_path_ohm']+K_access,omitted if i==group_index else None)
                alternative=1/conductance+contract['common_PCB_neck_max_ohm'];current=4.6*alternative/(contract['minimum_single_path_ohm']+alternative);candidates.append((current,group['ref'],pad))
        return max(candidates)
    zero_screen=worst_current(0.)
    if zero_screen[0]>=.5:K_access_max=0.;K_access_allocation=0.;current_result=zero_screen
    else:
        lo,hi=0.,1.
        for _ in range(50):
            mid=(lo+hi)/2
            if worst_current(mid)[0]<=.5:lo=mid
            else:hi=mid
        K_access_max=lo;K_access_allocation=min(.001,lo/2);current_result=worst_current(K_access_allocation)
    current_report={'worst_single_contact_A':current_result[0],'worst_ref':current_result[1],'worst_pad':current_result[2],'K_private_access_maximum_allowed_ohm':K_access_max,'K_private_access_allocated_maximum_ohm':K_access_allocation,'K_actual_access_extraction':'NOT RUN #43; finite allocated maximum must be verified, no zero-access acceptance','zero_K_access_feasibility_screen_A':zero_screen[0],'common_branch_plus_K_maximum_ohm':.0005,'status':'CONDITIONAL NUMERICAL SCREEN - finite K allocation required' if K_access_allocation>0 and current_result[0]<=.5 else 'NO FEASIBLE POSITIVE K ACCESS ALLOCATION IN THIS SCREEN','equation':'g_header=1^T (Z_shared_native_header + diag(R_GH_wire_max+R_K_access_max))^-1 1. Omit worst candidate from its matrix; add dedicated main-wire conductance. R_alternatives=1/sum(g)+0.5mOhm common upper allocation. I_candidate=4.6*R_alternatives/(R_candidate_wire_min+R_alternatives). Candidate PCB/contact access is zero; shared copper/barrel conductance is represented once.'}
    worst=max(c['worst_common_ohm'] for c in cases);report={'status':'CORRECTED NUMERICAL SCREEN; convergence/margin review required before allocation','board_sha256':data['board_sha256'],'model_source_sha256':{name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('solve_ground_interfaces.py','ground_access.py','ground_private.py','ground_annular.py')},'partition_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'mesh_pitch_mm':pitch,'temperature_C':req['calculation_temperature_C'],'plane_copper_mm':req['plane_copper_thickness_mm'],'minimum_finished_barrel_copper_mm':req['minimum_finished_via_barrel_copper_mm'],'resistivity_ohm_mm':rho,'material_evidence_sha256':hashlib.sha256(material_path.read_bytes()).hexdigest(),'minimum_native_annular_width_mm':min(b['annular_width_mm'] for b in data['plated_bridges']),'geometry_audits':geometry_audits,'native_unfracture_audit':data['native_unfracture_audit'],'common_graph_private_cut':'Native complete GH pad copper plus each disjoint contained 0.25mm strip to its actual courtyard boundary is omitted only from common B; remaining court copper stays shared. Every virtual input crosses its paid finite strip. Polar disks excluded from every plane cell; each native barrel is one shared sector network.','bridge_model':'One supported polar annulus per layer and one shared cylinder sector network per native bridge. Each adjacent axial link uses full board thickness; barrel angular conductance omitted. One fixed finite outer arc and exclusive wedge/strip per layer; plane cells intersecting the modeled disk excluded. No arbitrary nearest-island coupling.','plated_layer_links':link_count,'bridges':bridge_audits,'GH_interfaces':interfaces,'shared_private_header_networks':private_networks,'main_load_contact_patches':sinks,'cases':cases,'worst_common_all_and_single_land_ohm':worst,'prospective_remaining_K_common_budget_ohm':.0005-worst,'GH_current_bound':current_report,'private_access_maximum_ohm':max(i['private_access_ohm'] for i in interfaces),'runtime_sec':round(time.monotonic()-started,3),'numerical_limit':'Whole-cell geometry subset; square finite-volume discretization is numerical, not itself a proved continuum upper bound. Convergence and margin review required.','physical_hot_and_full_solder_coverage_qualification':'NOT RUN #65; minimum materials/process are draft acceptance conditions, not achieved evidence','K_actual_extraction':'NOT RUN #43; no native K PCB exists'};output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(f'Corrected{pitch}mm worst common{worst*1000:.6f}mOhm; private max{report["private_access_maximum_ohm"]*1000:.6f}mOhm; K residual{(.0005-worst)*1000:.6f}mOhm; runtime{report["runtime_sec"]}s')

def main():
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);p.add_argument('--pitch-mm',type=float,default=.5);p.add_argument('--source',type=Path,default=Path('design/partition/partition-input.json'));a=p.parse_args()
    try:solve(a.mesh,a.output,a.pitch_mm,a.source)
    except Exception as error:
        if not a.output.exists():a.output.write_text(json.dumps({'status':'NOT SOLVED - no resistance acceptance','error':str(error),'mesh_pitch_mm':a.pitch_mm,'board_sha256':json.loads(a.mesh.read_text())['board_sha256'],'model_source_sha256':{name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('solve_ground_interfaces.py','ground_access.py','ground_private.py','ground_annular.py')}},indent=2)+'\n')
        raise
if __name__=='__main__':main()
