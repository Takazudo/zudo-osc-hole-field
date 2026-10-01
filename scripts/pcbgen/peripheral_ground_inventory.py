"""Complete independent source/native ground reconciliation for O and EL."""
from scripts.pcbgen.generate_peripheral_ground import source_contacts


def audit(native,manifest,partition,io,require_connected=True):
    bid=manifest['board_id'];key=manifest['board_key']
    if native['board_id']!=bid or native['coordinate_frame']['source_to_native_translation_mm']!=[100,50]:
        raise ValueError('peripheral native board/frame differs')
    own,gh=source_contacts(bid,key,partition,io)
    expected=own|set(gh)
    if {(r['ref'],r['pad']) for r in manifest['own_ground_contacts']}!=own or {(r['ref'],r['pad']) for r in manifest['GH_ground_contacts']}!=set(gh):
        raise ValueError('peripheral manifest differs from independent source inventory')
    pads=[r for r in native['items'] if 'ref' in r]
    if len({(r['ref'],r['pad']) for r in pads})!=len(pads) or len({r['uuid'] for r in pads})!=len(pads):
        raise ValueError('duplicate native peripheral pad identity or UUID')
    grounds={(r['ref'],r['pad']):r for r in pads if r['net']=='AGND'}
    if set(grounds)!=expected:raise ValueError('peripheral native/source ground contact set differs')
    reference=native['ground_reference'];selected=manifest['source_reference']
    if not reference or any(reference[k]!=selected[k] for k in ('ref','pad','net')) or reference['layer']!=selected['side']:
        raise ValueError('peripheral named ground reference differs from source')
    ref=grounds[(selected['ref'],selected['pad'])]
    if ref['uuid']!=reference['uuid'] or ref['xy_mm']!=reference['xy_mm']:
        raise ValueError('peripheral reference UUID/position differs')
    connected=set(native['ground_reference_members']);rows=[]
    for identity,physical in sorted(grounds.items()):
        if identity in gh and set(physical['copper'])!={gh[identity]['side']}:
            raise ValueError('GH physical foil differs from source')
        if set(physical['copper'])-{'F.Cu','B.Cu'}:raise ValueError('inactive native copper foil')
        rows.append({'ref':identity[0],'pad':identity[1],'uuid':physical['uuid'],
            'kind':'GH' if identity in gh else 'own_load','native_layers':sorted(physical['copper']),
            'reference_connected':physical['uuid'] in connected})
    missing=[r for r in rows if not r['reference_connected']]
    if require_connected and missing:raise ValueError('peripheral ground contacts disconnected: '+str([(r['ref'],r['pad']) for r in missing]))
    return {'complete_ground_count':len(rows),'own_ground_count':len(own),'GH_ground_count':len(gh),
        'connected_count':len(rows)-len(missing),'contacts':rows,'disconnected':missing,
        'scope':'Source/native identity and continuity only; no physical current/contact or electrical acceptance'}
