"""Deterministic KiCad UUIDs for generator-owned board items only."""
from __future__ import annotations
import re
import uuid
from pathlib import Path

NAMESPACE=uuid.UUID('c67dff75-aa94-4ed4-8e31-31f2e6948ccf')
UUID_RE=re.compile(r'\(uuid\s+"([0-9a-fA-F-]{36})"\)')
REF_RE=re.compile(r'\(property\s+"Reference"\s+"([^"]+)"')
PAD_RE=re.compile(r'\(pad\s+"([^"]*)"')

def replace_spans(text: str, edits: list[tuple[int,int,str]]) -> str:
    """Apply nonoverlapping source-coordinate edits in one pass."""
    chunks=[];cursor=0
    for start,end,value in sorted(edits):
        if start<cursor:raise ValueError('overlapping board normalization edits')
        chunks.extend((text[cursor:start],value));cursor=end
    chunks.append(text[cursor:])
    return ''.join(chunks)

def stable_uuid(board_id: str, kind: str, key: str) -> str:
    if not board_id or not kind or not key:raise ValueError('UUID key fields must be nonempty')
    return str(uuid.uuid5(NAMESPACE,f'{board_id}\0{kind}\0{key}'))

def top_level_spans(text: str):
    """Yield direct child S-expression spans without treating quoted parentheses as syntax."""
    depth=0;quoted=False;escaped=False;start=None
    for i,c in enumerate(text):
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
            continue
        if c=='"':quoted=True;continue
        if c=='(':
            if depth==1:start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth<0:raise ValueError('unbalanced board S-expression')
            if depth==1 and start is not None:
                yield start,i+1;start=None
    if quoted or depth!=0:raise ValueError('unbalanced board S-expression')

def normalize(text: str, board_id: str, owned_refs: set[str], new_ids: dict[str,str], created: bool, owned_zone_ids: set[str]|None=None) -> str:
    # KiCad's PAGE_INFO binding is not exposed as a mutable Python value.
    # The board author owns the sheet declaration and fixes it in the postpass.
    text,n=re.subn(r'\(paper\s+"[^"]+"\)', '(paper "A2")', text, count=1)
    if n!=1:raise ValueError('board paper declaration missing')
    edits=[]
    if created:
        # KiCad 10 boards may omit a board-level UUID. Never substitute the
        # first footprint UUID for it; inspect only direct board children.
        board_uuid=next(((a,b) for a,b in top_level_spans(text) if text[a:b].startswith('(uuid ')),None)
        if board_uuid is not None:
            a,b=board_uuid
            m=UUID_RE.search(text,a,b)
            if m:edits.append((m.start(1),m.end(1),stable_uuid(board_id,'board','root')))
    for start,end in top_level_spans(text):
        block=text[start:end]
        kind=re.match(r'\(([A-Za-z0-9_]+)',block)
        if not kind:continue
        if kind[1]=='footprint':
            ref=REF_RE.search(block)
            if not ref or ref[1] not in owned_refs:continue
            pad_ids={};pad_ranks={}
            for child_start,child_end in top_level_spans(block):
                child=block[child_start:child_end]
                pad=PAD_RE.match(child)
                if not pad:continue
                match=UUID_RE.search(child)
                if match:
                    rank=pad_ranks.get(pad[1],0);pad_ranks[pad[1]]=rank+1
                    pad_ids[child_start+match.start(1)]=f'pad:{pad[1]}:{rank}'
            nonpad=0
            for n,m in enumerate(UUID_RE.finditer(block)):
                if n==0:key='root'
                elif m.start(1) in pad_ids:key=pad_ids[m.start(1)]
                else:
                    nonpad+=1;key=f'child:{nonpad}'
                edits.append((start+m.start(1),start+m.end(1),stable_uuid(board_id,'footprint:'+ref[1],key)))
        else:
            m=UUID_RE.search(block)
            if m and m[1] in new_ids:
                edits.append((start+m.start(1),start+m.end(1),new_ids[m[1]]))
    text=replace_spans(text,edits)
    # pcbnew's footprint container iteration is not stable across process runs.
    # Sort only managed footprint blocks; preserve the bytes of each unowned block.
    slots=[]
    for a,b in top_level_spans(text):
        block=text[a:b]
        if block.startswith('(footprint'):
            m=REF_RE.search(block)
            if m and m[1] in owned_refs:slots.append((a,b,m[1],block))
    ordered=sorted(slots,key=lambda x:x[2])
    text=replace_spans(text,[(a,b,source[3]) for (a,b,_,_),source in zip(slots,ordered)])
    if owned_zone_ids:
        slots=[]
        for a,b in top_level_spans(text):
            block=text[a:b]
            if block.startswith('(zone'):
                m=UUID_RE.search(block)
                if m and m[1] in owned_zone_ids:slots.append((a,b,m[1],block))
        ordered=sorted(slots,key=lambda x:x[2])
        text=replace_spans(text,[(a,b,source[3]) for (a,b,_,_),source in zip(slots,ordered)])
    return text

def normalize_file(path: Path, board_id: str, owned_refs: set[str], new_ids: dict[str,str], created: bool, owned_zone_ids: set[str]|None=None):
    text=path.read_text();updated=normalize(text,board_id,owned_refs,new_ids,created,owned_zone_ids)
    if updated!=text:path.write_text(updated)
