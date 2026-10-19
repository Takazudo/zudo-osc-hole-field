"""Pure exact translation: integer coordinates, explicit net bijection, fresh IDs."""
import copy
from scripts.pcbgen.uuid_tools import stable_uuid

def translated(row, nets):
    if row['kind'] not in ('segment','via'):raise ValueError('unsupported copper')
    if len(set(nets.values())) != len(nets):raise ValueError('net mapping must be injective')
    r=copy.deepcopy(row)
    r['net']=nets[r['net']]
    for key in ('start_nm','end_nm','at_nm'):
        if key in r:r[key][0]+=34000000
    r['uuid']=stable_uuid('osc-jack-left','stage43-translation',row['uuid'])
    return r
