"""Tiny disposable selected-zone API qualification. Never loads project CAD."""
import collections
import hashlib
import json
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

STATUS = 'SYNTHETIC_SELECTED_ZONE_QUALIFIED_NOT_BOARD_ACCEPTANCE'
NS = uuid.UUID('ff199280-3fce-4e20-b555-466bb21bcded')
def uid(name): return str(uuid.uuid5(NS, name))
def sha(data): return hashlib.sha256(data).hexdigest()
def require(condition, message):
    if not condition: raise ValueError(message)

def fixture():
    """Six-layer, 30mm square; all dimensions synthetic, no product inputs."""
    out=['(kicad_pcb (version 20260206) (generator "pcbnew")',
         '(general (thickness 1.6)) (paper "A4")',
         '(layers (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (8 "In3.Cu" signal) (10 "In4.Cu" signal) (2 "B.Cu" signal) (1 "F.Mask" user) (3 "B.Mask" user) (25 "Edge.Cuts" user))',
         '(setup (pad_to_mask_clearance 0))']
    for i,(a,b) in enumerate([((0,0),(30,0)),((30,0),(30,30)),((30,30),(0,30)),((0,30),(0,0))]):
        out.append(f'(gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid("edge"+str(i))}"))')
    for name,x,y,net in [('A',5,5,'+12V'),('B',12,5,'+12V'),('N',26,26,'+12V'),('X',10,10,'OTHER')]:
        out.append(f'(footprint "Synthetic:Pad" (layer "F.Cu") (uuid "{uid(name)}") (at {x} {y}) (property "Reference" "{name}" (at 0 -2) (layer "F.Cu") (effects (font (size 1 1) (thickness 0.15)))) (pad "1" thru_hole circle (at 0 0) (size 1.5 1.5) (drill 0.8) (layers "*.Cu" "*.Mask") (remove_unused_layers yes) (net "{net}") (uuid "{uid(name+"pad")}")))')
    for name,a,b in [('duplicate',(3,3),(4,3)),('duplicate',(3,4),(4,4))]:
        out.append(f'(segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (width 0.25) (layer "F.Cu") (net "+12V") (uuid "{uid(name)}"))')
    out.append(f'(via (at 8 5) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (remove_unused_layers yes) (net "+12V") (uuid "{uid("via")}"))')
    for name,layer,net,box,filled in [('target','In4.Cu','+12V',(2,2,18,18),False),('sentinel','F.Cu','OTHER',(20,2,28,10),True),('empty','B.Cu','OTHER',(20,12,28,20),False),('dependency','In4.Cu','+12V',(16,2,23,8),True)]:
        x,y,r,t=box; pts=f'(xy {x} {y}) (xy {r} {y}) (xy {r} {t}) (xy {x} {t})'
        out.append(f'(zone (net "{net}") (layer "{layer}") (uuid "{uid(name)}") (name "{name}") (hatch edge 0.5) (connect_pads yes (clearance 0.2)) (min_thickness 0.15) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3) (island_removal_mode 0)) (polygon (pts {pts}))'+(f'(filled_polygon (layer "{layer}") (pts {pts}))' if filled else '')+')')
    out.append(f'(zone (net "") (layers "F.Cu" "In4.Cu") (uuid "{uid("keepout")}") (hatch edge 0.5) (keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) (polygon (pts (xy 13 12) (xy 15 12) (xy 15 14) (xy 13 14))))')
    return ('\n'.join(out)+')\n').encode()

def parse(data):
    require(len(data)<2*1024*1024,'fixture size')
    stack=[];root=None
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',data.decode()):
        if t=='(':
            node=[]
            if stack: stack[-1].append(node)
            else: require(root is None,'multiple roots');root=node
            stack.append(node)
        elif t==')':
            require(bool(stack),'unbalanced');stack.pop()
        else:
            require(bool(stack),'atom outside');stack[-1].append(t)
    require(not stack and root and root[0]=='kicad_pcb','invalid fixture')
    return root

def nodes(tree,tag): return [x for x in tree if isinstance(x,list) and x and x[0]==tag]
def value(tree,tag):
    found=nodes(tree,tag);require(len(found)==1,'ambiguous '+tag);return found[0][1:]
def atom(s): return json.loads(s) if s.startswith('"') else s
def source_tracks(data):
    rows=[]
    for x in nodes(parse(data),'segment'):
        rows.append((atom(value(x,'uuid')[0]),tuple(round(float(v)*1e6) for v in value(x,'start')),tuple(round(float(v)*1e6) for v in value(x,'end')),round(float(value(x,'width')[0])*1e6),atom(value(x,'layer')[0]),atom(value(x,'net')[0])))
    return collections.Counter(rows)

