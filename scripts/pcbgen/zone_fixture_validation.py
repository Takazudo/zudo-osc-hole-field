"""Exact native fixture checks, optionally in a fresh process per fixture."""
import hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

def text_rows(board):
    objects=list(board.GetDrawings())
    for fp in board.GetFootprints():objects.extend([*fp.GetFields(),*fp.GraphicalItems()])
    return {x.m_Uuid.AsString():x.GetShownText(True) for x in objects if hasattr(x,'GetShownText')}

def native_fixture_check(fixture,uid,layer,item_uids,source_texts,source_signature,pcbnew):
    from scripts.pcbgen.audit_zone_silk_scope import native_zone_signature
    loaded=pcbnew.LoadBoard(str(fixture));zones=list(loaded.Zones())
    if len(zones)!=1 or zones[0].m_Uuid.AsString()!=uid:raise ValueError('fixture zone identity changed')
    if list(loaded.GetTracks()) or any(list(fp.Pads()) for fp in loaded.GetFootprints()):raise ValueError('unrelated fixture copper remains')
    actual_ids=[x.m_Uuid.AsString() for x in list(loaded.GetFootprints())+[x for x in loaded.GetDrawings() if x.GetLayer()!=pcbnew.Edge_Cuts]]
    if len(actual_ids)!=len(set(actual_ids)) or set(actual_ids)!=set(item_uids):raise ValueError('fixture artwork scope changed')
    actual=text_rows(loaded)
    if any(source_texts.get(k)!=v for k,v in actual.items()):raise ValueError('fixture rendered text changed')
    geometry=native_zone_signature(zones[0].GetFilledPolysList(layer))
    if geometry!=source_signature:raise ValueError('fixture native zone shape changed')
    return geometry

def context_hashes(fixture):
    return {suffix:hashlib.sha256(fixture.with_suffix(suffix).read_bytes()).hexdigest() for suffix in ('.kicad_pro','.kicad_dru')}

def worker(request_path,pcbnew,version):
    request=json.loads(Path(request_path).read_text());fixture=Path(request['fixture'])
    if request['version']!=version or version!='10.0.6':raise ValueError('fixture worker native version changed')
    if hashlib.sha256(fixture.read_bytes()).hexdigest()!=request['fixture_sha256']:raise ValueError('fixture worker source bytes changed')
    if context_hashes(fixture)!=request['context_sha256']:raise ValueError('fixture worker context changed')
    geometry=native_fixture_check(fixture,request['uid'],request['layer'],request['item_uids'],request['source_texts'],request['source_signature'],pcbnew)
    return dict(version=version,fixture_sha256=request['fixture_sha256'],context_sha256=request['context_sha256'],native_geometry_sha256=geometry)

def isolated_fixture_check(fixture,uid,layer,item_uids,source_texts,source_signature):
    fixture=Path(fixture)
    request=dict(version='10.0.6',fixture=str(fixture.resolve()),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),context_sha256=context_hashes(fixture),uid=uid,layer=layer,item_uids=item_uids,source_texts=source_texts,source_signature=source_signature)
    path=fixture.parent/'native-validation-request.json';path.write_text(json.dumps(request)+'\n')
    # A distinct interpreter owns every fixture LoadBoard; process exit releases
    # its native allocations before either the next fixture or DRC subprocess.
    try:
        result=subprocess.run([sys.executable,str(Path(__file__).resolve()),str(path)],check=True,capture_output=True,text=True)
    except subprocess.CalledProcessError as failure:
        (fixture.parent/'native-validation.stderr').write_text(failure.stderr or '')
        (fixture.parent/'native-validation-failure.json').write_text(json.dumps(dict(exit_status=failure.returncode,request=str(path)))+'\n')
        raise
    (fixture.parent/'native-validation.stderr').write_text(getattr(result,'stderr','') or '')
    proof=json.loads(result.stdout)
    expected={k:request[k] for k in ('version','fixture_sha256','context_sha256')}|dict(native_geometry_sha256=source_signature)
    if proof!=expected:raise ValueError('fixture worker validation receipt changed')
    if hashlib.sha256(fixture.read_bytes()).hexdigest()!=request['fixture_sha256'] or context_hashes(fixture)!=request['context_sha256']:
        raise ValueError('fixture source/context changed after worker')
    (fixture.parent/'native-validation.json').write_text(json.dumps(proof)+'\n')
    return proof['native_geometry_sha256']

if __name__=='__main__':
    import pcbnew
    version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
    print(json.dumps(worker(Path(sys.argv[1]),pcbnew,version)))
