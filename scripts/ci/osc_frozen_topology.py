"""Read-only native observations for one immutable PUBLIC board; no candidate ingestion."""
import hashlib
import json
import sys
from pathlib import Path

BOARD='boards/osc-core/osc-core.kicad_pcb'
BOARD_HASH='fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10'
STATUS='NATIVE_TOPOLOGY_OBSERVATIONS_NOT_ACCEPTANCE'
# Constants extracted from exact hash-pinned PUBLIC board.
EXPECTED = {'C1130.1': {'uuid': '14b906cd-7a69-50ea-8b9d-e8d44e3c2aa9', 'net': 'X96BBBE7E2F6614FCFBA7'}, 'C1130.2': {'uuid': '2c0813d5-5cfc-5190-b313-f76b3c6b42c5', 'net': 'AGND'}, 'C1111.1': {'uuid': '07c3263b-8e36-529c-ba2f-98ac5f6e32fe', 'net': 'X18B799A5334D35AC7DA4'}, 'C1111.2': {'uuid': '6e370474-ba32-594b-8c28-3b65ab475ff1', 'net': 'AGND'}, 'C1129.1': {'uuid': 'c05b8a0a-57c0-5d95-b350-d102fada2ba5', 'net': '+12V'}, 'C1129.2': {'uuid': '6b94427c-fb39-5000-99a0-e730dbd9a0dc', 'net': 'AGND'}, 'U1105.3': {'uuid': 'd96859b5-0d67-535a-84e0-65e431efc1a8', 'net': 'X96BBBE7E2F6614FCFBA7'}, 'U1105.11': {'uuid': 'd7e48140-2eb4-5352-b344-cd122c401282', 'net': 'X18B799A5334D35AC7DA4'}, 'U1105.12': {'uuid': '608c587b-7aab-54c1-b46c-3773193ec4c0', 'net': 'AGND'}, 'U1105.16': {'uuid': 'eb74c05a-78ff-545b-9c8d-4f97df7b2cd9', 'net': '+12V'}, 'C1131.1': {'uuid': '2e90dd0c-ebd7-5f2d-811f-608382ee5fef', 'net': '+12V'}, 'C1131.2': {'uuid': '61274621-8a49-5c06-b916-74a6d6ce8ecf', 'net': 'AGND'}, 'U1106.8': {'uuid': 'b5a3604a-e9fc-5483-a7b2-f0386e94ddf8', 'net': '+12V'}}
TRACKS = {'a2e996b6-0f19-5831-88eb-c54616ef74ed': 'AGND', '78a57192-9ee7-5e03-b428-d7073b7a8976': 'AGND', 'ccc30c50-bd1a-5356-a883-df5b67431b43': 'AGND', 'be37af5f-b79c-5fde-b6e0-56edf12612fd': '+12V', 'd48128fd-1ef5-532e-9504-260bfe185efc': '+12V', '3a33bfd8-90f9-5c78-a00a-54c46e75bf8c': '+12V', '7c573b4d-bf05-502c-8c41-02e3d2299962': '+12V', 'bd1502d5-bf7c-5ed3-a833-1fa8e07983e9': 'X96BBBE7E2F6614FCFBA7', 'fd7a6dae-4f93-5983-8bd4-42cdef309f52': 'X96BBBE7E2F6614FCFBA7', '42ee7ed3-41c6-511b-87c7-13e55e5ebfdf': 'X18B799A5334D35AC7DA4', 'fdf6137f-985c-5090-b5e9-023dcec9ee7a': 'X18B799A5334D35AC7DA4'}
ZONES = ['0b3a2f2d-a8db-5ec7-b328-2073823d9722', '3fee62c9-3c17-5ac9-8b80-648eef30162c', '418c65fc-bd04-5acf-8a07-1118bbc66aeb', '601e02b2-8ccb-5c28-83e5-03789d47fbbd', 'e389d344-872d-538e-9bfc-39577adb1686']
COPPER_LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
PAIRS = [('C1129.1', 'U1105.16'), ('C1130.1', 'U1105.3'), ('C1131.1', 'U1106.8'), ('C1111.1', 'U1105.11'), ('C1111.2', 'U1105.12')]
SUSPECTS = ['78a57192-9ee7-5e03-b428-d7073b7a8976', 'ccc30c50-bd1a-5356-a883-df5b67431b43']

