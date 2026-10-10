#!/usr/bin/env python3
"""Sharded hotspot-region routing: plan disjoint net shards, extract copper deltas, merge them.

Every shard starts from the same base board and renegotiates only the signal nets
it owns, so the deltas never touch the same net. Each delta is the set of
segment/via blocks the shard removed and added. The merge applies all deltas to
the base board as text, runs settled and independent native gates, and reverts
whole nets whose new copper still fails, as a route_jack_grid.py stage does.
Draft only: electrical and physical qualification remain NOT RUN.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE
from scripts.pcbgen.copper_identity import reject_new_uuid_collisions

NET_RE=re.compile(r'\(net\s+"((?:[^"\\]|\\.)*)"\)')
LAYER_RE=re.compile(r'\(layer\s+"([^"]+)"\)')


def region_key(region):
    """The rounded lower corner that route_jack_grid.py uses to mark a region as tried."""
    return tuple(round(float(v)/1e6) for v in region[0])


def region_nets(dump,nets,region,margin_mm):
    """Signal nets (from nets) with copper or a stranded pin inside one region box plus margin."""
    lo,hi=region[0],region[1];m=margin_mm*1e6
    inside=lambda xy:lo[0]-m<=xy[0]<=hi[0]+m and lo[1]-m<=xy[1]<=hi[1]+m
    nets=set(nets)
    chosen={i['net'] for i in dump['tracks'] if i['net'] in nets and (inside(i['a']) or inside(i['b']))}
    chosen|={i['net'] for i in dump['vias'] if i['net'] in nets and inside(i['xy'])}
    chosen|={p['net'] for p in dump['pads'] if p['net'] in nets and len(dump['islands'].get(p['net'],[]))>1 and inside(p['xy'])}
    return chosen


def plan(regions,nets_of,shards,margin=0):
    """Split regions over shards and give every net to exactly one shard.

    regions: [(lo, hi, stranded_pins)] largest first; nets_of: one net set per region.
    Regions whose boxes overlap once grown by margin (board units) stay in one shard,
    so two shards rarely rip copper in the same window, unless joining them would
    exceed an even share of the stranded pins (dense boards otherwise chain most
    regions into one group; the merge gate reverts any clash). Groups go greedily, by
    stranded pins, to the least-loaded shard. A net seen by several shards belongs to
    the one whose regions hold it most often (ties to the lower shard), so other
    shards keep that net's copper as a fixed obstacle.
    """
    parent=list(range(len(regions)));weight=[int(r[2]) for r in regions]
    cap=-(-sum(weight)//shards)
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,a in enumerate(regions):
        for j in range(i):
            b=regions[j];ri,rj=root(i),root(j)
            if ri==rj or weight[ri]+weight[rj]>cap:continue
            if all(a[0][k]-margin<=b[1][k]+margin and b[0][k]-margin<=a[1][k]+margin for k in (0,1)):parent[ri]=rj;weight[rj]+=weight[ri]
    groups={}
    for i in range(len(regions)):groups.setdefault(root(i),[]).append(i)
    load=[0]*shards;owner=[0]*len(regions)
    for members in sorted(groups.values(),key=lambda g:(-sum(int(regions[i][2]) for i in g),g[0])):
        s=min(range(shards),key=lambda k:(load[k],k));load[s]+=sum(int(regions[i][2]) for i in members)
        for i in members:owner[i]=s
    votes={}
    for s,ns in zip(owner,nets_of):
        for n in ns:votes.setdefault(n,[0]*shards)[s]+=1
    net_owner={n:max(range(shards),key=lambda k:(v[k],-k)) for n,v in votes.items()}
    out=[]
    for k in range(shards):
        mine=[(r,ns) for r,ns,s in zip(regions,nets_of,owner) if s==k]
        out.append({'regions':[[[float(v) for v in r[0]],[float(v) for v in r[1]],int(r[2])] for r,_ in mine],
                    'region_nets':[sorted(n for n in ns if net_owner[n]==k) for _,ns in mine],
                    'nets':sorted(n for n,s in net_owner.items() if s==k),'stranded_pins':load[k]})
    return out


def area_plan(points,shards):
    """Split nets into shards by board area: recursive bisection of net centroids.

    points: {net: (x, y, open_edges)}. Each cut runs across the longer side of the
    current box at the open-edge-weighted position that gives each half its share of
    shards; closed nets follow their position, so the nets a shard may rip up are the
    ones around its open nets. Returns one sorted net list per shard.
    """
    def split(nets,n):
        if n==1 or len(nets)<2:return [sorted(nets)]+[[] for _ in range(n-1)]
        xs=[points[m][0] for m in nets];ys=[points[m][1] for m in nets]
        axis=0 if max(xs)-min(xs)>=max(ys)-min(ys) else 1
        order=sorted(nets,key=lambda m:(points[m][axis],points[m][1-axis],m))
        left=n//2;total=sum(points[m][2] for m in order)
        if total:
            target=total*left/n;run=0;cut=len(order)
            for i,m in enumerate(order):
                run+=points[m][2]
                if run>=target:cut=i+1;break
        else:cut=len(order)*left//n
        cut=min(max(cut,1),len(order)-1)
        return split(order[:cut],left)+split(order[cut:],n-left)
    return split(sorted(points),shards)


def copper_block_groups(text):
    """Keep every block even when legacy copper shares a UUID."""
    out=collections.defaultdict(list)
    for start,end in top_level_spans(text):
        block=text[start:end]
        if not block.startswith(('(segment','(via')):continue
        uid=UUID_RE.search(block);net=NET_RE.search(block)
        if not uid or not net:raise ValueError('copper item without uuid or net: '+block[:80])
        layer=LAYER_RE.search(block) if block.startswith('(segment') else None
        out[uid[1]].append((net[1],layer[1] if layer else None,block))
    return dict(out)


def copper_blocks(text):
    """Unique-ID view; use copper_block_groups when comparing complete geometry."""
    return {u:items[-1] for u,items in copper_block_groups(text).items()}


def delta(base_text,final_text):
    """Copper removed from and added to base_text by one shard, with the nets it touched."""
    bg,fg=copper_block_groups(base_text),copper_block_groups(final_text)
    ambiguous={u for u in bg.keys()|fg.keys() if len(bg.get(u,[]))>1 or len(fg.get(u,[]))>1}
    for u in ambiguous:
        if sorted(x[2] for x in bg.get(u,[]))!=sorted(x[2] for x in fg.get(u,[])):
            raise ValueError('ambiguous duplicate copper UUID changed: '+u)
    # Unchanged duplicates remain byte-for-byte in the base; never select one
    # arbitrary object as the representative of a removal or modification.
    base={u:v[-1] for u,v in bg.items() if u not in ambiguous}
    final={u:v[-1] for u,v in fg.items() if u not in ambiguous}
    removed=sorted(set(base)-set(final));added=sorted(set(final)-set(base))
    changed=sorted(u for u in set(base)&set(final) if base[u][2]!=final[u][2])
    if changed:raise ValueError(f'shard edited {len(changed)} copper items in place; only removal and addition are mergeable')
    return {'base_sha256':hashlib.sha256(base_text.encode()).hexdigest(),
            'removed':[{'uuid':u,'net':base[u][0]} for u in removed],
            'added':[{'uuid':u,'net':final[u][0],'layer':final[u][1],'block':final[u][2]} for u in added],
            'nets':sorted({base[u][0] for u in removed}|{final[u][0] for u in added})}


def disjoint(deltas):
    """Nets each delta keeps: a net already claimed by an earlier delta is dropped from a later one."""
    seen=set();keep=[]
    for d in deltas:
        mine=set(d['nets'])-seen;keep.append(mine);seen|=mine
    return keep


def merge_text(base_text,deltas,reverted=frozenset()):
    """Base board with every delta applied, except for disjoint-check losers and reverted nets."""
    keep=disjoint(deltas)
    removed={r['uuid'] for d,k in zip(deltas,keep) for r in d['removed'] if r['net'] in k and r['net'] not in reverted}
    added_rows=[a for d,k in zip(deltas,keep) for a in d['added'] if a['net'] in k and a['net'] not in reverted]
    added=[a['block'] for a in added_rows];surviving=set()
    chunks=[];last=0;spans=list(top_level_spans(base_text));dropped=0
    for start,end in spans:
        block=base_text[start:end]
        if block.startswith(('(segment','(via')):
            uid=UUID_RE.search(block)
            if uid and uid[1] in removed:
                # Drop the block and the indentation/newline that preceded it.
                cut=base_text.rfind('\n',last,start);chunks.append(base_text[last:cut if cut>=0 else start]);last=end;dropped+=1
            elif uid:surviving.add(uid[1])
    if dropped!=len(removed):raise ValueError(f'removed copper not found in base: {dropped}/{len(removed)}')
    reject_new_uuid_collisions(surviving,added_rows)
    tail=base_text[last:];close=tail.rstrip().rfind(')')
    if close<0:raise ValueError('board text has no closing parenthesis')
    # Spans start at '(' and keep their inner lines' absolute indentation.
    body=''.join('\n\t'+b for b in added)
    chunks.append(tail[:close].rstrip('\n')+body+'\n'+tail[close:])
    return ''.join(chunks)


def reviewed_cut_scope(plan,board_id,source_sha,dump,removed):
    """Bind complete-warning cuts to the same bounded source plan as native repair."""
    from scripts.pcbgen.route_jack_grid import repair_selection,repair_bounds
    if plan.get('board')!=board_id or plan.get('input_board_sha256')!=source_sha:
        raise ValueError('reviewed cut plan board/source mismatch')
    spec=plan.get('stage',{})
    if spec.get('repair') is not True or 'repair_source_uuids' not in spec:
        raise ValueError('reviewed cut plan requires explicit repair cuts')
    ids=spec['repair_source_uuids']
    if len(ids)!=len(set(ids)):raise ValueError('duplicate reviewed cut UUID')
    targets,cuts=repair_selection(dump,spec)
    if repair_bounds(dump,spec,targets,cuts) is None:
        raise ValueError('reviewed cut plan requires bounded geometry')
    if len(removed)!=len(cuts) or {r['uuid'] for r in removed}!=cuts:
        raise ValueError('actual removals differ from reviewed cuts')
    return sorted(cuts)


def merge(board_id,delta_paths,label,repair_ground=False,complete_native_warnings=False,native_zone_batch_size=1,reviewed_cut_plan=None):
    """Apply every shard delta to the board, gate it natively, and promote it if open edges fall."""
    if type(native_zone_batch_size) is not int or native_zone_batch_size not in (1,4,16):raise ValueError('native zone batch size must be1,4or16')
    if native_zone_batch_size!=1 and not complete_native_warnings:raise ValueError('native zone batching requires complete warning audits')
    if reviewed_cut_plan is not None and not complete_native_warnings:raise ValueError('reviewed cuts require complete warning audits')
    cut_plan_bytes=Path(reviewed_cut_plan).read_bytes() if reviewed_cut_plan is not None else None
    cut_plan=json.loads(cut_plan_bytes) if cut_plan_bytes is not None else None
    from scripts.pcbgen.route_jack_grid import PLANES,workspace,check,promotion_gate,connectivity_signature,split_pad_groups,stitched
    board=ROOT/'boards'/board_id/f'{board_id}.kicad_pcb';base_text=board.read_text()
    sha=hashlib.sha256(base_text.encode()).hexdigest()
    deltas=[json.loads(Path(p).read_text()) for p in delta_paths]
    stale=[p for p,d in zip(delta_paths,deltas) if d['base_sha256']!=sha]
    if stale:raise ValueError(f'deltas made for a different board: {stale}')
    deltas=[d for d in deltas if d['added'] or d['removed']]
    if not deltas:print('no shard changed copper');return None
    start=workspace(board_id,'shards-start');base=start/board.name;shutil.copyfile(board,base)
    before_drc,before=check(base)
    if [v for v in before_drc['violations'] if v['severity']=='error'] or before_drc['schematic_parity']:raise RuntimeError('base board not clean')
    ownership=disjoint(deltas)
    lost=sorted(set().union(*(set(d['nets'])-k for d,k in zip(deltas,ownership))))
    if lost:print(f'{len(lost)} nets claimed by two shards; the later shard loses them: {lost[:10]}')
    added={a['uuid']:a for d in deltas for a in d['added']}
    reverted=set();rejected_attempts=[]
    for attempt in range(6):
        work=workspace(board_id,'shards-merge');candidate=work/board.name
        candidate.write_text(merge_text(base_text,deltas,reverted))
        drc,after=check(candidate)
        if drc['schematic_parity']:raise RuntimeError('schematic parity findings after the shard merge')
        bad={i.get('uuid') for v in drc['violations'] if v['severity']=='error' for i in v['items']}
        culprits={added[u]['net'] for u in bad if u in added}
        if bad and not culprits:raise RuntimeError('merged DRC errors not attributable to shard copper')
        split=[n for n in PLANES if len(after['islands'].get(n,[None]))>len(before['islands'].get(n,[None]))]
        if split and not culprits:
            layers={PLANES[n] for n in split}
            culprits={a['net'] for a in added.values() if a['net'] not in reverted and a['layer'] in layers}
            culprits=culprits or {a['net'] for a in added.values() if a['net'] not in reverted and a['layer'] is None}
            print(f'{split} split by merged copper')
        if not culprits:break
        # The next workspace() call clears shards-merge. Preserve the actual
        # failing geometry and native findings before reverting whole nets.
        saved=work.with_name(work.name+f'-rejected-{attempt+1}')
        suffix=2
        while saved.exists():
            saved=work.with_name(work.name+f'-rejected-{attempt+1}-{suffix}');suffix+=1
        evidence={'attempt':attempt+1,'input_board_sha256':sha,
                  'candidate_board_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
                  'open_edges':after['open_edges'],'reverted_nets':sorted(culprits),
                  'native_errors':[v for v in drc['violations'] if v['severity']=='error'],
                  'plane_splits':split,'split_pad_groups':split_pad_groups(before,after),
                  'workspace':str(saved.relative_to(ROOT))}
        (work/'rejected-attempt.json').write_text(json.dumps(evidence,indent=2)+'\n')
        (work/'candidate-replay.json').write_text(json.dumps(delta(base_text,candidate.read_text()),sort_keys=True)+'\n')
        work.rename(saved);rejected_attempts.append(evidence)
        reverted|=culprits;print(f'merge attempt {attempt+1}: reverting {len(culprits)} nets with failing copper',flush=True)
    else:raise RuntimeError('merged DRC errors persist after reverting nets')
    stitch_receipt=None
    if repair_ground and split_pad_groups(before,after):
        staged={'open_edges_before':before['open_edges'],'open_edges_after':after['open_edges'],
                'open_by_net_after':{n:len(g)-1 for n,g in after['islands'].items()}}
        definition=json.loads((ROOT/'design/boards'/f'{board_id}.json').read_text())
        candidate,stitch_receipt=stitched(board_id,base,candidate,staged,{'name':f'shards-{label}'},definition,print)
        drc=json.loads(candidate.with_name('drc.json').read_text());after=json.loads(candidate.with_name('dump.json').read_text())
    fresh=workspace(board_id,'shards-fresh')/board.name;shutil.copyfile(candidate,fresh)
    fresh_drc,fresh_dump=check(fresh)
    agreement=connectivity_signature(after)==connectivity_signature(fresh_dump)
    candidate,drc,after=fresh,fresh_drc,fresh_dump
    receipt={'stage':f'shards-{label}','status':'NATIVE CHECKED DRAFT STAGE','shards':len(deltas),
             'open_edges_before':before['open_edges'],'open_edges_after':after['open_edges'],
             'nets_merged':len(set().union(*disjoint(deltas))-reverted),'nets_reverted':sorted(reverted),'nets_lost_to_overlap':lost,
             'rejected_attempts':rejected_attempts,
             'copper_added':sum(a['net'] not in reverted for a in added.values()),'drc_errors':sum(v['severity']=='error' for v in drc['violations']),
             'drc_warnings':sum(v['severity']=='warning' for v in drc['violations']),'parity':len(drc['schematic_parity']),
             'open_by_net_after':{n:len(g)-1 for n,g in after['islands'].items()}}
    receipt.update(promotion_gate(before,after,before_drc,drc))
    if complete_native_warnings:
        receipt['native_zone_batch_size']=native_zone_batch_size
        # Supplemental observations are opt-in and source-bound. Existing
        # findings survive, and the same ordinary gate evaluates the result.
        from scripts.pcbgen.complete_native_warnings import audit_current_reports
        receipt['raw_promotion_gate']=promotion_gate(before,after,before_drc,drc)
        evidence=workspace(board_id,'shards-complete-warnings')/'native-audits'
        try:
            options={} if native_zone_batch_size==1 else {'zone_batch_size':native_zone_batch_size}
            if cut_plan is not None:
                actual=delta(base_text,candidate.read_text())
                cuts=reviewed_cut_scope(cut_plan,board_id,sha,before,actual['removed'])
                options['reviewed_removed_uuids']=cuts
                receipt['reviewed_cut_plan']={'path':str(reviewed_cut_plan),'sha256':hashlib.sha256(cut_plan_bytes).hexdigest(),'removed_uuids':cuts,'bounds_mm':cut_plan['stage']['repair_bounds_mm']}
            complete_before,complete_after,proof=audit_current_reports(base,candidate,before_drc,drc,evidence,**options)
            receipt['complete_native_warning_evidence']=proof
            receipt.update(promotion_gate(before,after,complete_before,complete_after))
        except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as error:
            receipt['adopted']=False
            receipt['rejection_reason']='incomplete_native_warning_evidence'
            receipt['native_warning_evidence_error']=str(error)
    if stitch_receipt and 'agnd_stitch' in stitch_receipt:receipt['agnd_stitch']=stitch_receipt['agnd_stitch']
    if receipt['native_errors']:receipt['status']='REJECTED: fresh native DRC/parity errors'
    receipt['independent_connectivity_agrees']=agreement
    if not agreement:
        receipt['adopted']=False;receipt['rejection_reason']='independent_connectivity_changed'
    receipt['input_board_sha256']=sha
    receipt['candidate_board_sha256']=hashlib.sha256(candidate.read_bytes()).hexdigest()
    reports=board.parent/'reports'/'grid-routing';reports.mkdir(parents=True,exist_ok=True)
    # Retain the exact candidate even when a membership/warning gate rejects it.
    replay=delta(base_text,candidate.read_text())
    replay_path=reports/f'shards-{label}-copper.json'
    replay_path.write_text(json.dumps(replay,sort_keys=True)+'\n')
    receipt['copper_added']=len(replay['added']);receipt['copper_removed']=len(replay['removed'])
    receipt['copper_replay']={'path':str(replay_path.relative_to(ROOT)),
                            'sha256':hashlib.sha256(replay_path.read_bytes()).hexdigest(),'base_sha256':sha}
    if receipt['adopted']:
        from scripts.pcbgen.adopt_obstacle_benchmark import publication_copy
        if hashlib.sha256(board.read_bytes()).hexdigest()!=sha:
            raise RuntimeError('canonical board changed during native checks; refuse stale promotion')
        native_candidate=candidate
        candidate,cache=publication_copy(board_id,candidate,drc,after)
        receipt['native_filled_board_sha256']=hashlib.sha256(native_candidate.read_bytes()).hexdigest()
        receipt['candidate_board_sha256']=hashlib.sha256(candidate.read_bytes()).hexdigest()
        receipt['publication_cache']=cache
    (reports/f'shards-{label}.json').write_text(json.dumps(receipt,indent=1,sort_keys=True)+'\n')
    print(f"shards-{label}: {receipt['open_edges_before']} -> {receipt['open_edges_after']} open edges",flush=True)
    if receipt['adopted']:
        if hashlib.sha256(board.read_bytes()).hexdigest()!=sha:
            raise RuntimeError('canonical board changed during native checks; refuse stale promotion')
        shutil.copyfile(candidate,board);print('promoted',board.relative_to(ROOT),flush=True)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);sub=p.add_subparsers(dest='cmd',required=True)
    d=sub.add_parser('delta',help='copper delta between a base and a shard board');d.add_argument('base',type=Path);d.add_argument('final',type=Path);d.add_argument('-o','--output',type=Path,required=True)
    m=sub.add_parser('merge',help='apply shard deltas to boards/<id>/<id>.kicad_pcb (KiCad via scripts/kicad/run.sh)')
    m.add_argument('board_id',choices=('osc-jack-left','osc-jack-right','osc-core'));m.add_argument('deltas',nargs='+');m.add_argument('--label',required=True)
    m.add_argument('--repair-ground',action='store_true',help='try existing AGND stitching before the complete membership gate')
    m.add_argument('--native-zone-batch-size',type=int,choices=(1,4,16),default=1,help='opt-in bounded artwork batches; requires complete native warning audits')
    m.add_argument('--complete-native-warnings',action='store_true',help='require source-bound complete native hole/silk evidence; unsupported scope rejects')
    m.add_argument('--reviewed-cut-plan',type=Path,help='exact source-bound bounded repair plan; requires complete native warning audits')
    a=p.parse_args()
    if a.cmd=='delta':
        out=delta(a.base.read_text(),a.final.read_text());a.output.write_text(json.dumps(out)+'\n')
        print(f"delta: {len(out['removed'])} removed, {len(out['added'])} added, {len(out['nets'])} nets")
    else:merge(a.board_id,a.deltas,a.label,a.repair_ground,a.complete_native_warnings,a.native_zone_batch_size,a.reviewed_cut_plan)


if __name__=='__main__':main()