def native_tracks(board):
    rows=[]
    for x in board.GetTracks():
        if type(x).__name__=='PCB_VIA': continue
        rows.append((x.m_Uuid.AsString(),(x.GetStart().x,x.GetStart().y),(x.GetEnd().x,x.GetEnd().y),x.GetWidth(),board.GetLayerName(x.GetLayer()),x.GetNetname()))
    return collections.Counter(rows)

def canonical(node): return json.dumps(node,separators=(',',':'),sort_keys=True)
def zones_serialized(data):
    # UUID+complete canonical node MULTISET, never a UUID-keyed lossy dictionary.
    return collections.Counter(canonical(x) for x in nodes(parse(data),'zone') if atom(value(x,'uuid')[0])!=uid('target'))

def persistent(data):
    tree=parse(data)
    for z in nodes(tree,'zone'):
        if atom(value(z,'uuid')[0])==uid('target'):
            z[:]=[v for v in z if not (isinstance(v,list) and v and v[0]=='filled_polygon')]
    # Top-level serialization may reorder objects; preserve complete multiplicity.
    return collections.Counter(canonical(x) for x in tree[1:])

def select(board):
    found=[z for z in board.Zones() if z.m_Uuid.AsString()==uid('target')]
    require(len(found)==1,'target cardinality');z=found[0]
    require(z.GetNetname()=='+12V' and board.GetLayerName(z.GetLayer())=='In4.Cu' and not z.GetIsRuleArea(),'target identity')
    return z

def observe(board,pcb):
    conn=board.GetConnectivity();conn.Build(board)
    layers=[pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.In3_Cu,pcb.In4_Cu,pcb.B_Cu]
    pads=[p for f in board.GetFootprints() for p in f.Pads()]
    vias=[x for x in board.GetTracks() if type(x).__name__=='PCB_VIA']
    flash=[{'uuid':x.m_Uuid.AsString(),'net':x.GetNetname(),'position':[x.GetPosition().x,x.GetPosition().y],'layers':[[board.GetLayerName(l),int(x.GetZoneLayerOverride(l))] for l in layers if x.IsOnLayer(l)]} for x in pads+vias]
    fills=[{'uuid':z.m_Uuid.AsString(),'filled':bool(z.IsFilled()),'layers':[[board.GetLayerName(l),int(z.GetFilledPolysList(l).OutlineCount()),str(z.GetFilledPolysList(l).Format())] for l in layers if z.IsOnLayer(l)]} for z in board.Zones() if not z.GetIsRuleArea()]
    # Graph traversal, not direct-neighbour membership; retain actual native object identity.
    byname={f.GetReference()+'.'+p.GetNumber():p for f in board.GetFootprints() for p in f.Pads()}
    start=byname['A.1'];seen=set();queue=[start]
    def key(x): return (x.m_Uuid.AsString(),type(x).__name__,x.GetPosition().x,x.GetPosition().y)
    while queue:
        x=queue.pop();k=key(x)
        if k in seen:continue
        seen.add(k);require(len(seen)<100,'fixture graph bound')
        queue.extend(conn.GetConnectedItems(x))
    return {'flashing':flash,'fills':fills,'A_to_B':key(byname['B.1']) in seen,'A_to_N':key(byname['N.1']) in seen}

def nonselected(o):return sorted([r for r in o['fills'] if r['uuid']!=uid('target')],key=canonical)

def flash_changes(before,after):
    def index(obs):
        rows={}
        for item in obs['flashing']:
            for layer,override in item['layers']:
                key=(item['uuid'],item['net'],tuple(item['position']),layer)
                require(key not in rows,'duplicate flashing composite');rows[key]=override
        return rows
    a,b=index(before),index(after);require(a.keys()==b.keys(),'flashing identity changed')
    return [{'identity':list(k),'before':a[k],'after':b[k]} for k in a if a[k]!=b[k]]

def qualify_flashing(before,after,reloaded):
    changes=flash_changes(before,after)
    # Deliberately strict confinement: only target-net In4 derived state may
    # change. Global collateral flashing is a finding, NOT silently accepted.
    require(all(x['identity'][1]=='+12V' and x['identity'][3]=='In4.Cu' for x in changes),'collateral flashing outside selected net/layer')
    require(not flash_changes(after,reloaded),'flashing not preserved on reload')
    require(nonselected(after)==nonselected(reloaded),'nonselected fill changed on reload')
    return changes

