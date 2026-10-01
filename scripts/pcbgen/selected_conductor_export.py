"""Explicit bijective net relabeling for the shared conductor extractor.

The existing extractor names its selected conductor AGND. A rail diagnostic
may use that role through this transparent relabeling; every geometric value,
UUID, board identity and native membership remains unchanged. The original
native export hash is retained. This is not a renamed physical PCB/netlist.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def select(data,net,original_sha256):
    if net not in ('+12V','-12V','+5V'):raise ValueError('explicit source rail required')
    sentinel='__original_native_AGND__'
    native_names=set(data['main_rail_members'])
    for collection in ('items','holes','zones'):
        for item in data[collection]:
            if 'net' in item:native_names.add(item['net'])
            elif collection!='zones' or not item.get('keepout'):
                raise ValueError('native conductor item has no explicit net identity')
    for row in data.get('routing',{}).get('net_classes',[]):native_names.update(row['nets'])
    native_names.update(row['net'] for row in data.get('routing',{}).get('zones',[]))
    if sentinel in native_names:raise ValueError('net alias would collide')
    if net not in data['main_rail_members']:raise ValueError('native rail component is absent')
    result=copy.deepcopy(data)
    def name(value):return 'AGND' if value==net else sentinel if value=='AGND' else value
    for collection in ('items','holes','zones'):
        for item in result[collection]:
            if 'net' in item:item['net']=name(item['net'])
    result['main_rail_members']={name(key):value for key,value in result['main_rail_members'].items()}
    for row in result.get('routing',{}).get('net_classes',[]):row['nets']=[name(n) for n in row['nets']]
    for row in result.get('routing',{}).get('zones',[]):row['net']=name(row['net'])
    selected=set(data['main_rail_members'][net])
    expected=[i['uuid'] for i in data['items'] if i['net']==net and i['uuid'] in selected]
    actual=[i['uuid'] for i in result['items'] if i['net']=='AGND' and i['uuid'] in selected]
    if expected!=actual:raise ValueError('conductor relabeling changed native membership')
    result['conductor_role_mapping']={'status':'EXPLICIT MATHEMATICAL RELABELING ONLY; physical native nets unchanged',
        'actual_native_net':net,'extractor_selected_role':'AGND','original_ground_alias':sentinel,
        'original_native_export_sha256':original_sha256,'selected_native_item_count':len(expected),
        'geometry_scope':'Only listed net-label fields change. Every primitive, contour, drill, layer, source UUID, board SHA and connected-component member is copied without alteration.'}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('native',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--net',required=True,choices=('+12V','-12V','+5V'),help='Use --net=-12V for the negative rail.')
    a=p.parse_args();raw=a.native.read_bytes();result=select(json.loads(raw),a.net,hashlib.sha256(raw).hexdigest())
    a.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(result['conductor_role_mapping']))
