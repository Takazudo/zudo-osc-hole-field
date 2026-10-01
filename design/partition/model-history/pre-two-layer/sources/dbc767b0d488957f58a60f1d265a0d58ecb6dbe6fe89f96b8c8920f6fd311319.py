"""Native four-layer ground conductor envelopes and disjoint barrel ownership.

Inside primitive polygons support conserved-current trials; outside polygons
support continuous-potential energy envelopes. Physical contact classes and
stack/material tolerances remain explicit source acceptance requirements.
"""
import hashlib
import json
import math
from pathlib import Path

import shapely
from shapely.geometry import Point,Polygon,box
from scripts.pcbgen.propose_rail_transfers import geometry,drill_geometry,LAYERS
from scripts.pcbgen.barrel_volume import BarrelVolume
from scripts.pcbgen.copper_envelope import primitive_envelopes,FLOAT_GUARD_MM
from scripts.pcbgen.solve_ground_interfaces import area_geometry
from scripts.pcbgen.terminal_face import external_smd_face,main_land_face


def axis_box(x0,y0,x1,y1):
    # Match the declared mesh coordinate representation exactly, including
    # shared faces. Binary additions such as 268.347502 + .05 otherwise create
    # a nonzero ghost overlap on a mathematically coincident profile boundary.
    return box(*(round(v,9) for v in (x0,y0,x1,y1)))


def computational_envelopes(inside,outside,tolerance=1e-5):
    """Explicit computational domains, with strict Boolean inclusion gates.

    Simplification alone has no direction. Retreat/expand its result and verify
    the actual sets; no native copper, contact or manufacturing rule is changed.
    Exact collar boundaries are subtracted only AFTER this operation.
    """
    current=inside.simplify(tolerance,preserve_topology=True).buffer(-2*tolerance,join_style='mitre')
    potential=outside.simplify(tolerance,preserve_topology=True).buffer(2*tolerance,join_style='mitre')
    if current.is_empty or not inside.covers(current):
        raise ValueError('computational current domain is not a strict native subset')
    if not potential.covers(outside):
        raise ValueError('computational potential domain is not a strict native superset')
    projection_guard=2e-9  # 2 pm, separate from the 2 nm native primitive guard.
    if not inside.covers(current.buffer(projection_guard)):
        raise ValueError('canonical mesh projection lacks a contained current guard')
    if not potential.buffer(-projection_guard).covers(outside):
        raise ValueError('canonical mesh projection lacks a containing potential guard')
    return current,potential,{'simplification_mm':tolerance,'directed_buffer_mm':2*tolerance,
        'verified_canonical_projection_guard_mm':projection_guard,
        'current_removed_area_mm2':inside.area-current.area,
        'potential_added_area_mm2':potential.area-outside.area,
        'strict_boolean_inclusion':True}


def fixed_load_patch(native_support):
    """A fixed finite numerical probe with exact axis-aligned boundaries.

    Curved native pad boundaries remain copper geometry, not a partly clipped
    RT source. Up to four separated squares cover distinct parts of a PTH rim.
    This does not assert that a real component injects a uniform current there.
    """
    x0,y0,x1,y1=native_support.bounds
    for side in (.1,.05,.025):
        candidates=[]
        step=side*1.25
        for ix in range(math.ceil((x1-x0)/step)):
            for iy in range(math.ceil((y1-y0)/step)):
                x=round(x0+(ix+.5)*step,6);y=round(y0+(iy+.5)*step,6)
                square=axis_box(x-side/2,y-side/2,x+side/2,y+side/2)
                if native_support.covers(square.buffer(.0001)):
                    candidates.append(square)
        if candidates:
            chosen=[candidates.pop(0)]
            while candidates and len(chosen)<4:
                index=max(range(len(candidates)),key=lambda i:min(candidates[i].centroid.distance(s.centroid) for s in chosen))
                chosen.append(candidates.pop(index))
            return shapely.union_all(chosen)
    raise ValueError('native load pad lacks a supported finite numerical profile')