def run_case(root,pcb,custom,events):
    root.mkdir();boardfile=root/'fixture.kicad_pcb';data=fixture();boardfile.write_bytes(data)
    (root/'fixture.kicad_pro').write_text('{}\n')
    rule='(version 1)\n(rule "synthetic observable clearance" (constraint clearance (min 2mm)))\n' if custom else '(version 1)\n'
    (root/'fixture.kicad_dru').write_text(rule)
    events.append({'stage':'input','custom_rules':custom,'board_hash':sha(data),'rules_hash':sha(rule.encode())});emit(events)
    b=pcb.LoadBoard(str(boardfile));require(b is not None,'load returned null')
    require(native_tracks(b)==source_tracks(data),'duplicate/geometry loss at initial native load')
    before=observe(b,pcb);events.append({'stage':'loaded','custom_rules':custom,'observation':before});emit(events)
    control=root/'control.kicad_pcb';require(pcb.SaveBoard(str(control),b) is not False,'control save failed')
    require(source_tracks(control.read_bytes())==source_tracks(data),'duplicate/geometry loss at control save')
    controlb=pcb.LoadBoard(str(control));require(native_tracks(controlb)==source_tracks(data),'control reload loss')
    # SaveBoard may change the object's filename. Fresh original load keeps the
    # rule basename fixed rather than accidentally testing control.kicad_dru.
    b=pcb.LoadBoard(str(boardfile));require(native_tracks(b)==source_tracks(data),'fresh reload loss')
    target=select(b);selection=pcb.ZONES();selection.append(target)
    require(len(selection)==1,'selection length')
    events.append({'stage':'fill_start','custom_rules':custom});emit(events)
    require(pcb.ZONE_FILLER(b).Fill(selection,False) is True,'Fill not true')
    after=observe(b,pcb)
    events.append({'stage':'fill_observed','custom_rules':custom,'after':after,'flashing_changes':flash_changes(before,after)});emit(events)
    require(nonselected(before)==nonselected(after),'nonselected native fill changed')
    require(native_tracks(b)==source_tracks(data),'native tracks changed')
    filled=root/'filled.kicad_pcb';require(pcb.SaveBoard(str(filled),b) is not False,'fill save failed')
    require(zones_serialized(control.read_bytes())==zones_serialized(filled.read_bytes()),'nonselected persistent zone changed')
    require(persistent(control.read_bytes())==persistent(filled.read_bytes()),'persistent mutation outside selected polygons')
    require(source_tracks(filled.read_bytes())==source_tracks(data),'filled serialized tracks changed')
    again=pcb.LoadBoard(str(filled));require(native_tracks(again)==source_tracks(data),'filled reload tracks changed')
    reloaded=observe(again,pcb)
    events.append({'stage':'mutation_observations','custom_rules':custom,'after':after,'reloaded':reloaded,'flashing_changes':flash_changes(before,after)});emit(events)
    qualify_flashing(before,after,reloaded)
    # A probe 1.2mm from foreign pad centre: outside its0.75mm radius, inside custom2mm clearance.
    poly=select(b).GetFilledPolysList(pcb.In4_Cu)
    probe=bool(poly.Contains(pcb.VECTOR2I(pcb.FromMM(11.2),pcb.FromMM(10))))
    keepout=bool(poly.Contains(pcb.VECTOR2I(pcb.FromMM(14),pcb.FromMM(13))))
    require(not keepout,'keepout ignored')
    require(after['A_to_B'] and not after['A_to_N'],'positive/negative connectivity control')
    require(reloaded['A_to_B'] and not reloaded['A_to_N'],'reload connectivity control')
    events.append({'stage':'case_complete','custom_rules':custom,'after':after,'reloaded':reloaded,'rule_probe_filled':probe,'keepout_probe_filled':keepout,'output_hash':sha(filled.read_bytes()),'input_unchanged':boardfile.read_bytes()==data});emit(events)
    require(boardfile.read_bytes()==data,'input changed')
    return probe

def emit(events,status='RUNNING',error=None):
    for event in events:
        if 'monotonic_seconds' not in event:event['monotonic_seconds']=time.monotonic()
    obj={'status':status,'events':events,'error':error,'board_acceptance':False,'full_board_executed':False}
    text=json.dumps(obj,sort_keys=True);require(len(text.encode())<100000,'receipt bound')
    print(text,flush=True)

def main():
    events=[]
    try:
        import pcbnew
        cli=subprocess.run(['kicad-cli','version'],capture_output=True,text=True,timeout=5,check=True)
        require(cli.stdout.strip()=='10.0.6' and pcbnew.GetBuildVersion()=='10.0.6','exact version mismatch')
        events.append({'stage':'versions','cli':cli.stdout.strip(),'pcbnew':pcbnew.GetBuildVersion(),'fixture_sha256':sha(fixture())});emit(events)
        plain=run_case(Path('/scratch/plain'),pcbnew,False,events)
        ruled=run_case(Path('/scratch/ruled'),pcbnew,True,events)
        require(plain and not ruled,'custom rule effect not observed; initialization unqualified')
        emit(events,STATUS);return 0
    except Exception as exc:
        emit(events,'FAILED',type(exc).__name__+': '+str(exc)[:600]);return 1

if __name__=='__main__':raise SystemExit(main())
