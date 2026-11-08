#!/usr/bin/env python3
"""Copper UUID identity: inventory, fail-closed ambiguity rejection and a dry-run normalization proposal.

A KiCad UUID is supposed to name one copper object. Legacy boards carry UUIDs that
name two distinct objects (see legacy-copper-duplicates.json). Every tool that
selects copper by UUID (cut lists, removal scopes, rip-up sets) must refuse such
an ambiguous selection before any dictionary collapses the group to one object.

Boards are read as text through uuid_tools.top_level_spans, never through pcbnew.
Text is decoded as latin-1 so that every offset and digest here is byte-exact.
Nothing in this module writes under boards/; the proposal is a dry run bound to
the exact input bytes, and migrating a canonical board remains a reviewed wave.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,sys,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE,replace_spans

ROOT=Path(__file__).resolve().parents[2]
COPPER_KINDS=('segment','via','arc')
LEGACY_ALLOWLIST=Path(__file__).with_name('legacy-copper-duplicates.json')
MANIFEST_SCHEMA='copper-identity-normalization/1'
# Separate namespace from uuid_tools.NAMESPACE so a renamed occurrence can never
# reproduce a generator-owned stable_uuid by coincidence of key layout.
NORMALIZATION_NAMESPACE=uuid.UUID('4a3a6a1e-0d0f-5b64-9a2b-7e9c8d1f2a35')
KIND_RE=re.compile(r'\(([A-Za-z0-9_]+)')
NET_RE=re.compile(r'\(net\s+"((?:[^"\\]|\\.)*)"\)')
LAYER_RE=re.compile(r'\(layer\s+"([^"]+)"\)')
LAYERS_RE=re.compile(r'\(layers((?:\s+"[^"]+")+)\)')
SCALAR_RE={k:re.compile(r'\('+k+r'\s+([-0-9.eE+]+)\)') for k in ('width','size','drill')}
POINT_RE={k:re.compile(r'\('+k+r'\s+([-0-9.eE+]+)\s+([-0-9.eE+]+)\)') for k in ('start','mid','end','at')}


def reject_new_uuid_collisions(existing,rows):
    seen=set(existing)
    for row in rows:
        uid=row['uuid']
        if uid in seen:raise ValueError('new copper UUID collides with surviving geometry: '+uid)
        seen.add(uid)


def retention(before,after):
    old=[i for kind in ('tracks','vias') for i in before[kind]]
    new=[i for kind in ('tracks','vias') for i in after[kind]]
    def geometry(items):return collections.Counter(json.dumps(i,sort_keys=True,separators=(',',':')) for i in items)
    a,b=geometry(old),geometry(new)
    old_ids=collections.Counter(i['uuid'] for i in old);new_ids=collections.Counter(i['uuid'] for i in new)
    old_groups=collections.defaultdict(list);new_groups=collections.defaultdict(list)
    for i in old:old_groups[i['uuid']].append(i)
    for i in new:new_groups[i['uuid']].append(i)
    return {'counting':'multiset of full object geometry and UUID; duplicate IDs are not collapsed',
        'before':len(old),'after':len(new),'identical':sum((a&b).values()),
        'removed_objects':sum((a-b).values()),'added_objects':sum((b-a).values()),
        'before_unique_uuids':len(old_ids),'after_unique_uuids':len(new_ids),
        'duplicate_uuids_before':{u:n for u,n in old_ids.items() if n>1},
        'duplicate_uuids_after':{u:n for u,n in new_ids.items() if n>1},
        'removed_uuids':sorted(old_ids.keys()-new_ids.keys()),'added_uuids':sorted(new_ids.keys()-old_ids.keys()),
        'changed_existing_uuids':sorted(u for u in old_ids.keys()&new_ids.keys() if geometry(old_groups[u])!=geometry(new_groups[u]))}


# ---------------------------------------------------------------- byte-exact text

def load_board_text(path):
    """Board bytes as a str whose indices are byte offsets (latin-1 is a bijection on bytes)."""
    return Path(path).read_bytes().decode('latin-1')


def board_bytes(text):
    return text.encode('latin-1')


def digest(text):
    return hashlib.sha256(board_bytes(text)).hexdigest()


# ---------------------------------------------------------------- inventory

def require_unique(objects_by_uuid,uuids,context):
    """Refuse, before any dict collapse, every selected UUID that names more than one object."""
    ambiguous=sorted(u for u in set(uuids) if len(objects_by_uuid.get(u,()))>1)
    if ambiguous:
        raise ValueError(f'{context}: UUID is not unique, it names {len(objects_by_uuid[ambiguous[0]])} copper objects; selection is ambiguous: '+', '.join(ambiguous))


def parse_geometry(block):
    geometry={}
    for key,rx in POINT_RE.items():
        m=rx.search(block)
        if m:geometry[key]=[float(m[1]),float(m[2])]
    for key,rx in SCALAR_RE.items():
        m=rx.search(block)
        if m:geometry[key]=float(m[1])
    return geometry


def copper_layers(kind,block):
    if kind=='via':
        m=LAYERS_RE.search(block)
        return re.findall(r'"([^"]+)"',m[1]) if m else []
    m=LAYER_RE.search(block)
    return [m[1]] if m else []


def copper_objects(text):
    """Every top-level copper block in file order, with byte span, digest and parsed fields."""
    out=[]
    for start,end in top_level_spans(text):
        block=text[start:end];kind=KIND_RE.match(block)
        if not kind or kind[1] not in COPPER_KINDS:continue
        uid=UUID_RE.search(block);net=NET_RE.search(block)
        out.append({'kind':kind[1],'uuid':uid[1] if uid else None,'uuid_span':[start+uid.start(1),start+uid.end(1)] if uid else None,
                    'net':net[1] if net else None,'layers':copper_layers(kind[1],block),'geometry':parse_geometry(block),
                    'span':[start,end],'block_sha256':digest(block)})
    return out


def copper_uuid_groups(text):
    """{uuid: [object,...]} over copper_objects(text); a missing UUID groups under None."""
    groups=collections.defaultdict(list)
    for obj in copper_objects(text):groups[obj['uuid']].append(obj)
    return dict(groups)


def duplicate_groups(objects):
    """Sorted duplicate groups; each occurrence carries its index within the group in file order."""
    groups=collections.defaultdict(list)
    for obj in objects:
        if obj['uuid'] is not None:groups[obj['uuid']].append(obj)
    out=[]
    for uid in sorted(groups):
        items=groups[uid]
        if len(items)<2:continue
        out.append({'uuid':uid,'count':len(items),'kinds':sorted({o['kind'] for o in items}),'nets':sorted({o['net'] or '' for o in items}),
                    'occurrences':[{'index':i,**{k:o[k] for k in ('kind','net','layers','geometry','span','block_sha256')}} for i,o in enumerate(items)]})
    return out


def inventory(text,path=None):
    objects=copper_objects(text)
    missing=[o['span'] for o in objects if o['uuid'] is None]
    return {'board':str(path) if path is not None else None,'sha256':digest(text),
            'counts':dict(sorted(collections.Counter(o['kind'] for o in objects).items())),'objects':len(objects),
            'unique_uuids':len({o['uuid'] for o in objects if o['uuid'] is not None}),'missing_uuid_spans':missing,
            'duplicate_groups':duplicate_groups(objects)}


# ---------------------------------------------------------------- allowlist check

def allowlist_entry(board_sha,groups):
    return {'sha256':board_sha,'groups':[{'uuid':g['uuid'],'kinds':g['kinds'],'nets':g['nets'],
            'occurrences':[{'index':o['index'],'kind':o['kind'],'block_sha256':o['block_sha256']} for o in g['occurrences']]} for g in groups]}


def check(text,allowlist,path=None):
    """Violations for every duplicate group not exactly recorded for this board's bytes.

    An allowlisted group matches only when the board sha256, the UUID, the occurrence
    count and the ordered per-occurrence block digests all agree; anything else fails.
    """
    inv=inventory(text,path);board_sha=inv['sha256']
    allowed={}
    for entry in allowlist.get('boards',[]):
        if entry.get('sha256')==board_sha:
            for g in entry.get('groups',[]):allowed[g['uuid']]=g
    violations=[]
    for g in inv['duplicate_groups']:
        ref=allowed.pop(g['uuid'],None)
        actual=[(o['index'],o['kind'],o['block_sha256']) for o in g['occurrences']]
        if ref is None:
            violations.append({'uuid':g['uuid'],'reason':'duplicate copper UUID not in the legacy allowlist for this board sha256','occurrences':actual})
        elif [(o['index'],o['kind'],o['block_sha256']) for o in ref['occurrences']]!=actual:
            violations.append({'uuid':g['uuid'],'reason':'allowlisted duplicate group bytes changed','occurrences':actual})
    for uid in sorted(allowed):
        violations.append({'uuid':uid,'reason':'allowlisted duplicate group is absent from the board','occurrences':[]})
    if inv['missing_uuid_spans']:
        violations.append({'uuid':None,'reason':'copper object without a UUID','occurrences':inv['missing_uuid_spans']})
    return {'board':inv['board'],'sha256':board_sha,'duplicate_groups':len(inv['duplicate_groups']),'violations':violations}


def load_allowlist(path=LEGACY_ALLOWLIST):
    return json.loads(Path(path).read_text())


def canonical_boards():
    import subprocess
    out=subprocess.check_output(['git','ls-files','boards/*/*.kicad_pcb'],cwd=ROOT,text=True)
    return [ROOT/line for line in out.split() if line]


# ---------------------------------------------------------------- removal over text

def drop_copper_blocks(text,removed,context='copper removal'):
    """Text without the copper blocks named in removed; every name must be unique and present."""
    removed=set(removed)
    if not removed:return text
    groups=copper_uuid_groups(text)
    require_unique(groups,removed,context)
    missing=sorted(u for u in removed if u not in groups)
    if missing:raise ValueError(f'{context}: ripped copper not found: {len(removed)-len(missing)}/{len(removed)}; missing '+', '.join(missing))
    edits=[(groups[u][0]['span'][0],groups[u][0]['span'][1],'') for u in removed]
    # Keep the whitespace before each block, as grid_apply.py always did.
    return replace_spans(text,edits)


# ---------------------------------------------------------------- normalization proposal

def derived_uuid(board_sha,old_uuid,index,block_sha):
    return str(uuid.uuid5(NORMALIZATION_NAMESPACE,f'{board_sha}\0{old_uuid}\0{index}\0{block_sha}'))


def all_uuid_tokens(text):
    return collections.Counter(m[1] for m in UUID_RE.finditer(text))


def propose_normalization(text,path=None):
    """Rename every occurrence after the first in each duplicate group; return (manifest, proposed text).

    The first occurrence in file order keeps its UUID so that existing references
    (receipts, replay deltas, reviewed cut plans) to a legacy ID still resolve to one
    object. Later occurrences receive a UUIDv5 derived from the board sha256, the old
    UUID, the occurrence index and the block digest, so two runs are byte-identical and
    a proposal made for other bytes cannot be applied.
    """
    board_sha=digest(text);groups=duplicate_groups(copper_objects(text))
    taken=all_uuid_tokens(text);renames=[];edits=[]
    for g in groups:
        for occ in g['occurrences'][1:]:
            start,end=occ['span'];block=text[start:end];m=UUID_RE.search(block)
            new=derived_uuid(board_sha,g['uuid'],occ['index'],occ['block_sha256'])
            if taken.get(new):raise ValueError('derived UUID collides with an existing token: '+new)
            taken[new]=1
            uuid_span=[start+m.start(1),start+m.end(1)]
            renames.append({'old_uuid':g['uuid'],'occurrence_index':occ['index'],'kind':occ['kind'],'net':occ['net'],'layers':occ['layers'],
                            'geometry':occ['geometry'],'block_sha256':occ['block_sha256'],'span':occ['span'],'uuid_span':uuid_span,'new_uuid':new})
            edits.append((uuid_span[0],uuid_span[1],new))
    output=replace_spans(text,edits)
    manifest={'schema':MANIFEST_SCHEMA,'board':str(path) if path is not None else None,'input_board_sha256':board_sha,
              'output_board_sha256':digest(output),'policy':'first occurrence in file order keeps its UUID; every later occurrence is renamed',
              'derivation':f'uuid5({NORMALIZATION_NAMESPACE}, input_board_sha256\\0old_uuid\\0occurrence_index\\0block_sha256)',
              'duplicate_groups':len(groups),'renames':renames}
    return manifest,output


def apply_manifest(text,manifest):
    """Proposal text rebuilt from the input and the manifest; refuses stale or tampered manifests."""
    if manifest.get('schema')!=MANIFEST_SCHEMA:raise ValueError('unsupported normalization manifest schema')
    board_sha=digest(text)
    if manifest.get('input_board_sha256')!=board_sha:raise ValueError('normalization manifest was made for a different board')
    edits=[];seen=set()
    for r in manifest['renames']:
        start,end=r['span'];block=text[start:end]
        if digest(block)!=r['block_sha256']:raise ValueError(f"normalization manifest block digest mismatch at {start}")
        us,ue=r['uuid_span']
        if not (start<=us<ue<=end) or text[us:ue]!=r['old_uuid']:raise ValueError(f'normalization manifest UUID token mismatch at {us}')
        if r['new_uuid'] in seen or not UUID_RE.fullmatch(f'(uuid "{r["new_uuid"]}")'):raise ValueError('normalization manifest new UUID invalid or repeated')
        seen.add(r['new_uuid']);edits.append((us,ue,r['new_uuid']))
    output=replace_spans(text,edits)
    if digest(output)!=manifest.get('output_board_sha256'):raise ValueError('normalization manifest output digest mismatch')
    return output


def verify_normalization(input_text,output_text,manifest):
    """Proof that output differs from input only by the manifest's UUID tokens and keeps every object."""
    rebuilt=apply_manifest(input_text,manifest)
    if board_bytes(rebuilt)!=board_bytes(output_text):raise ValueError('proposal bytes differ from input plus manifest renames')
    before,after=copper_objects(input_text),copper_objects(output_text)
    if len(before)!=len(after):raise ValueError('normalization changed the copper object count')
    strip=lambda o,t:t[o['span'][0]:o['uuid_span'][0]]+t[o['uuid_span'][1]:o['span'][1]] if o['uuid_span'] else t[o['span'][0]:o['span'][1]]
    if collections.Counter(strip(o,input_text) for o in before)!=collections.Counter(strip(o,output_text) for o in after):
        raise ValueError('normalization changed copper geometry outside the UUID tokens')
    renamed={r['new_uuid'] for r in manifest['renames']}
    remaining=duplicate_groups(after)
    if any(g['uuid'] in renamed for g in remaining):raise ValueError('a renamed UUID is still duplicated')
    old_tokens,new_tokens=all_uuid_tokens(input_text),all_uuid_tokens(output_text)
    for r in manifest['renames']:
        if new_tokens.get(r['new_uuid'])!=1 or old_tokens.get(r['new_uuid']):raise ValueError('new UUID token count is not exactly one: '+r['new_uuid'])
    return {'input_board_sha256':digest(input_text),'output_board_sha256':digest(output_text),'renames':len(manifest['renames']),
            'objects':len(before),'counts':dict(sorted(collections.Counter(o['kind'] for o in before).items())),
            'duplicate_groups_before':len(duplicate_groups(before)),'duplicate_groups_after':len(remaining),
            'differing_bytes':sum(a!=b for a,b in zip(board_bytes(input_text),board_bytes(output_text))),
            'renamed_token_bytes':sum(sum(a!=b for a,b in zip(r['old_uuid'].encode(),r['new_uuid'].encode())) for r in manifest['renames'])}


