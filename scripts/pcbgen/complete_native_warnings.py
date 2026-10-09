"""Validate native fixture evidence, then append full hole observations to DRC.

Never delete or waive a native finding. Only additive, context-invariant boards
are supported. Both capped silk domains require the independent added-via audit.
The ordinary promotion gate still decides connectivity, errors and warnings.
"""
import collections
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import subprocess

from scripts.pcbgen.audit_hole_pairs import possible_pairs
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting, new_silk_identities
from scripts.pcbgen.uuid_tools import top_level_spans

HOLE_TYPES={'hole_to_hole','holes_co_located'}
SUPPORTED_CAPS=HOLE_TYPES | {'silk_overlap','silk_over_copper'}
SILK_TARGET_LAYERS={'F.Cu','B.Cu','F.SilkS','B.SilkS','F.Mask','B.Mask',
                    'F.Adhes','B.Adhes','F.Paste','B.Paste','F.CrtYd','B.CrtYd',
                    'F.Fab','B.Fab','Edge.Cuts','Margin'}


def unchanged_silk_zones(before, after):
    """Zone fills participate in native silk DRC, independently of new vias."""
    def relevant(text):
        result=collections.Counter()
        for a,b in top_level_spans(text):
            block=text[a:b]
            if not block.startswith('(zone') or re.search(r'\(keepout\s',block):continue
            match=re.search(r'\(layers?\s+([^)]*)\)',block)
            if not match:raise ValueError('zone layers missing')
            if set(re.findall(r'"([^"]+)"',match[1])) & SILK_TARGET_LAYERS:
                result[block]+=1
        return result
    if relevant(before)!=relevant(after):
        raise ValueError('silk-relevant zone fills changed; complete native zone evidence required')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def identity(v):return (v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items'])))
def normalized(rows):return {(a,b,tuple(c)) for a,b,c in rows}


def append_observations(drc, observations):
    result=copy.deepcopy(drc);known={identity(v) for v in drc['violations']}
    for kind,severity,ids in sorted(observations):
        if kind not in HOLE_TYPES:raise ValueError('unsupported appended observation')
        if (kind,severity,ids) not in known:
            result['violations'].append(dict(type=kind,severity=severity,items=[{'uuid':u} for u in ids],
                                            description='Complete pinned-native hole fixture observation'))
    return result


def check_caps(drc):
    counts=collections.Counter(v['type'] for v in drc['violations'] if v['severity']=='warning')
    if any(n>=199 and kind not in SUPPORTED_CAPS for kind,n in counts.items()):
        raise ValueError('unsupported capped warning domain')


def hole_evidence(root, board, drc, context):
    root=Path(root);audit=read(root/'result.json')
    if audit['version']!='10.0.6' or audit['source_sha256']!=sha(board):
        raise ValueError('hole audit native version/source mismatch')
    for key,value in context.items():
        if audit[key]!=value:raise ValueError('hole audit context mismatch: '+key)
    holes=audit['holes'];keys={h['object_key']:i for i,h in enumerate(holes)}
    if len(keys)!=len(holes):raise ValueError('duplicate full hole identity')
    for h in holes:
        row={k:v for k,v in h.items() if k!='object_key'}
        if hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()!=h['object_key']:
            raise ValueError('hole geometry key mismatch')
    pairs=set(possible_pairs(holes,context['clearance_nm']))
    if pairs!={tuple(p) for p in audit['covered_pairs']}:raise ValueError('hole pair enumeration incomplete')
    covered=set();observations=set();objects=set()
    for f in audit['fixtures']:
        folder=Path(f['fixture']).parent.name
        if not re.fullmatch(r'fixture-\d+',folder):raise ValueError('unexpected fixture path')
        indices=[keys[k] for k in f['holes']]
        if len(indices)!=len(set(indices)) or not 2<=len(indices)<=14:raise ValueError('unsafe fixture size')
        uuid_to_key={holes[i]['uuid']:holes[i]['object_key'] for i in indices}
        if len(uuid_to_key)!=len(indices):raise ValueError('ambiguous native fixture UUIDs')
        covered.update(tuple(sorted(p)) for p in itertools.combinations(indices,2))
        report=root/folder/'drc.json'
        if sha(report)!=f['report_sha256']:raise ValueError('native fixture report hash mismatch')
        for suffix,key in (('.kicad_pro','project_sha256'),('.kicad_dru','rules_sha256')):
            if sha(root/folder/Path(board).with_suffix(suffix).name)!=context[key]:
                raise ValueError('native fixture context changed')
        rows=[v for v in read(report)['violations'] if v['type'] in HOLE_TYPES]
        if len(rows)>len(indices)*(len(indices)-1):raise ValueError('hole fixture report cap/duplication')
        if collections.Counter(identity(v) for v in rows)!=collections.Counter((a,b,tuple(c)) for a,b,c in f['identities']):
            raise ValueError('hole receipt differs from raw native report')
        for v in rows:
            item=identity(v)
            if len(item[2])!=2 or not set(item[2])<=set(uuid_to_key):raise ValueError('foreign fixture identity')
            observations.add(item)
            objects.add((item[0],item[1],tuple(sorted(uuid_to_key[u] for u in item[2]))))
    if not pairs<=covered:raise ValueError('native pair coverage incomplete')
    if observations!=normalized(audit['identities']) or objects!=normalized(audit['object_identities']):
        raise ValueError('native identity union incomplete')
    if not {identity(v) for v in drc['violations'] if v['type'] in HOLE_TYPES}<=observations:
        raise ValueError('full-board native identity missing from audit')
    return audit,observations,objects


def complete_reports(before_board, after_board, before_drc, after_drc, before_audit, after_audit, mask_audit):
    before_board,after_board=Path(before_board),Path(after_board)
    for drc in (before_drc,after_drc):check_caps(drc)
    count=unchanged_nonrouting(before_board.read_text(),after_board.read_text())
    unchanged_silk_zones(before_board.read_text(),after_board.read_text())
    context={}
    for suffix,key in (('.kicad_pro','project_sha256'),('.kicad_dru','rules_sha256')):
        context[key]=sha(before_board.with_suffix(suffix))
        if sha(after_board.with_suffix(suffix))!=context[key]:raise ValueError('source context changed')
    rules=before_board.with_suffix('.kicad_dru').read_text()
    if re.search(r'\(\s*constraint\s+(?:hole|drilled|silk|solder)',rules):
        raise ValueError('custom audited-domain constraint unsupported')
    context['clearance_nm']=math.ceil(read(before_board.with_suffix('.kicad_pro'))['board']['design_settings']['rules']['min_hole_to_hole']*1e6)
    a,old,old_objects=hole_evidence(before_audit,before_board,before_drc,context)
    b,new,new_objects=hole_evidence(after_audit,after_board,after_drc,context)
    if new_objects-old_objects:raise ValueError('new complete native hole warning identities')
    old_holes={h['object_key']:h for h in a['holes']};new_holes={h['object_key']:h for h in b['holes']}
    if not old_holes.keys()<=new_holes.keys():raise ValueError('old holes removed/changed')
    added=[h for k,h in new_holes.items() if k not in old_holes]
    if any(h['kind']!='via' for h in added):raise ValueError('new pad geometry unsupported')
    expected={h['uuid'] for h in added}
    if len(expected)!=len(added):raise ValueError('new via UUID ambiguity')
    root=Path(mask_audit);mask=read(root/'result.json')
    if not mask.get('added_copper_scope_complete'):
        raise ValueError('new track silk interactions are not covered by via-only evidence')
    if mask['version']!='10.0.6' or mask['before_sha256']!=sha(before_board) or mask['after_sha256']!=sha(after_board):
        raise ValueError('silk audit native version/source mismatch')
    if mask['unchanged_nonrouting_objects']!=count:raise ValueError('silk invariance mismatch')
    from scripts.pcbgen.route_shards import copper_block_groups
    old_ids=set(copper_block_groups(before_board.read_text()));new_ids=set(copper_block_groups(after_board.read_text()))
    expected_copper=new_ids-old_ids
    if len(mask['fixtures'])!=len(expected_copper) or {f['copper_uuid'] for f in mask['fixtures']}!=expected_copper:
        raise ValueError('silk audit omits added copper')
    if {f['copper_uuid'] for f in mask['fixtures'] if f['kind']=='via'}!=expected:
        raise ValueError('silk audit added via scope mismatch')
    found=set()
    for i,f in enumerate(mask['fixtures']):
        folder=root/f'fixture-{i:03d}';report=folder/'drc.json'
        if sha(report)!=f['report_sha256']:raise ValueError('silk fixture report hash mismatch')
        for suffix,key in (('.kicad_pro','project_sha256'),('.kicad_dru','rules_sha256')):
            if sha(folder/after_board.with_suffix(suffix).name)!=context[key]:raise ValueError('silk fixture context changed')
        rows=new_silk_identities(read(report),f['copper_uuid'])
        if rows!=f['violations']:raise ValueError('silk receipt differs from raw native report')
        found.update(identity(v) for v in rows)
    if found!=normalized(mask['new_mask_identities']):raise ValueError('silk identity union incomplete')
    if found:raise ValueError('new complete native silk warning identities')
    return append_observations(before_drc,old),append_observations(after_drc,new),dict(
        status='COMPLETE NATIVE HOLE OBSERVATIONS APPENDED; NO ORIGINAL FINDING REMOVED',
        before_hole_identities=len(old),after_hole_identities=len(new),new_hole_object_identities=[],
        new_silk_identities=[],before_source_sha256=sha(before_board),after_source_sha256=sha(after_board),
        audit_result_sha256=[sha(Path(p)/'result.json') for p in (before_audit,after_audit,mask_audit)])


def audit_current_reports(before_board, after_board, before_drc, after_drc, output):
    """Produce evidence for these exact native boards; never reuse stale audits."""
    root=Path(__file__).resolve().parents[2]
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    before_audit=output/'holes-before';after_audit=output/'holes-after';mask_audit=output/'silk'
    # The pinned container mounts the checkout at /work, not the host path.
    relative=lambda p:str(Path(p).resolve().relative_to(root))
    commands=[['scripts/pcbgen/audit_hole_pairs.py',relative(before_board),relative(before_audit)],
              ['scripts/pcbgen/audit_hole_pairs.py',relative(after_board),relative(after_audit)],
              ['scripts/pcbgen/audit_added_mask.py',relative(before_board),relative(after_board),relative(mask_audit)]]
    for command in commands:
        subprocess.run(['bash','scripts/kicad/run.sh','python3',*command],cwd=root,check=True)
    result=complete_reports(before_board,after_board,before_drc,after_drc,before_audit,after_audit,mask_audit)
    for name,value in zip(('complete-before-drc','complete-after-drc','proof'),result):
        (output/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    return result