def extract(source,rho,polygon_sides=16,refinement=1,include_loads=False,main_strands=False):
    data=json.loads(Path(source).read_text());main=set(data['main_rail_members']['AGND'])
    items=[i for i in data['items'] if i['net']=='AGND' and i['uuid'] in main]
    unused=[i['uuid'] for i in data['items'] if i['net']=='AGND' and i['uuid'] not in main]
    coppers=[r for r in data['stackup'] if r['layer'] in LAYERS]
    if [r['layer'] for r in coppers]!=list(LAYERS):raise ValueError('physical four-layer stack order is missing')
    thickness=[r['copper_thickness_mm'] for r in coppers]
    bands=[(r['nominal_midplane_depth_mm']-t/2,r['nominal_midplane_depth_mm']+t/2) for r,t in zip(coppers,thickness)]
    # Floating-point stack additions are normalized at their declared total.
    bands[0]=(0.,bands[0][1]);bands[-1]=(bands[-1][0],1.6)
    holes=[h for h in data['holes'] if h['net']=='AGND' and h['uuid'] in main]
    templates={};barrels=[];barrel_polygons=[];ownership=[]
    for h in holes:
        if not h['plated'] or h['size_mm'][0]!=h['size_mm'][1] or h['copper_layers']!=list(LAYERS):
            raise ValueError('actual AGND bridge is not a circular full-stack plated hole')
        diameter=h['size_mm'][0]
        if diameter not in templates:
            # The extra0.075mm foil flange stays strictly inside the minimum
            # hole-spacing envelope for actual0.3/1.22mm holes at16-sided collars.
            templates[diameter]=BarrelVolume(diameter/2,.025,diameter/2+.1,1.6,bands,rho,
                polygon_sides=polygon_sides,angular_subdivisions=refinement,
                radial_steps=refinement,band_steps=refinement,gap_steps=2*refinement)
        barrel=templates[diameter];polygon=Polygon(barrel.interface_polygon(h['xy_mm']))
        barrels.append((barrel,h['xy_mm']));barrel_polygons.append(polygon)
        ownership.append({'uuid':h['uuid'],'xy_mm':h['xy_mm'],'finished_drill_mm':diameter,
                          'flange_radius_mm':barrel.flange_radius})
    tree=shapely.STRtree(barrel_polygons)
    for index,polygon in enumerate(barrel_polygons):
        for other in tree.query(polygon,predicate='intersects'):
            if other>index and polygon.intersection(barrel_polygons[other]).area>1e-12:
                raise ValueError('two physical barrel/foil volumes overlap')
    owned=shapely.union_all(barrel_polygons)
    inner=[];outer=[];native_inner=[];native_outer=[];zone_audits=[];computational_audits=[]
    envelopes={i['uuid']:{l:primitive_envelopes(p) for l,p in i['analytic_primitives'].items()} for i in items}
    for layer in LAYERS:
        original_domains=[]
        for zone in data['zones']:
            if zone['keepout'] or zone['net']!='AGND' or zone['layer']!=layer:continue
            original,audits=area_geometry(zone['original_filled_contours'])
            original_domains.append(original)
            zone_audits.append({'uuid':zone['uuid'],'layer':layer,'normalization':audits,
                               'authority':'Original native filled domain; zero-area fracture seams retained as linework, not trenches',
                               'unfracture_area_comparison':zone['native_unfracture_audit']})
        zones=shapely.union_all(original_domains)
        inside=shapely.union_all([zones.buffer(-FLOAT_GUARD_MM)]+[envelopes[i['uuid']][layer][0] for i in items if layer in i['analytic_primitives']])
        outside=shapely.union_all([zones.buffer(FLOAT_GUARD_MM)]+[envelopes[i['uuid']][layer][1] for i in items if layer in i['analytic_primitives']])
        if not outside.covers(inside):raise ValueError('full native analytic conductor envelopes are not nested')
        # Every modeled full flange/collar must be supported by real native Cu.
        missing=owned.difference(inside).area
        if missing>1e-8:raise ValueError(f'{layer} lacks native Cu for finite flanges: {missing} mm2')
        # Foreign drills are already cleared in native filled Cu. Explicitly
        # remove inscribed/circumscribed drill envelopes for full pad primitives.
        inside_holes=[];outside_holes=[]
        for hole in data['holes']:
            nominal=drill_geometry(hole)
            outside_holes.append(nominal)
            outside_error=min(hole['size_mm'])/2*(1/math.cos(math.pi/128)-1)
            inside_holes.append(nominal.buffer(outside_error+2e-9))
        inside=inside.difference(shapely.union_all(inside_holes))
        outside=outside.difference(shapely.union_all(outside_holes))
        native_inner.append(inside);native_outer.append(outside)
        inside,outside,audit=computational_envelopes(inside,outside)
        audit['layer']=layer;computational_audits.append(audit)
        if not inside.covers(owned.boundary):
            raise ValueError('computational envelope removed finite barrel interface support')
        inner.append(inside.difference(owned));outer.append(outside.difference(owned))
    ports=[]
    packages=json.loads(Path('design/reports/io-partition.json').read_text())['physical_packages']
    fitted={p['ref']:p for p in packages if not p['dnp']}
    for item in items:
        if 'ref' not in item:continue
        shapes={l:p[0] for l,p in envelopes[item['uuid']].items()}
        land_layer=main_land_face(shapes)
        land=land_layer is not None
        gh=item['ref'].startswith('J900')
        if not (land or gh):
            if not include_loads or item['ref'] not in fitted:continue
            layer=3 if 'B.Cu' in shapes else 0
            if LAYERS[layer] not in shapes:raise ValueError('fitted load has no physical external foil pad')
            x,y=item['xy_mm'];patch=axis_box(x-.125,y-.125,x+.125,y+.125)
            if not inner[layer].covers(patch):
                # Fixed native profile, independent of computational refinement.
                patch=fixed_load_patch(shapes[LAYERS[layer]].intersection(native_inner[layer]).difference(owned))
            if patch.is_empty or patch.area<=1e-9:raise ValueError('load contact has no finite native foil support: '+item['ref'])
            if not inner[layer].covers(patch):raise ValueError('computational envelope removed fixed load contact: '+item['ref'])
            ports.append({'ref':item['ref'],'pad':item['pad'],'layer':layer,'patch':patch,'kind':'load',
                'source_instance':fitted[item['ref']]['instance'],'source_symbol':fitted[item['ref']]['symbol'],
                'physical_contact_class':'FIXED FINITE NUMERICAL PROFILE ONLY; actual terminal transfer not accepted'})
            continue
        layer=land_layer if land else external_smd_face(shapes,item['ref']+':'+item['pad'])
        x,y=item['xy_mm'];patch=axis_box(x+.225,y+.225,x+.475,y+.475) if land else axis_box(x-.125,y-.125,x+.125,y+.125)
        contact_fields={}
        if land and main_strands:
            from scripts.pcbgen.contact_transfer import main_contact_supports
            supports=main_contact_supports((x,y));patch=shapely.union_all(supports)
            wetting=axis_box(x-2,y-2,x+2,y+2)
            if patch.intersects(owned):
                raise ValueError('main strand support intersects an actual owned polygonal collar')
            contact_fields={'maximum_wetting':wetting,'strand_count':len(supports),
                'minimum_owned_collar_separation_mm':patch.distance(owned),
                'physical_contact_class':'UNSELECTED conditional nineteen-strand transfer; full maximum-wetting primal extension'}
        if not inner[layer].covers(patch):raise ValueError('fixed contact patch is outside contained native foil: '+item['ref'])
        ports.append({'ref':item['ref'],'pad':item['pad'],'layer':layer,'patch':patch,'kind':'main' if land else 'GH',
                      'physical_contact_class':'FIXED FINITE NUMERICAL PROFILE ONLY; transfer process not accepted',**contact_fields})
    fitted_ground=[{'ref':i['ref'],'pad':i['pad'],'uuid':i['uuid'],'layers':list(i['copper'])}
                   for i in items if 'ref' in i]
    return {'data':data,'inner':inner,'outer':outer,'barrels':barrels,'barrel_ownership':ownership,
            'thickness':thickness,'bands':bands,'ports':ports,'native_inner':native_inner,'native_outer':native_outer,
            'native_zone_authority_audits':zone_audits,
            'computational_envelope_audits':computational_audits,
            'unused_native_AGND_copper_uuids':unused,'all_native_ground_pad_component_mapping':fitted_ground,
            'geometry_export_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest()}