def uid(item): return item.m_Uuid.AsString()

# Follow-up only for the three non-matching pairs from run 39748715341.
MISMATCH_PAIRS = [('C1129.1','U1105.16'), ('C1131.1','U1106.8'), ('C1111.2','U1105.12')]

def member_inventory(board, pcb, members):
    """Resolve native UUIDs to saved objects; never infer path connectivity."""
    endpoints = sorted({n for pair in MISMATCH_PAIRS for n in pair})
    wanted = {u for n in endpoints for u in members[n]}
    if len(wanted)>128: raise ValueError('Follow-up member bound exceeded')
    objects = {}; native_tracks={}; native_pads={}
    def add(item, kind, name=None):
        key=uid(item)
        if key not in wanted: return
        if key in objects: raise ValueError('Duplicate native object UUID')
        objects[key]={'kind':kind,'pad':name,'net':item.GetNetname(),
            'layers':[s for s in COPPER_LAYERS if item.IsOnLayer(getattr(pcb,s.replace('.','_')))]}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name=fp.GetReference()+'.'+pad.GetNumber()
            add(pad,'pad',name)
            if name in endpoints: native_pads[name]=pad
    for item in board.GetTracks():
        add(item,'track_or_via')
        if uid(item) in wanted: native_tracks[uid(item)]=item
    for item in board.Zones(): add(item,'zone')
    if set(objects)!=wanted: raise ValueError('Unresolved native member UUID')
    neighbors={}
    for key,item in sorted(native_tracks.items()):
        found=board.GetConnectivity().GetConnectedItems(item)
        if len(found)>128: raise ValueError('Follow-up neighbor bound exceeded')
        neighbors[key]=sorted({uid(i) for i in found})
    contacts=[]
    for name in endpoints:
        for key in members[name]:
            if key not in native_tracks: continue
            for layer in COPPER_LAYERS:
                contacts.append({'pad':name,'member':key,'layer':layer,
                    **contact_observation(native_pads[name],native_tracks[key],getattr(pcb,layer.replace('.','_')))})
    return {'objects':objects,'member_reported_neighbors':neighbors,'pad_member_shape_contacts':contacts,'pairs':[{'a':a,'b':b,
        'a_members':members[a], 'b_members':members[b],
        'shared_members':sorted(set(members[a]) & set(members[b]))}
        for a,b in MISMATCH_PAIRS],
        'meaning':'UUID attribution only; shared membership is not a proven conductive path'}

def contact_observation(pad,track,layer):
    # Connectivity membership must not be used as a foreign-net collision filter.
    if not pad.IsOnLayer(layer) or not track.IsOnLayer(layer):
        return {'shared_layer':False,'shape_intersection':False}
    result=pad.GetEffectiveShape(layer).Collide(track.GetEffectiveShape(layer),0)
    if type(result) is not bool: raise ValueError('Unsupported shape collision result type')
    return {'shared_layer':True,'shape_intersection':result}

