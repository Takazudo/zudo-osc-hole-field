"""Exact pinned editor metadata for a newly source-owned two-foil stack.

These four KiCad defaults are serialization labels, not material/finish facts.
No physical band or other setup field is inferred or accepted from readback.
"""
import hashlib
import json
from scripts.pcbgen.native_stack import stack_block
from scripts.pcbgen.uuid_tools import top_level_spans


def setup_and_stack(text):
    setups=[(a,b) for a,b in top_level_spans(text) if text[a:b].startswith('(setup')]
    if len(setups)!=1:raise ValueError('one source native setup required')
    a,b=setups[0];setup=text[a:b]
    stacks=[(x,y) for x,y in top_level_spans(setup) if setup[x:y].startswith('(stackup')]
    if len(stacks)!=1:raise ValueError('one source native stack required')
    x,y=stacks[0]
    return (a,b),setup,(a+x,a+y),setup[x:y]


def serialize(text,definition_bytes):
    definition=json.loads(definition_bytes)
    if definition['layers']!=2:raise ValueError('peripheral serializer requires two physical foils')
    _,_,(a,b),old=setup_and_stack(text)
    expected=stack_block(definition).replace('\n','\n\t\t')
    if old!=expected:raise ValueError('input stack differs from exact source dielectric/material/dimensions')
    children=[(x,y) for x,y in top_level_spans(old) if old[x:y].startswith('(layer "dielectric 1"')]
    if len(children)!=1:raise ValueError('one source dielectric band required')
    x,y=children[0];child=old[x:y];ending='\n\t\t\t)'
    if not child.endswith(ending) or not old.endswith('\n\t\t)'):
        raise ValueError('unexpected source stack formatting')
    revised=child[:-len(ending)]+'\n\t\t\t\t(epsilon_r 4.5)\n\t\t\t\t(loss_tangent 0.02)'+ending
    new=old[:x]+revised+old[y:]
    new=new[:-len('\n\t\t)')]+'\n\t\t\t(copper_finish "None")\n\t\t\t(dielectric_constraints no)\n\t\t)'
    result=text[:a]+new+text[b:];sha=lambda raw:hashlib.sha256(raw).hexdigest()
    return result,{'status':'Pinned native editor serialization only; NOT material/finish evidence',
        'definition_sha256':sha(definition_bytes),'before_board_sha256':sha(text.encode()),
        'after_board_sha256':sha(result.encode()),'before_stack_sha256':sha(old.encode()),'after_stack_sha256':sha(new.encode()),
        'added_editor_defaults':{'epsilon_r':4.5,'loss_tangent':.02,'copper_finish':'None','dielectric_constraints':'no'},
        'physical_stack_and_all_other_bytes_unchanged':True}


def verify(before,after,definition_bytes):
    expected,receipt=serialize(before,definition_bytes)
    if after!=expected:raise ValueError('native serialization changed an undeclared stack/setup/board value')
    return receipt
