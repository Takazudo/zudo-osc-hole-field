"""Logical connector/land source capture of all270 transport graph nodes.

No DIN drilling/land geometry, new component identity, native run or PCB is created.
"""
import json
from pathlib import Path
import stage17_assets as assets

ROOT=assets.ROOT
MECHANICAL=ROOT/'design/architecture-278/implementation/stage10/mechanical-report.json'
LIB='A01Transport'
need=assets.need


def symbol(name,row,footprint):
    enabled=lambda flag:'yes' if flag else 'no'
    properties=[assets.property_source('Reference','TP' if not row['in_bom'] else 'J',48,False),
        assets.property_source('Value',row['unit_records'][0]['value'],-48,False),
        assets.property_source('MPN',row['selected_mpn'] or ''),
        assets.property_source('Manufacturer',row['selected_manufacturer'] or ''),
        assets.property_source('Footprint',footprint),assets.property_source('Datasheet',''),assets.property_source('LCSC','')]
    pins=[]
    order=sorted(row['pins'],key=lambda p:(p.rstrip('0123456789'),int(p[len(p.rstrip('0123456789')):] or 0)))
    for index,number in enumerate(order):
        if row['source_kind']=='DIN':
            column,offset=divmod(index,32);x=-33.02+column*25.4;y=39.37-offset*2.54
        else:x=-5.08;y=(len(order)-1)*1.27-index*2.54
        pins.append(f'(pin passive line (at {x} {y} 0) (length 2.54) (name {assets.quoted(number)} (effects (font (size 0.9 0.9)))) (number {assets.quoted(number)} (effects (font (size 0.9 0.9)))))')
    return f'(symbol "{name}" (in_bom {enabled(row["in_bom"])}) (on_board {enabled(row["on_board"])})\n'+ '\n'.join(properties)+f'\n(symbol "{name}_1_1"\n'+'\n'.join(pins)+'\n))'


def build_transport(inp):
    graph=inp['transport_contract']; nodes=graph['nodes']; mechanical=json.loads(MECHANICAL.read_text())
    need(len(graph['headers'])==8,'eight retained GH headers')
    rows={};bindings={};definitions=[]

    def add(ref,pins,sources,mpn,manufacturer,kind,board,footprint,value,in_bom=True,on_board=True,source=None):
        need(set(pins)==set(sources),'source node map pin coverage')
        for pin,nodeid in sources.items():
            need(nodeid in nodes and nodes[nodeid]['pin']==pin and nodes[nodeid]['net']==pins[pin] and nodes[nodeid]['kind']==kind,'exact source node binding')
        attrs={'MPN':mpn or '', 'Manufacturer':manufacturer or '',
            'SourceGraphNodes':json.dumps(sources,sort_keys=True,separators=(',',':')),
            'SourceRole':'TRANSPORT','SourceKind':kind,
            'FootprintStatus':'RETAINED_SOURCE_FOOTPRINT' if footprint else 'UNBOUND_SCHEMATIC_ONLY'}
        row={'ref':ref,'pins':pins,'source_nodes':sources,'source_kind':kind,
            'selected_mpn':mpn,'selected_manufacturer':manufacturer,'supplier_order_code':None,
            'identity_status':'EXACT_RETAINED_TRANSPORT_IDENTITY' if mpn else 'NON_BOM_SOURCE_LAND_ANNOTATION',
            'placement':{'board':board},'unit_records':[{'unit':1,'value':value,'pins':pins,'attributes':attrs}],
            'in_bom':in_bom,'on_board':on_board,'footprint_status':attrs['FootprintStatus'],
            'footprint_source':source,'native_validated':False,
            'scope':'Logical source capture only; blank footprint means no native land/drill/board geometry claim.'}
        name='A01_'+ref;text=symbol(name,row,footprint);units,pindata=assets.symbol_metadata(text)
        need(set(pindata)==set(pins) and units==[1],'transport symbol pins')
        definitions.append(text);rows[ref]=row
        bindings[ref]={'symbol_lib_id':LIB+':'+name,'footprint_lib_id':footprint,
            'symbol_units':[1],'pin_to_unit':dict.fromkeys(pins,1),'pins':pindata,
            'source_nodes':sources,'source_footprint_path':source,'native_validated':False,
            'asset_status':'GENERATED_LOGICAL_SOURCE_ONLY','footprint_status':attrs['FootprintStatus']}

    for index,(oldref,header) in enumerate(sorted(graph['headers'].items()),17901):
        pins=header['pins'];sources={pin:oldref+':'+pin for pin in pins}
        add('J'+str(index),pins,sources,header['header_mpn'],'JST','GH',header['board'],
            'A01Candidate:'+Path(header['source']).stem,header['header_mpn'],source=header['source'])
    for ref,side,expected in [('J17909','middle','09032966824'),('J17910','rear','09031966922')]:
        connector=mechanical['din_connectors'][side]
        need(connector['mpn']==expected,'frozen DIN identity')
        oldref=connector['ref'];pins=connector['pins'];sources={pin:'DIN:'+side+':'+pin for pin in pins}
        need(pins==graph['DIN_pinmap'] and len(pins)==96,'full DIN source96pinmap')
        add(ref,pins,sources,expected,'HARTING','DIN','A01-middle' if side=='middle' else 'A01-core','',expected)
    tails=sorted((key,node) for key,node in nodes.items() if node['kind'] in ('terminal_land','LED_wire_land'))
    need(len(tails)==22,'22source land annotations')
    for index,(key,node) in enumerate(tails,17901):
        pin=node['pin']
        add('TP'+str(index),{pin:node['net']},{pin:key},None,None,node['kind'],'A01-jack' if node['kind']=='terminal_land' else 'A01-fixed','',
            'Source land: '+key,False,False)
    represented=[key for row in rows.values() for key in row['source_nodes'].values()]
    wanted={key for key,node in nodes.items() if node['kind']!='source'}
    need(len(represented)==len(set(represented))==270 and set(represented)==wanted,'all270transportnodes exactly once')
    need(len(rows)==32,'10connectors22annotations')
    text='(kicad_symbol_lib (version 20231120) (generator "stage17-source")\n'+'\n'.join(definitions)+'\n)\n'
    files={LIB+'.kicad_sym':text,
        'transport-component-rows.json':json.dumps(rows,sort_keys=True,indent=2)+'\n',
        'transport-component-bindings.json':json.dumps(bindings,sort_keys=True,indent=2)+'\n'}
    return files,bindings,rows