def observe(board,pcb):
    pads={}; tracks={}; zones={}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            key=fp.GetReference()+'.'+pad.GetNumber()
            if key not in EXPECTED: continue
            if key in pads or {'uuid':uid(pad),'net':pad.GetNetname()}!=EXPECTED[key]:
                raise ValueError('Public pad identity mismatch: '+key)
            pads[key]=pad
    if set(pads)!=set(EXPECTED):raise ValueError('Missing selected pad')
    for item in board.GetTracks():
        if uid(item) in TRACKS:
            if uid(item) in tracks or item.GetNetname()!=TRACKS[uid(item)]:raise ValueError('Track identity mismatch')
            tracks[uid(item)]=item
    for z in board.Zones():
        if uid(z) in ZONES:
            if uid(z) in zones:raise ValueError('Duplicate zone')
            zones[uid(z)]=z
    if set(tracks)!=set(TRACKS) or set(zones)!=set(ZONES):raise ValueError('Missing track/zone UUID')
    conn=board.GetConnectivity()
    # Existing pinned-source extractors use this to build native connectivity;
    # this does not refill zones or serialize the board.
    conn.RecalculateRatsnest()
    members={}
    for name,pad in pads.items():
        items=conn.GetConnectedItems(pad)
        if len(items)>20000:raise ValueError('Native membership output bound exceeded')
        members[name]=sorted({uid(i) for i in items})
    pairs=[{'a':a,'b':b,'b_reported_by_a':uid(pads[b]) in members[a],
            'a_reported_by_b':uid(pads[a]) in members[b]} for a,b in PAIRS]
    collisions=[{'track':t,'pad':'U1105.16','layer':'B.Cu',
        'track_net':tracks[t].GetNetname(),'pad_net':pads['U1105.16'].GetNetname(),
        **contact_observation(pads['U1105.16'],tracks[t],pcb.B_Cu)} for t in SUSPECTS]
    zone_rows=[]
    for key,z in zones.items():
        layers=[]
        for name in COPPER_LAYERS:
            layer=getattr(pcb,name.replace('.','_'))
            if z.IsOnLayer(layer):
                layers.append({'layer':name,'saved_filled_outline_count':z.GetFilledPolysList(layer).OutlineCount()})
        zone_rows.append({'uuid':key,'net':z.GetNetname(),'rule_area':z.GetIsRuleArea(),'layers':layers})
    return {'status':STATUS,'pairs':pairs,'native_reported_members':members,
        'mismatch_member_inventory':member_inventory(board,pcb,members),
        'foreign_net_shape_observations':collisions,'zones':zone_rows,
        'pad_copper_layers':{n:[s for s in COPPER_LAYERS if p.IsOnLayer(getattr(pcb,s.replace('.','_')))] for n,p in pads.items()},
        'limits':['GetConnectedItems observations are not an independently traversed path or DRC.',
          'Saved filled-outline counts do not establish fill freshness or thermal connectivity.',
          'Public SMD board only; no candidate placement or through-hole substitution evaluated.'],
        'return_terminal_selection':None,'copper_retirement':[],'board_acceptance':False}

