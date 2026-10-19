"""Compare full packages against baseline with only native pose operations replayed."""
from pathlib import Path
import re,tempfile
from identity_guard import top_level_spans,kind,digest

def tokens(raw):return re.findall(r'"(?:[^"\\]|\\.)*"|[^\s()]+|[()]',raw)
def package_blocks(raw):
    result={}
    for a,z in top_level_spans(raw):
        part=raw[a:z]
        if kind(part)=='footprint':
            ref=re.search(r'\(property\s+"Reference"\s+"([^"]+)"',part)[1]
            if ref in result:raise ValueError('duplicate package reference')
            result[ref]=part
    return result

def compare_serialized(expected,actual,refs):
    a,b=package_blocks(expected),package_blocks(actual)
    for ref in refs:
        if tokens(a[ref])!=tokens(b[ref]):raise ValueError('non-pose package change: '+ref)
    return {ref:digest(' '.join(tokens(b[ref]))) for ref in sorted(refs)}

def verify(baseline,candidate,refs):
    import pcbnew
    if pcbnew.GetBuildVersion()!='10.0.6':raise ValueError('package oracle version')
    original=pcbnew.LoadBoard(str(baseline));source={f.GetReference():f for f in original.GetFootprints()}
    actual={f.GetReference():f for f in candidate.GetFootprints()}
    for ref in refs:
        f,target=source[ref],actual[ref]
        if f.GetLayer()!=target.GetLayer():f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(target.GetOrientationDegrees());f.SetPosition(target.GetPosition())
    with tempfile.TemporaryDirectory(prefix='stage44-package-proof-') as td:
        expected=Path(td)/'expected.kicad_pcb';observed=Path(td)/'observed.kicad_pcb'
        pcbnew.SaveBoard(str(expected),original);pcbnew.SaveBoard(str(observed),candidate)
        return compare_serialized(expected.read_text(),observed.read_text(),refs)
