"""Source geometry/assembly consequence; never a manufacturing qualification."""
from pathlib import Path
import hashlib,json,math,sys
from shapely.geometry import Polygon,Point
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import top_level_spans,kind,value
BASE='d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(board,dump):
 if sha(board)!=BASE:raise ValueError('baseline bytes')
 data=json.loads(dump.read_text())
 if data['board_sha256']!=BASE:raise ValueError('native geometry baseline')
 raw=board.read_text();fp=None
 for a,b in top_level_spans(raw):
  t=raw[a:b]
  if kind(t)=='footprint' and value(t,'uuid')=='09a6be67-4e4d-532a-a30b-10b5e3b0259b':fp=t
 if fp is None:raise ValueError('footprint absent')
 required=['(at 270.31 133.94 90)','(start 1.64 -0.91)','(start -1.64 0.91)','(property "MPN" ""','(size 0.81 0.86)','(layers "B.Cu" "B.Mask" "B.Paste")']
 if not all(t in fp for t in required) or any(t in fp for t in ['solder_mask_margin','solder_paste_margin','solder_paste_margin_ratio']):raise ValueError('footprint or aperture assumption changed')
 if '(pad_to_mask_clearance 0)' not in raw or '(tenting\n\t\t\t(front yes)\n\t\t\t(back yes)' not in raw:raise ValueError('mask/tenting assumptions')
 center=Point(271.32,132.8);rows=[];unknown=[]
 for p in data['pads']:
  polygon=Polygon([(x/1e6,y/1e6) for x,y in p['poly']]);distance=center.distance(polygon)
  if not math.isfinite(distance):
   unknown.append(dict(ref=p['ref'],pad=p['pad'],center_distance_mm=math.hypot(p['xy'][0]/1e6-271.32,p['xy'][1]/1e6-132.8)));continue
  rows.append(dict(uuid=p['uuid'],ref=p['ref'],pad=p['pad'],layers=p['layers'],copper_gap_mm=round(distance-.3,9),drill_gap_mm=round(distance-.15,9)))
 rows.sort(key=lambda p:p['copper_gap_mm']);nearest=rows[0]
 if nearest['uuid']!='b9d402b4-b8c4-5ab2-a8c0-3fd450c4809c' or nearest['copper_gap_mm']!=.28 or nearest['drill_gap_mm']!=.43:raise ValueError('nearest pad geometry changed')
 # Court rectangle local ±1.64,±.91 rotated90 around270.31,133.94.
 court=[269.4,132.3,271.22,135.58];center_gap=round(271.32-court[2],9)
 return dict(baseline_sha256=BASE,dump_sha256=sha(dump),footprint_sha256=hashlib.sha256(fp.encode()).hexdigest(),via_center_mm=[271.32,132.8],via_diameter_mm=.6,drill_mm=.3,nearest_five_pads=rows[:5],empty_polygon_inputs=unknown,empty_polygon_limit='Four remote mounting holes are not solder pads; no empty polygon treated as a free local solder-pad region.',pad_copper_and_nominal_aperture_nonoverlap=True,pad_mask_expansion_mm=0,local_mask_paste_overrides=False,inherited_via_tenting=['front','back'],courtyard_bounds_mm=court,via_center_outside_courtyard_mm=center_gap,annulus_intrusion_into_courtyard_mm=round(.3-center_gap,9),drill_intrusion_into_courtyard_mm=round(.15-center_gap,9),assembly_status='UNRESOLVED',limits='Via-in-pad geometry removed, but courtyard interaction remains. Exact populated body envelope/MPN and process tenting quality unavailable. No fabrication or physical acceptance. Nominal source apertures only, not generated manufacturing outputs.')
if __name__=='__main__':
 result=check(ROOT/'.circuit-cache/stage44-b2-fresh/osc-jack-left.kicad_pcb',ROOT/'.circuit-cache/stage45/dump.json');out=HERE/'assembly.json'
 if '--write' in sys.argv:out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 elif json.loads(out.read_text())!=result:raise ValueError('assembly replay')
 print(json.dumps({'pad_gap_mm':result['nearest_five_pads'][0]['copper_gap_mm'],'courtyard_overlap_mm':result['annulus_intrusion_into_courtyard_mm'],'assembly_status':result['assembly_status']}))
