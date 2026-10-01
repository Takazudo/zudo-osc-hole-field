"""Ordered balanced numerical functions with an exact named native reference."""


def ordered_profiles(geometry, port_limit=0):
    ports=geometry['ports'];data=geometry['data']
    keys=[(p['ref'],p['pad']) for p in ports]
    if len(set(keys))!=len(keys):raise ValueError('duplicate finite contact identity')
    mains=sorted((p for p in ports if p['kind']=='main'),key=lambda p:(p['ref'],p['pad']))
    headers=sorted((p for p in ports if p['kind']=='GH'),key=lambda p:(p['ref'],p['pad']))
    loads=sorted((p for p in ports if p['kind']=='load'),key=lambda p:(p['ref'],p['pad']))
    named=data.get('ground_reference')
    if named is None:
        if not mains:raise ValueError('no main or explicitly named ground reference')
        reference=mains[0]
    else:
        matches=[p for p in ports if (p['ref'],p['pad'])==(named['ref'],named['pad'])]
        if len(matches)!=1:raise ValueError('named reference is absent from complete finite contacts')
        reference=matches[0]
        physical=[i for i in data['items'] if (i.get('ref'),i.get('pad'))==(named['ref'],named['pad'])]
        if (len(physical)!=1 or physical[0]['net']!='AGND' or physical[0]['uuid']!=named['uuid']
                or set(physical[0]['copper'])!={named['layer']}
                or reference.get('physical_layer')!=named['layer'] or reference['kind']!='GH'):
            raise ValueError('named GH reference physical identity or face differs')
    if port_limit:
        import numpy as np
        selected=np.linspace(0,len(headers)-1,port_limit,dtype=int)
        headers=[headers[i] for i in selected]
    ordered=[p for p in headers+loads+mains if (p['ref'],p['pad'])!=(reference['ref'],reference['pad'])]
    if len({(p['ref'],p['pad']) for p in ordered})!=len(ordered):
        raise ValueError('sampled header functions contain duplicate contacts')
    if not ordered:raise ValueError('at least one balanced finite function is required')
    profiles=[[(p['layer'],p['patch'],1.),(reference['layer'],reference['patch'],-1.)] for p in ordered]
    identity={k:reference[k] for k in ('ref','pad','kind','layer','physical_layer') if k in reference}
    return mains,reference,ordered,profiles,identity
