"""Frozen virtual FH12 endpoint inventory; never infer a physical pad-1 map."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
MANIFEST=Path(__file__).with_name('manifest.json')
GATE='design/stack/geometry/links/link-gate.json'
GOPTS='design/stack/geometry/links/link-gate-options.json'
OPTS='design/stack/geometry/links/link-options.json'
DIRECTIONS={'+x':(1,0),'-x':(-1,0),'+y':(0,1),'-y':(0,-1)}


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def verify_pins(root,manifest):
    for name,pin in manifest['sha256'].items():
        if sha(root/name)!=pin:raise ValueError('source pin changed: '+name)


def scan_board_names(root,boards):
    """Absence of literal FH12 is a source-name observation, not component identity proof."""
    matches=[]
    for board,path in sorted(boards.items()):
        with (root/path).open() as stream:
            for number,line in enumerate(stream,1):
                if 'fh12' in line.lower():matches.append({'board':board,'path':path,'line':number,'text':line.strip()})
    return matches


def endpoint_rows(link):
    direction=DIRECTIONS[link['direction']]
    if sorted(p['pos'] for p in link['positions'])!=list(range(1,link['circuits']+1)):
        raise ValueError('logical positions incomplete/duplicated: '+link['id'])
    rows=[]
    for endpoint,board,key,sign in (('front',link['front_board'],'front_connector',1),('K','K','K_connector',-1)):
        rect=link['geometry'][key]
        if len(rect)!=4 or not all(math.isfinite(v) for v in rect) or rect[0]>=rect[2] or rect[1]>=rect[3]:
            raise ValueError('invalid virtual field rectangle')
        center=[round((rect[0]+rect[2])/2,4),round((rect[1]+rect[3])/2,4)]
        rows.append({'endpoint_id':link['id']+':'+endpoint,'link_id':link['id'],'endpoint':endpoint,
            'representation':'virtual courtyard-level connector field; no generated FH12 footprint placement',
            'connector_identity':link['connector'],'cable_code':link['cable'],'contacts':link['circuits'],
            'board':board,'board_face':'B','specified_contact_side':'bottom contact',
            'field_rectangle_panel_mm':rect,'field_center_panel_mm':center,
            'direction_from_field_toward_slot':[sign*v for v in direction],
            'direction_scope':'Geometric field-to-slot direction only; not a numbered-contact handedness or footprint rotation',
            'physical_reference':None,'footprint_rotation_deg':None,'pad1_local_mm':None,'pad1_panel_mm':None,
            'numbered_pad_coordinates':None,'physical_mapping_status':'NOT_ESTABLISHED',
            'logical_position_1':next(p for p in link['positions'] if p['pos']==1),
            'logical_positions':link['positions'],
            'mapping_gap':'Logical positions are not linked to a generated numbered pad or primary contact-1 drawing coordinate',
            'source_locator':GATE+' links[id='+link['id']+'].geometry.'+key,
            'face_basis':'scripts/stack/geometry/links_gate_part2.py Field.__init__: front_connector and K_connector indexed on B'})
    return rows


def build(gate,gopts,opts,kernel):
    links=[r for r in gate['links'] if not r.get('gone')]
    if len(links)!=61 or len({r['id'] for r in links})!=61 or not all(r.get('placed') for r in links):
        raise ValueError('61 unique placed virtual links required')
    endpoints=[]
    for row in links:
        direction=DIRECTIONS[row['direction']]
        size=kernel.fh12_size(row['circuits'],gopts,{'cable':row['cable'],'cable_length_mm':row['cable_length_mm']})
        if size['connector']!=row['connector']:raise ValueError('connector identity mismatch')
        geometry=kernel.gate_geometry(*row['slot_centre'],direction,size,opts,
            ef=row['geometry']['front_extension_mm'],ek=row['geometry']['K_extension_mm'],
            hard=row['geometry']['tail_rule_hard_mm'])
        if geometry!=row['geometry']:raise ValueError('retained virtual geometry does not reproduce: '+row['id'])
        endpoints.extend(endpoint_rows(row))
    return endpoints


def run(root=ROOT):
    manifest=json.loads(MANIFEST.read_text());verify_pins(root,manifest)
    observed=scan_board_names(root,manifest['boards'])
    if observed:raise ValueError('FH12-named board objects require explicit physical mapping review: '+json.dumps(observed))
    sys.path.insert(0,str(root/'scripts/stack/geometry'))
    import links_gate as kernel
    gate,gopts,opts=[json.loads((root/p).read_text()) for p in (GATE,GOPTS,OPTS)]
    endpoints=build(gate,gopts,opts,kernel)
    verify_pins(root,manifest)
    return {'engineering_commit':manifest['engineering_commit'],'inputs_sha256':manifest['sha256'],
            'virtual_links':61,'virtual_endpoints':len(endpoints),'physical_mappings_established':0,
            'board_source_scan':{'files':manifest['boards'],'FH12_literal_matches':observed,
                                 'scope':'Literal source-name observation only, not exhaustive manufacturer identity inference'},
            'endpoints':endpoints,
            'scope':'Project-source extraction only. Primary-drawing contact1 correspondence, physical footprint rotations/pads, mounted latch access and acceptance remain unestablished. No native, geometry changes, adoption or manufacturing.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
    print(json.dumps(run(),indent=2))


if __name__=='__main__':main()
