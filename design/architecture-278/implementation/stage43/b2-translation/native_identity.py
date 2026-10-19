"""Reject loader-side net reassignment before connectivity, refill or save."""
from pathlib import Path
import json,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from native_guard import check_native
from identity_guard import digest

def verify(directory):
    path=directory/'osc-jack-left.kicad_pcb';raw=path.read_text()
    result={'board_sha256':digest(raw),'operation':'LoadBoard then check_native; no connectivity/refill/save'}
    try:
        b=pcbnew.LoadBoard(str(path));result['checks']=check_native(b,raw);result['accepted_identity_only']=True
    except ValueError as e:result.update(accepted_identity_only=False,error=str(e))
    if path.read_text()!=raw:raise ValueError('read-only load changed source file')
    (directory/'native-load.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    if not result['accepted_identity_only']:raise SystemExit(1)
if __name__=='__main__':verify(Path(sys.argv[1]))
