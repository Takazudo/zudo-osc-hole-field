"""Independent read-only reconciliation of full paired native batch artifacts.

This module is not called by the acceptance gate; that gate rejects this format
until separate integration and regression validation are complete.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata,zone_fixture_parts,zone_fixture_batch_text,artwork_batches
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting,new_silk_identities
from scripts.pcbgen.complete_native_warnings import SILK_TARGET_LAYERS
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE

BEFORE='95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5'
AFTER='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def validate_coverage(pairs):
    size=pairs['artwork_batch_size'];selected=pairs['selected_item_uuids']
    if type(size) is not int or not 2<=size<=16:
        raise ValueError('unsupported batch size')
    if not isinstance(selected,list) or any(not isinstance(x,str) or not x for x in selected):
        raise ValueError('invalid selected artwork')
    batches=artwork_batches(selected,size)
    expected=[(stage,index,ids) for stage in (0,1) for index,ids in enumerate(batches)]
    actual=[]
    for f in pairs['fixtures']:
        if type(f['stage']) is not int or type(f['batch_index']) is not int:
            raise ValueError('invalid stage/batch index')
        actual.append((f['stage'],f['batch_index'],f['item_uuids']))
    if actual!=expected:
        raise ValueError('incomplete, duplicate or reordered paired batch coverage')
    return expected


def artwork_ids(text):
    ids=[]
    for a,b in top_level_spans(text):
        block=text[a:b];kind=block[1:].split(None,1)[0].rstrip(')')
        if kind=='footprint' or ((kind.startswith('gr_') or kind in ('dimension','image')) and not re.search(r'\(layer "Edge.Cuts"\)',block)):
            match=UUID_RE.search(block)
            if not match:raise ValueError('artwork UUID missing')
            ids.append(match[1])
    if len(set(ids))!=len(ids):raise ValueError('ambiguous artwork identity')
    return set(ids)


def normalized(rows):
    result={(a,b,tuple(c)) for a,b,c in rows}
    if len(result)!=len(rows):raise ValueError('duplicate receipt identity')
    return result


def main(archive,digest,before,after,output):
    if SHA(archive.read_bytes())!=digest or SHA(before.read_bytes())!=BEFORE or SHA(after.read_bytes())!=AFTER:
        raise ValueError('immutable archive/source mismatch')
    sources=[before,after];texts=[p.read_text() for p in sources]
    if zone_metadata(texts[0])!=zone_metadata(texts[1]):raise ValueError('zone metadata changed')
    unchanged_nonrouting(*texts)
    art=[artwork_ids(t) for t in texts]
    if art[0]!=art[1]:raise ValueError('artwork scope changed')
    context={suffix:before.with_suffix(suffix).read_bytes() for suffix in ('.kicad_pro','.kicad_dru')}
    if any(after.with_suffix(s).read_bytes()!=b for s,b in context.items()):raise ValueError('source context changed')
    rules=json.loads(context['.kicad_pro'])['board']['design_settings']['rules']
    margin=max(0,math.ceil(rules['min_silk_clearance']*1e6))+5_000_000
    expected_zones=set()
    for a,b in top_level_spans(texts[1]):
        block=texts[1][a:b]
        if not block.startswith('(zone') or re.search(r'\(keepout\s',block):continue
        layers=re.search(r'\(layers?\s+([^)]*)\)',block)
        if not layers:raise ValueError('zone layer missing')
        expected_zones.update((UUID_RE.search(block)[1],layer) for layer in re.findall(r'"([^"]+)"',layers[1]) if layer in SILK_TARGET_LAYERS)
    with zipfile.ZipFile(archive) as z:
        names=[n for n in z.namelist() if n.endswith('/result.json') and 'paired-zone-batches/' in n]
        if len(names)!=1:raise ValueError('missing/ambiguous result')
        prefix=names[0][:-len('result.json')];read=lambda n:json.loads(z.read(prefix+n))
        result=read('result.json')
        if (result['version']!='10.0.6' or result['before_sha256']!=BEFORE or result['after_sha256']!=AFTER
                or not result.get('zone_silk_scope_complete')):raise ValueError('native source/version/coverage incomplete')
        rows=result['zones']
        if len(rows)!=len(expected_zones) or {(r['uuid'],r['layer']) for r in rows}!=expected_zones:
            raise ValueError('zone layer coverage incomplete')
        all_new=set();counts=[]
        for row in rows:
            if row['native_added_shape_empty']:
                if row['native_added_area_nm2']!=0 or row['native_added_outline_count']!=0:raise ValueError('inconsistent empty growth')
                counts.append(dict(uuid=row['uuid'],layer=row['layer'],subset=True,fixtures=0));continue
            uid=row['uuid'];pairs=row['native_silk_pairs'];coverage=validate_coverage(pairs)
            selected=pairs['selected_item_uuids']
            if selected!=sorted(selected) or not set(selected)<=art[1]:raise ValueError('unbound selected artwork')
            scope=read(f'zone-{uid}-scope.json')
            if (scope['zone_uuid']!=uid or scope['layer']!=row['layer'] or scope['selected_item_uuids']!=selected
                    or scope['artwork_count']!=len(art[1]) or scope['conservative_margin_nm']!=margin
                    or pairs['conservative_margin_nm']!=margin):raise ValueError('native scope receipt mismatch')
            boxes=scope['growth_boxes_nm']
            if len(boxes)!=row['native_added_outline_count'] or any(len(b)!=4 or any(type(v) is not int for v in b) or min(b[2:])<=0 for b in boxes):
                raise ValueError('native growth box receipt invalid')
            geometry=pairs['source_geometry_sha256']
            if (pairs['native_geometry_method']!='exact_native_coordinates_no_arcs' or set(geometry)!={'0','1'}
                    or any(not re.fullmatch('[0-9a-f]{64}',v) for v in geometry.values())):raise ValueError('invalid geometry signatures')
            parts=[zone_fixture_parts(t,uid,ids) for t,ids in zip(texts,art)]
            unions=[set(),set()]
            for f,(stage,index,ids) in zip(pairs['fixtures'],coverage):
                folder=f'zone-{uid}/{stage}-batch-{index:04d}/'
                pcb=z.read(prefix+folder+sources[stage].name)
                if pcb!=zone_fixture_batch_text(parts[stage],ids).encode() or SHA(pcb)!=f['fixture_sha256']:
                    raise ValueError('fixture differs from exact source artwork/zone bytes')
                if f['native_geometry_sha256']!=geometry[str(stage)]:raise ValueError('fixture geometry signature mismatch')
                for suffix,data in context.items():
                    if z.read(prefix+folder+sources[stage].stem+suffix)!=data:raise ValueError('fixture native context changed')
                report=z.read(prefix+folder+'drc.json')
                if SHA(report)!=f['report_sha256']:raise ValueError('report hash mismatch')
                raw=json.loads(report)
                if raw.get('kicad_version')!='10.0.6' or set(raw.get('included_severities',[]))!={'error','warning','exclusion'}:
                    raise ValueError('native version/severity scope mismatch')
                actual={(r['type'],r['severity'],tuple(sorted(i['uuid'] for i in r['items']))) for r in new_silk_identities(raw,uid)}
                if actual!=normalized(f['identities']):raise ValueError('receipt differs from raw native observations')
                unions[stage].update(actual)
            if unions[0]!=normalized(pairs['before_identities']) or unions[1]!=normalized(pairs['after_identities']):raise ValueError('incomplete identity union')
            new=unions[1]-unions[0]
            if new!=normalized(pairs['new_identities']):raise ValueError('identity delta mismatch')
            all_new.update(new)
            counts.append(dict(uuid=uid,layer=row['layer'],selected_items=len(selected),fixtures=len(coverage),before_identities=len(unions[0]),after_identities=len(unions[1])))
        if all_new!=normalized(result['new_zone_silk_identities']):raise ValueError('incomplete final identity union')
        receipt=dict(status='COMPLETE PAIRED BATCH ARTIFACT RECONCILED; NOT ACCEPTED OR ADOPTED',
            artifact_sha256=digest,before_sha256=BEFORE,after_sha256=AFTER,version='10.0.6',zones=counts,
            new_zone_silk_identities=sorted(all_new),full_paired_zone_coverage=True,
            acceptance_integration='NOT IMPLEMENTED; gate rejects batch receipts',adopted=False)
        output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('archive','before','after','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--sha256',required=True)
    args=parser.parse_args();main(args.archive,args.sha256,args.before,args.after,args.output)
