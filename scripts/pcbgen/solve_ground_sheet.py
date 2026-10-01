"""Finite native ground-sheet screen with disjoint GH access and shared barrels.

Whole-board runs require heavy-guard.sh. Results are conditional numerical
screens until fixed-geometry convergence, positive budget and native coverage
gates have been reviewed. This program never changes a PCB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, box
from scipy.sparse import block_diag, coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.solve_ground_interfaces import area_geometry
from scripts.pcbgen.ground_access import strip
from scripts.pcbgen.ground_private import alternative_conductance
from scripts.pcbgen.sheet_mesh import Sheet, make_cells, barrel_edges

LAYERS = ('F.Cu', 'In1.Cu', 'B.Cu')


def solve(source, output, coarse, fine, origin):
    started = time.monotonic()
    data = json.loads(source.read_text())
    partition_source = ROOT/'design/partition/partition-input.json'
    requirement = json.loads(partition_source.read_text())['load_distribution']['jack_terminal_transfer']
    material_path = partition_source.with_name('ground-material-evidence.json')
    material = json.loads(material_path.read_text())['retained_reference_values']
    rho = material['annealed_copper_volume_resistivity_20C_ohm_mm']*(1+material['volume_temperature_coefficient_per_C']*(requirement['calculation_temperature_C']-20))
    sheet_ohm = rho/requirement['plane_copper_thickness_mm']
    holes = []
    for hole in data['drilled_holes']:
        x, y = hole['x_mm'], hole['y_mm']; sx, sy = hole['size_mm']
        d, length = min(sx, sy), abs(sx-sy)
        angle = math.radians(hole['angle_deg']+(90 if sy > sx else 0))
        dx, dy = math.cos(angle)*length/2, math.sin(angle)*length/2
        centre = LineString([(x-dx, y-dy), (x+dx, y+dy)]) if length else Point(x, y)
        holes.append(centre.buffer(d/2/math.cos(math.pi/128), quad_segs=32))
    drilled = shapely.union_all(holes)
    copper = []; audits = []
    for layer in LAYERS:
        native, _ = area_geometry(data['filled_contours'][layer])
        original, normalization = area_geometry(data['fractured_contours'][layer])
        envelope = original.boundary.length*2e-6+1e-6
        delta = native.symmetric_difference(original).area
        if delta > envelope:
            raise ValueError('native contour normalization changed physical copper')
        actual, _ = area_geometry(data['actual_AGND_pad_track_polygons'][layer])
        metal = shapely.union_all([native.intersection(original), actual]).difference(drilled).buffer(-2e-6)
        copper.append(metal)
        audits.append({'layer': layer, 'normalization': normalization,
                       'symmetric_difference_mm2': delta, 'allowed_boundary_envelope_mm2': envelope})
    owned = []; ports = []
    for port in data['ports']:
        pad, _ = area_geometry(port['native_B_pad_polygons'])
        x, y = port['x_mm'], port['y_mm']
        x0, y0, x1, y1 = data['GH_private_courtyards'][port['ref']]
        choices = []
        for cut in ((x, y0), (x, y1), (x0, y), (x1, y)):
            proof = strip(copper[2], (x, y), cut, sheet_ohm, max_width=.25, flat=True)
            if not proof or proof['width_mm'] != .25 or len(proof['points']) != 2:
                continue
            domain = pad.buffer(.001).union(LineString(proof['points']).buffer(.125, cap_style='flat'))
            if any(domain.intersection(other).area > 1e-8 for other in owned):
                continue
            face = LineString([(cut[0]-.125, cut[1]), (cut[0]+.125, cut[1])]) if cut[0] == x else \
                   LineString([(cut[0], cut[1]-.125), (cut[0], cut[1]+.125)])
            choices.append((proof['ohm'], cut, proof, domain, face))
        if not choices:
            raise ValueError('no exclusive finite GH access '+port['ref']+':'+port['pad'])
        resistance, cut, proof, domain, face = min(choices, key=lambda r: r[0])
        owned.append(domain)
        ports.append({'ref': port['ref'], 'pad': port['pad'], 'cut_mm': cut,
                      'private_ohm': resistance, 'private_path': proof, 'face': face})
    copper[2] = copper[2].difference(shapely.union_all(owned))
    patches = [box(land['x_mm']+.225, land['y_mm']+.225, land['x_mm']+.475, land['y_mm']+.475)
               for land in data['lands']]
    features = shapely.union_all([Point(b['x_mm'], b['y_mm']).buffer(.65) for b in data['plated_bridges']] +
        [p['face'].buffer(.5) for p in ports]+[p.buffer(2.5) for p in patches])
    bounds = (data['x0_mm'], data['y0_mm'], data['x0_mm']+data['nx']*data['pitch_mm'],
              data['y0_mm']+data['ny']*data['pitch_mm'])
    cells = make_cells(bounds, coarse, fine, features, origin)
    sheets = []
    for layer, metal in zip(LAYERS, copper):
        print('Meshing', layer, 'cells', len(cells), flush=True)
        sheets.append(Sheet(metal, cells, sheet_ohm))
        print(layer, 'nodes', len(sheets[-1].xy), 'triangles', len(sheets[-1].triangles), flush=True)
    offsets = np.cumsum([0]+[len(s.xy) for s in sheets])[:-1]
    matrix = block_diag([s.matrix for s in sheets], format='csc')
    rows, cols, values, barrels = barrel_edges(sheets, offsets, data['plated_bridges'], rho,
        data['board_thickness_mm'], requirement['minimum_finished_via_barrel_copper_mm'], sheet_ohm)
    matrix += coo_matrix((values, (rows, cols)), shape=matrix.shape).tocsc()
    count, labels = connected_components(matrix, directed=False)
    n = matrix.shape[0]
    def global_load(local):
        result = np.zeros(n); result[offsets[2]:] = local; return result
    sinks = [global_load(sheets[2].area_load(patch)) for patch in patches]
    sources = [global_load(sheets[2].line_load(p['face'])) for p in ports]
    selected_labels = {int(labels[i]) for rhs in [*sinks, *sources] for i in np.flatnonzero(abs(rhs)>1e-12)}
    if len(selected_labels) != 1:
        raise ValueError('physical GH/main electrodes are disconnected in finite sheet model')
    main_label = selected_labels.pop(); keep = labels == main_label
    # The connected component is retained explicitly. Mapping every actual
    # native load pad into it is a required additional whole-board gate.
    indices = np.flatnonzero(keep); reference = indices[0]; active = indices[1:]
    reduced = matrix[active][:, active].tocsc()
    print('Factoring connected common sheet nodes', len(indices), 'other components', count-1, flush=True)
    factor = splu(reduced)
    cases = []
    for land, sink in zip(data['lands'], sinks):
        results = []
        for port, source_load in zip(ports, sources):
            rhs = source_load-sink
            voltage = np.zeros(n); voltage[active] = factor.solve(rhs[active])
            residual = float(np.max(np.abs(matrix@voltage-rhs)))
            if residual > 1e-6:
                raise ValueError('finite sheet current residual exceeds gate')
            span = float(np.max(voltage[keep])-np.min(voltage[keep]))
            results.append({'ref': port['ref'], 'pad': port['pad'], 'private_ohm': port['private_ohm'],
                'reciprocal_voltage_span_ohm': span, 'electrode_effective_ohm': float(rhs@voltage),
                'residual_A': residual})
        cases.append({'single_main_land': land['ref'], 'ports': results,
                      'maximum_reciprocal_voltage_span_ohm': max(p['reciprocal_voltage_span_ohm'] for p in results)})
        print('Single land', land['ref'], 'max span mOhm', cases[-1]['maximum_reciprocal_voltage_span_ohm']*1000, flush=True)
    worst = max(c['maximum_reciprocal_voltage_span_ohm'] for c in cases)
    serial_ports = [{k: v for k, v in p.items() if k != 'face'} for p in ports]
    report = {'status': 'NUMERICAL SCREEN ONLY - convergence, all-load coverage and allocation not yet accepted',
        'board_sha256': data['board_sha256'], 'native_export_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'partition_source_sha256': hashlib.sha256(partition_source.read_bytes()).hexdigest(),
        'material_evidence_sha256': hashlib.sha256(material_path.read_bytes()).hexdigest(),
        'coarse_pitch_mm': coarse, 'fine_pitch_mm': fine, 'grid_origin_mm': origin,
        'temperature_C': requirement['calculation_temperature_C'], 'resistivity_ohm_mm': rho,
        'sheet_ohm': sheet_ohm, 'copper_geometry_audits': audits, 'nodes_by_layer': [len(s.xy) for s in sheets],
        'triangles_by_layer': [len(s.triangles) for s in sheets], 'shared_barrels': barrels,
        'GH_private_ports': serial_ports, 'cases': cases, 'worst_common_span_ohm': worst,
        'raw_remaining_K_common_ohm': .0005-worst,
        'reciprocity_bound': '|b^T K^-1 f| = |v^T f| <= I_total*(max(v)-min(v)) for sum(f)=0 and sum(positive f)<=I_total. Unit reciprocal field b uses fixed finite GH/main electrodes. All actual load copper must map into the retained common component. No uniform load distribution or equal main-wire sharing is assumed.',
        'all_native_load_pad_component_mapping': 'NOT RUN - required before acceptance',
        'finite_electrodes': 'Uniform trial current on the fixed 0.25mm GH boundary face and fixed 0.25x0.25mm main contact patch; all finite sheet/annular/axial transfers retained. No equipotential pad or ring.',
        'model_source_sha256': {name: hashlib.sha256((ROOT/'scripts/pcbgen'/name).read_bytes()).hexdigest()
                                for name in ('solve_ground_sheet.py', 'sheet_mesh.py')},
        'physical_material_process_hot_qualification': 'NOT RUN #65', 'runtime_sec': time.monotonic()-started}
    output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path); parser.add_argument('output', type=Path)
    parser.add_argument('--coarse-mm', type=float, default=2.)
    parser.add_argument('--fine-mm', type=float, default=.25)
    parser.add_argument('--origin-mm', type=float, nargs=2, default=[0., 0.])
    args = parser.parse_args()
    solve(args.source, args.output, args.coarse_mm, args.fine_mm, tuple(args.origin_mm))