# ---------------------------------------------------------------- CLI

def dumps(value):
    return json.dumps(value,indent=1,sort_keys=True)+'\n'


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);sub=p.add_subparsers(dest='cmd',required=True)
    i=sub.add_parser('inventory',help='every copper object class count and every duplicate UUID group, as JSON')
    i.add_argument('boards',nargs='+',type=Path);i.add_argument('-o','--output',type=Path)
    c=sub.add_parser('check',help='exit 1 on any duplicate copper UUID not exactly allowlisted for the board bytes')
    c.add_argument('boards',nargs='*',type=Path,help='default: every tracked boards/*/*.kicad_pcb');c.add_argument('--allowlist',type=Path,default=LEGACY_ALLOWLIST)
    c.add_argument('--record',type=Path,help='write an allowlist entry file for the current duplicates instead of judging them')
    n=sub.add_parser('propose-normalization',help='dry-run rename of later duplicate occurrences into --out; never writes boards/')
    n.add_argument('board',type=Path);n.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('apply-manifest',help='rebuild a proposal from a board and its manifest into --out');a.add_argument('board',type=Path)
    a.add_argument('manifest',type=Path);a.add_argument('--out',type=Path,required=True)
    v=sub.add_parser('verify',help='prove a proposal equals input plus manifest renames');v.add_argument('board',type=Path)
    v.add_argument('proposal',type=Path);v.add_argument('manifest',type=Path)
    args=p.parse_args(argv)
    if args.cmd=='inventory':
        out=[inventory(load_board_text(b),rel(b)) for b in args.boards]
        text=dumps(out if len(out)>1 else out[0])
        if args.output:args.output.write_text(text)
        else:sys.stdout.write(text)
        return 0
    if args.cmd=='check':
        boards=args.boards or canonical_boards()
        if args.record:
            inventories=[inventory(load_board_text(b),rel(b)) for b in boards]
            entries=[{'path':i['board'],**allowlist_entry(i['sha256'],i['duplicate_groups'])} for i in inventories if i['duplicate_groups']]
            args.record.write_text(dumps({'purpose':'exact legacy duplicate copper UUID groups tolerated only while byte-identical; see scripts/pcbgen/README.md "Copper identity"',
                                          'boards':entries}))
            print('recorded',len(entries),'board entries to',args.record);return 0
        allowlist=load_allowlist(args.allowlist)
        results=[check(load_board_text(b),allowlist,rel(b)) for b in boards]
        bad=[r for r in results if r['violations']]
        for r in results:print(f"{r['board']}: {r['duplicate_groups']} duplicate groups, {len(r['violations'])} violations")
        if bad:sys.stdout.write(dumps(bad));return 1
        return 0
    if args.cmd=='propose-normalization':
        refuse_boards_dir(args.out);text=load_board_text(args.board);manifest,output=propose_normalization(text,rel(args.board))
        args.out.mkdir(parents=True,exist_ok=True);proof=verify_normalization(text,output,manifest)
        (args.out/'manifest.json').write_text(dumps(manifest));(args.out/args.board.name).write_bytes(board_bytes(output))
        (args.out/'proof.json').write_text(dumps(proof))
        print(f"{len(manifest['renames'])} renames proposed for {manifest['duplicate_groups']} duplicate groups; wrote {args.out}");return 0
    if args.cmd=='apply-manifest':
        refuse_boards_dir(args.out.parent);text=load_board_text(args.board);manifest=json.loads(args.manifest.read_text())
        output=apply_manifest(text,manifest);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(board_bytes(output))
        print('wrote',args.out);return 0
    if args.cmd=='verify':
        proof=verify_normalization(load_board_text(args.board),load_board_text(args.proposal),json.loads(args.manifest.read_text()))
        sys.stdout.write(dumps(proof));return 0
    return 2


def rel(path):
    path=Path(path).resolve()
    try:return str(path.relative_to(ROOT))
    except ValueError:return str(path)


def refuse_boards_dir(path):
    if (ROOT/'boards') in Path(path).resolve().parents or Path(path).resolve()==ROOT/'boards':
        raise SystemExit('refusing to write a proposal under boards/; canonical boards change only in a reviewed migration')


if __name__=='__main__':sys.exit(main())
