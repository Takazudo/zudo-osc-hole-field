"""Independent source/native identity and connectivity gates for the K trial."""
from scripts.pcbgen.source_contact_inventory import expected_contacts,reconcile_native


def audit(geometry,manifest,partition,io,*,require_connected=True):
    if geometry['board_id']!='osc-core':
        raise ValueError('K native board identity required')
    if geometry['coordinate_frame']['source_to_native_translation_mm']!=[100,50]:
        raise ValueError('K native/source frame changed')
    expected=expected_contacts('osc-core',partition,io,{'AGND'})
    fitted={p['ref'] for p in io['physical_packages'] if not p['dnp']}
    source_pads=reconcile_native(geometry,expected,fitted,{'AGND'})
    pads=[i for i in geometry['items'] if 'ref' in i]
    identities=[(i['ref'],i['pad']) for i in pads]
    if len(set(identities))!=len(pads) or len({i['uuid'] for i in pads})!=len(pads):
        raise ValueError('duplicate K native pad identity or UUID')
    by_identity=dict(zip(identities,pads));main=set(geometry['main_rail_members']['AGND'])
    selected=manifest['selected_K_ground_ports']
    lands=[r for r in manifest['all_K_main_lands'] if r['net']=='AGND']
    direct_headers=[c for c in partition['connectors'] if c['board']=='K' and c['id'].startswith(('JL-K-','JR-K-'))]
    direct_ports={(c['pcb_reference'],p):c for c in direct_headers for p,n in c['pin_map'].items() if n=='AGND'}
    if set(direct_ports)!={(r['ref'],r['pad']) for r in selected}:
        raise ValueError('K selected manifest differs from direct partition interfaces')
    direct_lands=[r for r in partition['load_side_terminals'] if r['board']=='K' and r['net']=='AGND']
    if lands!=direct_lands:
        raise ValueError('K main manifest differs from direct partition source')
    if len(selected)!=206 or len({(r['ref'],r['pad']) for r in selected})!=206 or len(lands)!=9:
        raise ValueError('K selected source inventory changed')
    rows=[]
    for expected_row in selected+[
        {'ref':r['reference'],'pad':'1','side':r['side'],'main_center_mm':r['center_mm']} for r in lands]:
        key=(expected_row['ref'],expected_row['pad'])
        if key not in by_identity:
            raise ValueError('K selected native contact absent: '+str(key))
        native=by_identity[key]
        if native['net']!='AGND' or set(native['copper'])!={'F.Cu'} or expected_row['side']!='F.Cu':
            raise ValueError('K selected contact net or physical face changed: '+str(key))
        if 'main_center_mm' in expected_row:
            xy=[a+b for a,b in zip(expected_row['main_center_mm'],[100,50])]
            if max(abs(a-b) for a,b in zip(xy,native['xy_mm']))>1.001e-6:
                raise ValueError('K main source/native origin changed: '+str(key))
        rows.append({'ref':key[0],'pad':key[1],'uuid':native['uuid'],
            'native_xy_mm':native['xy_mm'],'native_layer':'F.Cu',
            'main_connected':native['uuid'] in main,
            'kind':'main' if 'main_center_mm' in expected_row else 'GH'})
    missing=[r for r in rows if not r['main_connected']]
    if require_connected and missing:
        raise ValueError('K selected ground contacts disconnected: '+str([(r['ref'],r['pad']) for r in missing]))
    return {'source_fitted_AGND_count':len(source_pads),'source_fitted_AGND_connected_count':sum(r['uuid'] in main for r in source_pads.values()),
        'source_fitted_AGND_mapping':[{'ref':r['ref'],'pad':r['pad'],'uuid':r['uuid'],
            'main_connected':r['uuid'] in main} for r in source_pads.values()],
        'selected_contacts':rows,'selected_disconnected':missing,
        'scope':'Exact source/native inventory and physical F-side connectivity; no terminal-current density or electrical budget acceptance.'}
