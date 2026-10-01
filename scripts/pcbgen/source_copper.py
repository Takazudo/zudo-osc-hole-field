"""Retire only explicitly listed, UUID-verified obsolete generated copper."""
import hashlib
from scripts.pcbgen.uuid_tools import stable_uuid,top_level_spans,UUID_RE


def retire_vias(text,board_id,spec):
    rows=spec['boards'][board_id]
    expected={r['uuid']:r for r in rows}
    if len(expected)!=len(rows):raise ValueError('duplicate source via retirement')
    found=set();removals=[]
    for start,end in top_level_spans(text):
        block=text[start:end]
        if not block.startswith('(via'):continue
        match=UUID_RE.search(block)
        if not match or match[1] not in expected:continue
        row=expected[match[1]]
        if stable_uuid(board_id,row['generator_kind'],row['generator_key'])!=row['uuid']:
            raise ValueError('retired via is not owned by its declared source generator')
        if hashlib.sha256(block.encode()).hexdigest()!=row['serialized_via_sha256']:
            raise ValueError('retired generated via differs from its reviewed source bytes')
        found.add(row['uuid']);removals.append((start,end))
    if found!=set(expected):raise ValueError('declared obsolete source via is missing')
    for start,end in reversed(removals):text=text[:start]+text[end:]
    return text,rows
