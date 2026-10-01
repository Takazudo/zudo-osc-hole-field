"""Complete source/native P ground inventory; every own-load return is real."""
from scripts.pcbgen.source_contact_inventory import expected_contacts, reconcile_native


def audit(native, manifest, partition, io, *, require_connected=True):
    if native['board_id'] != 'osc-control' or native['coordinate_frame']['source_to_native_translation_mm'] != [100, 50]:
        raise ValueError('Exact P native board/frame required')
    expected = expected_contacts('osc-control', partition, io, {'AGND'})
    fitted = {row['ref'] for row in io['physical_packages'] if not row['dnp']}
    own = reconcile_native(native, expected, fitted, {'AGND'})
    if len(own) != 214:
        raise ValueError('All 214 P own-load AGND contacts required')
    pads = [row for row in native['items'] if 'ref' in row]
    keys = [(row['ref'], row['pad']) for row in pads]
    if len(set(keys)) != len(keys) or len({row['uuid'] for row in pads}) != len(keys):
        raise ValueError('Duplicate P pad identity or UUID')
    by_key = dict(zip(keys, pads))
    direct = {(row['pcb_reference'], pad): row for row in partition['connectors'] if row['board'] == 'P'
              for pad, net in row['pin_map'].items() if net == 'AGND'}
    selected = manifest['selected_P_ground_ports']
    if len(selected) != 127 or len(direct) != 127 or {(row['ref'], row['pad']) for row in selected} != set(direct):
        raise ValueError('All 127 exact source P GH grounds required')
    lands = [row for row in manifest['all_P_main_lands'] if row['net'] == 'AGND']
    if len(lands) != 3 or lands != [row for row in partition['load_side_terminals'] if row['board'] == 'P' and row['net'] == 'AGND']:
        raise ValueError('All three exact source P main grounds required')
    connected = set(native['main_rail_members']['AGND'])
    rows = []
    for row in own.values():
        rows.append({'ref': row['ref'], 'pad': row['pad'], 'uuid': row['uuid'],
            'kind': 'own_load', 'native_layers': sorted(row['copper']),
            'main_connected': row['uuid'] in connected})
    for source in selected + [{'ref': row['reference'], 'pad': '1', 'side': row['side'], 'main_centre': row['center_mm']} for row in lands]:
        key = (source['ref'], source['pad'])
        if key not in by_key:
            raise ValueError('Missing P selected native contact: '+str(key))
        row = by_key[key]
        if row['net'] != 'AGND' or set(row['copper']) != {'B.Cu'} or source['side'] != 'B.Cu':
            raise ValueError('P selected ground net or physical face changed')
        if 'main_centre' in source and row['xy_mm'] != [a+b for a, b in zip(source['main_centre'], [100, 50])]:
            raise ValueError('P main native origin changed')
        rows.append({'ref': row['ref'], 'pad': row['pad'], 'uuid': row['uuid'],
            'kind': 'main' if 'main_centre' in source else 'GH', 'native_layers': ['B.Cu'],
            'main_connected': row['uuid'] in connected})
    if len(rows) != 344 or len({row['uuid'] for row in rows}) != 344:
        raise ValueError('P ground inventory is not a disjoint complete 344-contact set')
    missing = [row for row in rows if not row['main_connected']]
    if require_connected and missing:
        raise ValueError('P own-load/GH/main ground disconnected: '+str([(row['ref'], row['pad']) for row in missing]))
    return {'source_fitted_AGND_count': 214, 'GH_ground_count': 127, 'main_ground_count': 3,
        'complete_ground_contact_count': len(rows), 'connected_count': len(rows)-len(missing),
        'contacts': rows, 'disconnected': missing,
        'scope': 'Exact source/native identity and continuity only; no zero own-load current, physical source-density or electrical-budget acceptance.'}
