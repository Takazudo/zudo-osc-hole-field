"""Remove only proven source-free, separate copper from zero-barrel models.

Physical foil identity survives active-sheet renumbering. A removed component
has zero current and one constant potential on its whole volume. Its energy
is zero. No interlayer connection or omitted terminal current is introduced.
Barrel assemblies keep the stricter full-domain connectivity check.
"""
import shapely


def active_domains(inner, outer, layers, supports, barrel_count):
    if not (len(inner)==len(outer)==len(layers)==len(supports)):
        raise ValueError('physical foil domain and support counts differ')
    audits=[]; kept_inner=[]; kept_outer=[]; indices=[]
    for index,(inside,outside,name,contact_supports) in enumerate(zip(inner,outer,layers,supports)):
        if outside.is_empty:
            if not inside.is_empty or contact_supports or barrel_count:
                raise ValueError('empty physical foil contains a declared source or barrel')
            audits.append({'layer':name,'omitted':'empty physical ground domain','area_mm2':0.})
            continue
        if barrel_count:
            selected=outside
        else:
            pieces=list(outside.geoms) if outside.geom_type=='MultiPolygon' else [outside]
            live=[p for p in pieces if any(p.intersects(s) for s in contact_supports)]
            if len(live)>1:
                raise ValueError('source-bearing physical ground components are disconnected')
            selected=shapely.union_all(live)
            for piece in pieces:
                if any(piece.equals(p) for p in live):continue
                if any(piece.intersects(s) for s in contact_supports):
                    raise ValueError('omitted component intersects a declared contact support')
                if not selected.is_empty and piece.distance(selected)<=0:
                    raise ValueError('omitted conductor lacks positive physical separation')
                audits.append({'layer':name,'omitted':'source-free separate conductor',
                    'area_mm2':piece.area,'domain_geojson':shapely.geometry.mapping(piece),
                    'extension':'zero current and constant potential on this complete separate component',
                    'all_declared_contact_supports_disjoint':True})
        if selected.is_empty:continue
        # Existing full-barrel four-foil geometry stays byte-for-byte in its
        # original polygon representation; do not reorder rings needlessly.
        current=inside if barrel_count else inside.intersection(selected)
        if current.is_empty:raise ValueError('source-bearing foil lacks a current domain')
        indices.append(index);kept_inner.append(current);kept_outer.append(selected)
    if not indices:raise ValueError('no physical ground conductor with declared contacts')
    if not barrel_count and len(indices)!=1:
        raise ValueError('source-bearing foils lack a physical interlayer connection')
    return {'inner':kept_inner,'outer':kept_outer,'physical_indices':indices,
        'layers':[layers[i] for i in indices], 'omission_audits':audits}
