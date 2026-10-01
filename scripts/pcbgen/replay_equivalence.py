"""Exact native replay comparison with proven other-board override metadata."""
import copy
import hashlib
from pathlib import Path


def verify_export_provenance(data, board_id, board, project, extractor):
    """Bind cached geometry to its supplied physical inputs before comparing it."""
    if data.get('board_id') != board_id:
        raise ValueError('cached native export board identity mismatch')
    expected = {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                for name, path in (('board_sha256', board),
                                   ('project_sha256', project),
                                   ('extractor_sha256', extractor))}
    for name, value in expected.items():
        if data.get(name) != value:
            raise ValueError('cached native export provenance mismatch: ' + name)
    return expected


def normalize(data, partition):
    board=[b for b in partition['boards'] if b['id']==data['board_id']]
    if len(board)!=1:raise ValueError('native export lacks exact source board identity')
    key=board[0]['board_key']
    rows=partition['assignment']['components']
    assigned={r['ref']:r for r in rows}
    if len(assigned)!=len(rows):raise ValueError('duplicate independent source assignment')
    native_refs={r['ref'] for r in data['items'] if 'ref' in r}
    result={k:copy.deepcopy(data[k]) for k in ('outline_mm','coordinate_frame','native_project_rules','routing','stackup','main_rail_members')}
    unused=[];applicable=[]
    for override in result['routing'].get('local_escape_overrides',[]):
        ref=override['ref']
        if ref not in assigned:raise ValueError('escape override lacks independent source assignment')
        if assigned[ref]['board']!=key:
            if ref in native_refs:raise ValueError('other-board override reference is actually present in native board')
            unused.append({'override':override,'source_board':assigned[ref]['board'],
                           'audited_board':key,'native_reference_absent':True})
        else:applicable.append(override)
    if 'local_escape_overrides' in result['routing']:
        result['routing']['local_escape_overrides']=applicable
    for collection in ('items','holes','zones','clusters'):
        identity='id' if collection=='clusters' else 'uuid';rows=data[collection]
        if len({r[identity] for r in rows})!=len(rows):raise ValueError('duplicate native geometry identity: '+collection)
        result[collection]=sorted(rows,key=lambda r:r[identity])
    return result,unused


def compare(original,replayed,partition):
    if original['board_id']!=replayed['board_id']:raise ValueError('native replay board identity changed')
    before,old_unused=normalize(original,partition)
    after,new_unused=normalize(replayed,partition)
    if before!=after:raise ValueError('native replay changed conductor geometry or an applicable source rule')
    key=lambda row:(row['override']['ref'],row['override']['pad'],row['override']['net'])
    old={key(row):row for row in old_unused};new={key(row):row for row in new_unused}
    if len(old)!=len(old_unused) or len(new)!=len(new_unused):raise ValueError('duplicate inapplicable override identity')
    return [{'identity':list(k),'before':old.get(k),'after':new.get(k)}
            for k in sorted(old.keys()|new.keys()) if old.get(k)!=new.get(k)]
