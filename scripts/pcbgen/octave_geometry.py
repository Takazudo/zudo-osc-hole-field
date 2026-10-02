"""Exact source outline and unfilled zone definitions; no physical admission."""
from collections import Counter
from decimal import Decimal,InvalidOperation
from scripts.pcbgen.netlist import parse,TOKEN,one,many
from scripts.pcbgen.uuid_tools import stable_uuid


def canonical(value):
    if isinstance(value,list):return tuple(canonical(v) for v in value)
    try:return Decimal(value)
    except (InvalidOperation,TypeError):return value


def verify_geometry(raw,definition):
    tree,_=parse(TOKEN.findall(raw.decode()))
    outline=definition.outline
    if definition.corner_radius_mm!=0:raise ValueError('unsupported adapter corner source')
    expected=Counter()
    for i,p in enumerate(outline):
        q=outline[(i+1)%len(outline)]
        ends=tuple(sorted(((round((p[0]+100)*1e6),round((p[1]+50)*1e6)),(round((q[0]+100)*1e6),round((q[1]+50)*1e6)))))
        expected[(ends,50000)]+=1
    actual=Counter()
    objects=tree[1:]+[item for fp in many(tree,'footprint') for item in fp[1:] if isinstance(item,list)]
    for item in objects:
        if not isinstance(item,list) or not many(item,'layer') or one(item,'layer')[1]!='Edge.Cuts':continue
        if item[0]!='gr_line':raise ValueError('unexpected adapter edge feature')
        ends=tuple(sorted(tuple(round(float(x)*1e6) for x in one(item,key)[1:]) for key in ('start','end')))
        stroke=one(item,'stroke')
        if one(stroke,'type')[1]!='default':raise ValueError('unexpected edge stroke')
        actual[(ends,round(float(one(stroke,'width')[1])*1e6))]+=1
    if actual!=expected:raise ValueError('native adapter outline differs from fixed source')
    zones=many(tree,'zone');expected_zones=[]
    for spec in definition.routing['zones']:
        for layer in spec['layers']:
            expected_zones.append(['zone',['net',spec['net']],['layer',layer],['uuid',stable_uuid(definition.board_id,'pour',spec['name']+':'+layer)],
                ['name',f'pcbgen:{definition.board_id}:pour:{spec["name"]}:{layer}'],['hatch','edge','.5'],
                ['connect_pads','yes',['clearance',str(spec['clearance_mm'])]],['min_thickness',str(spec['min_thickness_mm'])],
                ['fill','yes',['thermal_gap','.5'],['thermal_bridge_width','.5'],['island_removal_mode','0']],
                ['polygon',['pts',*(['xy',str(x+100),str(y+50)] for x,y in spec.get('polygon',outline))]]])
    actual_zones=[[item for item in zone if not isinstance(item,list) or item[0]!='filled_polygon'] for zone in zones]
    if Counter(canonical(z) for z in actual_zones)!=Counter(canonical(z) for z in expected_zones):
        raise ValueError('saved zone definition differs from source routing')
