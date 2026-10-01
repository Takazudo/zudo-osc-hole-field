"""Source-owned exact white LED pad revision in an existing native text epoch.

This does not run native checks or preserve validity of historical receipts.
Every other byte, including pad UUID/net and package/body/copper/style, remains.
"""
import hashlib
import re
from scripts.pcbgen.uuid_tools import top_level_spans, UUID_RE
from scripts.libgen.gen_kingbright_land import derive


def digest(text):return hashlib.sha256(text.encode()).hexdigest()


def refresh(text, board_id, partition, io, spec, original_library):
    # Validate the same primary/source geometry contract as the library generator.
    derive(original_library,spec)
    boards=[x for x in partition['boards'] if x['id']==board_id]
    if len(boards)!=1:raise ValueError('one exact source board required')
    key=boards[0]['board_key'];assignment={x['ref']:x['board'] for x in partition['assignment']['components']}
    if len(assignment)!=len(partition['assignment']['components']):raise ValueError('duplicate source package')
    expected={p['ref'] for p in io['physical_packages'] if not p['dnp'] and p['footprint']=='zudo-osc-hole-field:LED0402-Kingbright-White' and assignment.get(p['ref'])==key}
    if len(expected)!={'JL':41,'JR':51,'EL':12}.get(key):raise ValueError('source white LED scope changed')
    edits=[];rows=[];seen=set();p=spec['project_mm']
    for start,end in top_level_spans(text):
        block=text[start:end]
        if not block.startswith('(footprint'):continue
        ref=re.search(r'\(property "Reference" "([^"]+)"',block)
        if not ref:raise ValueError('native footprint reference missing')
        ref=ref[1]
        white=bool(re.match(r'\(footprint "zudo-osc-hole-field:LED0402-Kingbright-White"',block))
        if (ref in expected)!=white:raise ValueError('white native/source footprint identity mismatch: '+ref)
        if not white:continue
        if ref in seen:raise ValueError('duplicate white native footprint')
        seen.add(ref);pad_edits=[];pads=[]
        for a,b in top_level_spans(block):
            pad=block[a:b]
            if not pad.startswith('(pad'):continue
            match=re.match(r'\(pad "([12])" smd rect\s',pad)
            if not match:raise ValueError('unexpected white native pad')
            pin=match[1];sign='-' if pin=='1' else ''
            at=f'(at {sign}0.45 0)';size='(size 0.7 0.5)'
            if pad.count(at)!=1 or pad.count(size)!=1:raise ValueError('white pad differs from exact old geometry: '+ref+':'+pin)
            if not re.search(r'\(net "[^"]+"\)',pad) or not UUID_RE.search(pad):raise ValueError('white pad net or UUID missing')
            changed=pad.replace(at,f'(at {sign}{p["centre_x_magnitude"]:g} 0)').replace(size,f'(size {p["width"]:g} 0.5)')
            pad_edits.append((a,b,changed));pads.append({'pad':pin,'uuid':UUID_RE.search(pad)[1],'old_block_sha256':digest(pad),'new_block_sha256':digest(changed)})
        if sorted(x['pad'] for x in pads)!=['1','2']:raise ValueError('white pad pair missing/duplicate')
        changed=block
        for a,b,value in reversed(pad_edits):changed=changed[:a]+value+changed[b:]
        rows.append({'ref':ref,'footprint_uuid':UUID_RE.search(block)[1],'old_block_sha256':digest(block),'new_block_sha256':digest(changed),'pads':pads})
        edits.append((start,end,changed))
    if seen!=expected:raise ValueError('missing source white footprint')
    result=text
    for a,b,value in reversed(edits):result=result[:a]+value+result[b:]
    return result,{'board_id':board_id,'before_sha256':digest(text),'after_sha256':digest(result),'footprints':rows,
                   'scope':'Only exact old white pad at/size fields derived from source; all other bytes retained. Fresh native clearance, connected-pad and source gates required; historical receipts not rebound.'}
