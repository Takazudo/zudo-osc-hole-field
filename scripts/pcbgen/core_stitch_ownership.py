"""Exact 52-header / 104-via source ownership before native mutation."""
import math
from scripts.pcbgen.uuid_tools import stable_uuid


def validate(stitch,manifest,basis):
    if basis['board_id']!='osc-core' or stitch['source_board_sha256']!=basis['board_sha256'] or stitch['unresolved']:
        raise ValueError('K stitch source board or unresolved state differs')
    headers={}
    for port in manifest['selected_K_ground_ports']:headers.setdefault(port['header_id'],set()).add((port['ref'],port['pad']))
    if len(headers)!=52 or sum(map(len,headers.values()))!=206:raise ValueError('K source interface inventory changed')
    pads={(i['ref'],i['pad']):i for i in basis['items'] if 'ref' in i}
    counts={h:0 for h in headers};seen=set()
    for row in stitch['added']:
        header=row['header_id']
        if header not in headers:raise ValueError('K stitch references foreign header')
        index=counts[header];counts[header]+=1
        if row['uuid'] in seen or row['uuid']!=stable_uuid('osc-core','ground-stitch:'+header,str(index)):
            raise ValueError('K stitch UUID ownership differs or repeats')
        seen.add(row['uuid'])
        if len(row['ports'])!=len(headers[header]) or {(p['ref'],p['pad']) for p in row['ports']}!=headers[header]:
            raise ValueError('K stitch source pad set differs')
        if row['net']!='AGND' or row['diameter_mm']!=.7 or row['drill_mm']!=.3 or row['layers']!=['F.Cu','B.Cu']:
            raise ValueError('K stitch finite geometry class differs')
        if len(row['xy_mm'])!=2 or any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) for v in row['xy_mm']):
            raise ValueError('K stitch finite coordinates required')
        for p in row['ports']:
            native=pads[p['ref'],p['pad']]
            if native['net']!='AGND' or native['uuid']!=p['uuid'] or native['xy_mm']!=p['native_xy_mm'] or list(native['copper'])!=p['native_layers'] or set(native['copper'])!={'F.Cu'}:
                raise ValueError('K stitch source/native port identity differs')
    if len(seen)!=104 or any(v!=2 for v in counts.values()):raise ValueError('K requires two exact stitches per selected header')
    return {'header_count':52,'ground_contact_count':206,'added_via_count':104,'new_tracks':0}
