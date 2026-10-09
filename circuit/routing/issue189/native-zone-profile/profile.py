"""Pinned-native timing/equivalence experiment only; no DRC or promotion claim."""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts,zone_fixture_text

def fingerprint(poly):
    # Exact10.0.6 Format emits all outline/hole vertices and closure, but omits arcs.
    if poly.ArcCount():raise ValueError('native Format omits arcs; unsupported')
    return hashlib.sha256(poly.Format().encode()).hexdigest()

parser=argparse.ArgumentParser();parser.add_argument('before',type=Path);parser.add_argument('after',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
import pcbnew
version=subprocess.check_output(['kicad-cli','version'],text=True).strip();assert version=='10.0.6'
args.output.mkdir(parents=True,exist_ok=True);rows=[]
expected=['95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5','b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66']
for stage,source in enumerate([args.before,args.after]):
    digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest==expected[stage]
    board=pcbnew.LoadBoard(str(source));text=source.read_text();fps=list(board.GetFootprints());item=fps[0].m_Uuid.AsString();all_ids={x.m_Uuid.AsString() for x in fps}|{x.m_Uuid.AsString() for x in board.GetDrawings() if x.GetLayer()!=pcbnew.Edge_Cuts}
    for zone in board.Zones():
        if zone.GetIsRuleArea():continue
        for layer in zone.GetLayerSet().Seq():
            if layer not in [pcbnew.F_Cu,pcbnew.B_Cu]:continue
            uid=zone.m_Uuid.AsString();folder=args.output/f'{stage}-{uid}';folder.mkdir(exist_ok=True);fixture=folder/source.name
            fixture.write_text(zone_fixture_text(zone_fixture_parts(text,uid,all_ids),item))
            for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(source.with_suffix(suffix),fixture.with_suffix(suffix))
            loaded=pcbnew.LoadBoard(str(fixture));zones=list(loaded.Zones());assert len(zones)==1 and zones[0].m_Uuid.AsString()==uid
            old=zone.GetFilledPolysList(layer);new=zones[0].GetFilledPolysList(layer)
            start=time.monotonic()
            for left,right in [(old,new),(new,old)]:
                diff=left.CloneDropTriangulation();diff.BooleanSubtract(right);assert diff.IsEmpty()
            boolean_seconds=time.monotonic()-start
            start=time.monotonic();a=fingerprint(old);b=fingerprint(new);assert a==b;format_seconds=time.monotonic()-start
            changed=new.CloneDropTriangulation();point=changed.CVertex(0);changed.SetVertex(0,pcbnew.VECTOR2I(point.x+1,point.y));assert fingerprint(changed)!=b
            row=dict(stage=stage,source_sha256=digest,fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),zone_uuid=uid,layer=pcbnew.LayerName(layer),points=old.FullPointCount(),arcs=old.ArcCount(),native_format_sha256=a,bidirectional_boolean_equal=True,format_equal=True,one_nm_vertex_change_detected=True,boolean_seconds=boolean_seconds,format_seconds=format_seconds)
            rows.append(row);print(json.dumps(row),flush=True)
            (args.output/'result.json').write_text(json.dumps(dict(status='PARTIAL PROFILE; NO ACCEPTANCE',version=version,rows=rows),indent=2)+'\n')
assert len(rows)==4
(args.output/'result.json').write_text(json.dumps(dict(status='COMPLETE FOUR-FIXTURE NATIVE GEOMETRY PROFILE; NO DRC OR PROMOTION CLAIM',version=version,rows=rows),indent=2)+'\n')
