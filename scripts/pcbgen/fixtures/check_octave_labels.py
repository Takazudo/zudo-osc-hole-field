"""Native reference-label preservation and deterministic sync checks."""
import sys
import tempfile
import shutil
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.octave_labels import place_default_reference
from scripts.pcbgen.sync import sync
for n in range(1,6):
 bid=f'osc-octave-{n}'
 path=ROOT/'boards'/bid/(bid+'.kicad_pcb')
 before=path.read_bytes()
 board=pcbnew.LoadBoard(str(path));fp=next(f for f in board.GetFootprints() if f.GetReference().startswith('SW'))
 x=pcbnew.ToMM(fp.GetPosition().x); y=pcbnew.ToMM(fp.GetPosition().y)
 text=fp.Reference()
 assert abs(pcbnew.ToMM(text.GetPosition().x)-x)<1e-6
 assert abs(pcbnew.ToMM(text.GetPosition().y)-(y-12))<1e-6
 hardware={'x_mm':x-100,'y_mm':y-50,'rot_deg':fp.GetOrientationDegrees()}
 text.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x+1),pcbnew.FromMM(y-11)))
 edited=(text.GetPosition().x,text.GetPosition().y)
 assert not place_default_reference(fp,hardware)
 assert (text.GetPosition().x,text.GetPosition().y)==edited
 with tempfile.TemporaryDirectory(prefix='octave-label-',dir=ROOT/'.circuit-cache') as tmp:
  target=Path(tmp)/(bid+'.kicad_pcb')
  target.write_bytes(before)
  shutil.copyfile(path.with_suffix('.kicad_pro'),target.with_suffix('.kicad_pro'))
  sync(bid,target)
  assert target.read_bytes()==before, bid+' sync changed bytes'
print('PASS: five tongue references, edited positions preserved, repeat sync byte-identical')
