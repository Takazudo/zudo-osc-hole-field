"""Sparse plane/land-array resistance estimate; run with task-local SciPy.

The native exporter and this numerical model are separate. Missing native
access/terminal connections fail the complete extraction gate, regardless of
a finite prospective plane estimate. The solver never modifies a board.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu

def solve(mesh_path,output,requirement):
    data=json.loads(mesh_path.read_text());spec=json.loads(requirement.read_text())['load_distribution']['jack_terminal_transfer']
    mask=np.array(data['mask'],dtype=bool).reshape(data['ny'],data['nx']);indices=np.full(mask.shape,-1,dtype=int);indices[mask]=np.arange(mask.sum());n=int(mask.sum());pitch=data['pitch_mm']
    # NBS Handbook100 printed pp3/35, physical indices8/40. Volume
    # resistivity coefficient includes the stated expansion correction.
    rho20=1.7241e-5;alpha=.003947;rho=rho20*(1+alpha*(spec['calculation_temperature_C']-20));sheet=rho/spec['plane_copper_thickness_mm']
    barrel=rho*1.6/(math.pi*spec['via_drill_mm']*spec['minimum_finished_via_barrel_copper_mm'])
    rows=[];cols=[];values=[];diagonal=np.zeros(n)
    for dy,dx in ((0,1),(1,0)):
        src=indices[:data['ny']-dy or None,:data['nx']-dx or None];dst=indices[dy:,dx:];valid=(src>=0)&(dst>=0);a=src[valid];b=dst[valid];g=1/sheet
        rows.extend(a);cols.extend(b);values.extend(np.full(len(a),-g));rows.extend(b);cols.extend(a);values.extend(np.full(len(a),-g));np.add.at(diagonal,a,g);np.add.at(diagonal,b,g)
    def nearest(x,y):
        fx=(x-data['x0_mm'])/pitch-.5;fy=(y-data['y0_mm'])/pitch-.5
        ix,iy=round(fx),round(fy);choices=[]
        for cy in range(max(0,iy-4),min(data['ny'],iy+5)):
            for cx in range(max(0,ix-4),min(data['nx'],ix+5)):
                if indices[cy,cx]>=0:choices.append(((cx-fx)**2+(cy-fy)**2,int(indices[cy,cx])))
        if not choices:raise ValueError('terminal/port has no nearby filled-plane mesh cell')
        error,node=min(choices)
        if math.sqrt(error)*pitch>2*pitch:raise ValueError('port snapping exceeds two mesh pitches')
        return node,math.sqrt(error)*pitch
    sink_points=[]
    for land in data['lands']:
        for ix in range(spec['array_columns']):
            for iy in range(spec['array_rows']):
                x=land['x_mm']+(ix-(spec['array_columns']-1)/2)*spec['array_pitch_mm'];y=land['y_mm']+(iy-(spec['array_rows']-1)/2)*spec['array_pitch_mm'];node,error=nearest(x,y);sink_points.append((node,land['ref'],error))
    for node,_,_ in sink_points:diagonal[node]+=1/barrel
    rows.extend(range(n));cols.extend(range(n));values.extend(diagonal)
    matrix=coo_matrix((values,(rows,cols)),shape=(n,n)).tocsc()
    # Remove orphan raster islands that have no terminal connection. They
    # otherwise make the Laplacian singular; ports on them must fail.
    from scipy.sparse.csgraph import connected_components
    count,labels=connected_components(matrix,directed=False);sink_labels={labels[node] for node,_,_ in sink_points};keep=np.array([label in sink_labels for label in labels]);mapping=np.full(n,-1);mapping[keep]=np.arange(keep.sum());factor=splu(matrix[keep][:,keep])
    results=[]
    for port in data['ports']:
        node,error=nearest(port['x_mm'],port['y_mm'])
        if not keep[node]:raise ValueError('GH contact raster component disconnected from all main return arrays')
        rhs=np.zeros(keep.sum());rhs[mapping[node]]=1.;voltage=factor.solve(rhs)
        residual=np.max(np.abs(matrix[keep][:,keep]@voltage-rhs))
        if residual>1e-7:raise ValueError('resistance solver residual exceeds gate')
        results.append({**port,'prospective_plane_and_main_array_ohm':float(voltage[mapping[node]]),'mesh_snap_mm':error,'solver_residual_A':float(residual)})
    worst=max(r['prospective_plane_and_main_array_ohm'] for r in results);open_ports=[r['ref']+':'+r['pad'] for r in results if not r['plane_connected']];open_lands=[r['ref'] for r in data['lands'] if not r['plane_connected']]
    report={'status':'FAIL - native return transfers open' if open_ports or open_lands else 'NUMERICAL EXTRACTION - mesh convergence and source resistance gates required','board_sha256':data['board_sha256'],'pitch_mm':pitch,'copper_resistivity_20C_ohm_mm':rho20,'volume_resistivity_temperature_coefficient_per_C':alpha,'temperature_C':spec['calculation_temperature_C'],'plane_thickness_mm':spec['plane_copper_thickness_mm'],'sheet_resistance_ohm_per_square':sheet,'single_via_barrel_ohm':barrel,'via_barrel_source_minimum_mm':spec['minimum_finished_via_barrel_copper_mm'],'array_vias_per_land':spec['array_rows']*spec['array_columns'],'prospective_worst_plane_and_main_transfer_ohm':worst,'prospective_remaining_K_common_allocation_ohm':.0005-worst,'open_contact_identities':open_ports,'open_terminal_identities':open_lands,'ports':results,'source':'NBS Handbook100 Copper Wire Tables,1966; physical PDF8/printed3 resistivity, physical40/printed35 volume temperature coefficient; https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf','scope':'Finite-volume mesh of native In1 plane with source25-via main transfer arrays. Arrays are prospective unless all native lands are connected. Individual GH access resistance and source-wire extrema must be added separately; no K PCB exists yet. This estimate is not a hot measurement or certified resistance bound.'}
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(f'Prospective plane/common main arrays: {worst*1000:.6f} mOhm; residual K budget {(0.0005-worst)*1000:.6f} mOhm; open contacts {len(open_ports)}, lands {len(open_lands)}')

def main():
    raise SystemExit("Historical unsupported ground screen: CLI retired; no acceptance proof. See ground-extraction-handoff.json and the unresolved issue #38 successor.")
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);p.add_argument('--requirement',type=Path,default=Path('design/partition/partition-input.json'));a=p.parse_args();solve(a.mesh,a.output,a.requirement)
if __name__=='__main__':main()