def validate(result):
    follow=result.get('mismatch_member_inventory')
    if not isinstance(follow,dict) or not isinstance(follow.get('objects'),dict): raise ValueError('Missing follow-up inventory')
    members=result.get('native_reported_members',{})
    endpoints={n for pair in MISMATCH_PAIRS for n in pair}
    if not endpoints<=set(members): raise ValueError('Missing follow-up endpoint')
    wanted={u for n in endpoints for u in members[n]}
    if len(wanted)>128 or set(follow['objects'])!=wanted: raise ValueError('Incomplete follow-up inventory')
    expected=[{'a':a,'b':b,'a_members':members[a],'b_members':members[b],
        'shared_members':sorted(set(members[a]) & set(members[b]))} for a,b in MISMATCH_PAIRS]
    if follow.get('pairs')!=expected: raise ValueError('Follow-up pair mismatch')
    for row in follow['objects'].values():
        if row.get('kind') not in ('pad','track_or_via','zone') or not isinstance(row.get('net'),str): raise ValueError('Invalid object attribution')
        layers=row.get('layers')
        if not isinstance(layers,list) or not layers or len(layers)!=len(set(layers)) or not set(layers)<=set(COPPER_LAYERS): raise ValueError('Invalid object layers')
        if row['kind']=='pad' and (not isinstance(row.get('pad'),str) or not row['pad']): raise ValueError('Missing pad attribution')
        if row['kind']!='pad' and row.get('pad') is not None: raise ValueError('Spurious pad attribution')
    contacts=follow.get('pad_member_shape_contacts')
    neighbors=follow.get('member_reported_neighbors')
    if not isinstance(neighbors,dict) or set(neighbors)!={u for u,r in follow['objects'].items() if r['kind']=='track_or_via'}: raise ValueError('Missing neighbor observations')
    for ids in neighbors.values():
        if not isinstance(ids,list) or len(ids)>128 or any(not isinstance(u,str) or not u for u in ids) or len(ids)!=len(set(ids)): raise ValueError('Invalid neighbor observations')
    expected_keys=[(n,u,l) for n in sorted(endpoints) for u in members[n]
        if follow['objects'][u]['kind']=='track_or_via' for l in COPPER_LAYERS]
    if not isinstance(contacts,list) or [(c.get('pad'),c.get('member'),c.get('layer')) for c in contacts]!=expected_keys: raise ValueError('Incomplete contact observations')
    for c in contacts:
        if any(type(c.get(k)) is not bool for k in ('shared_layer','shape_intersection')): raise ValueError('Invalid contact observation')
        if c['shape_intersection'] and not c['shared_layer']: raise ValueError('Contact without shared layer')
    required={'status','board_acceptance','copper_retirement','return_terminal_selection','pairs','native_reported_members','foreign_net_shape_observations','zones','pad_copper_layers','limits'}
    if not required<=set(result):raise ValueError('Missing evidence fields')
    if result.get('status')!=STATUS or result.get('board_acceptance') is not False or result.get('copper_retirement')!=[] or result.get('return_terminal_selection') is not None:
        raise ValueError('Invalid result authority')
    if set(result.get('native_reported_members',{}))!=set(EXPECTED):raise ValueError('Incomplete membership observations')
    if [(p['a'],p['b']) for p in result.get('pairs',[])]!=PAIRS:raise ValueError('Pair scope mismatch')
    if {z['uuid'] for z in result.get('zones',[])}!=set(ZONES):raise ValueError('Zone scope mismatch')
    if [r['track'] for r in result.get('foreign_net_shape_observations',[])]!=SUSPECTS:raise ValueError('Collision scope mismatch')
    for p in result['pairs']:
        if any(type(p.get(k)) is not bool for k in ('b_reported_by_a','a_reported_by_b')):raise ValueError('Invalid membership flags')
    for name,ids in result['native_reported_members'].items():
        if not isinstance(ids,list) or len(ids)>20000 or any(not isinstance(u,str) or not u for u in ids) or len(ids)!=len(set(ids)):raise ValueError('Invalid native membership IDs')
    if set(result['pad_copper_layers'])!=set(EXPECTED):raise ValueError('Pad layer coverage')
    for layers in result['pad_copper_layers'].values():
        if not isinstance(layers,list) or not layers or len(layers)!=len(set(layers)) or not set(layers)<=set(COPPER_LAYERS):raise ValueError('Invalid pad layers')
    for r in result['foreign_net_shape_observations']:
        if r.get('pad')!='U1105.16' or r.get('layer')!='B.Cu' or r.get('track_net')!=TRACKS[r['track']] or r.get('pad_net')!=EXPECTED['U1105.16']['net']:raise ValueError('Collision identity mismatch')
        if any(type(r.get(k)) is not bool for k in ('shared_layer','shape_intersection')):raise ValueError('Invalid collision flags')
        if r['shape_intersection'] and not r['shared_layer']:raise ValueError('Intersection without shared layer')
    if len(result['zones'])!=len(ZONES):raise ValueError('Duplicate zone')
    for z in result['zones']:
        if not isinstance(z.get('net'),str) or type(z.get('rule_area')) is not bool or not isinstance(z.get('layers'),list):raise ValueError('Invalid zone evidence')
        names=[r['layer'] for r in z['layers']]
        if not names or len(names)!=len(set(names)) or not set(names)<=set(COPPER_LAYERS):raise ValueError('Invalid zone layers')
        for r in z['layers']:
            if type(r.get('saved_filled_outline_count')) is not int or r['saved_filled_outline_count']<0:raise ValueError('Invalid saved-fill count')

def main():
    if len(sys.argv)!=1:raise ValueError('Arbitrary inputs unsupported')
    path=Path('/work')/BOARD;before=hashlib.sha256(path.read_bytes()).hexdigest()
    if before!=BOARD_HASH:raise ValueError('Public board hash mismatch')
    import pcbnew
    if pcbnew.GetBuildVersion()!='10.0.6':raise ValueError('pcbnew version mismatch')
    result=observe(pcbnew.LoadBoard(str(path)),pcbnew)
    validate(result)
    after=hashlib.sha256(path.read_bytes()).hexdigest()
    if after!=before:raise ValueError('Input changed')
    result.update(before=before,after=after,version=pcbnew.GetBuildVersion())
    encoded=json.dumps(result,sort_keys=True)
    if len(encoded.encode())>900000:raise ValueError('Topology receipt exceeds bounded stdout budget')
    print(encoded)

if __name__=='__main__':main()
