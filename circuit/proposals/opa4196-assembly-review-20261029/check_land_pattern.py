import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,sys.argv[1])
from scripts.schgen.core import parse,tokens,children
root=Path(sys.argv[2]);results=[]
for v in ['UNI_ROYAL/BA1','UNI_ROYAL/RevP','YAGEO/BA1','YAGEO/RevP']:
 p=root/v/'candidate/footprints/zudo-osc-hole-field.pretty/SOIC-14_3.9x8.7mm_P1.27mm.kicad_mod'
 t=parse(tokens(p.read_text()))[0];pads=children(t,'pad');assert len(pads)==14
 assert {x[1] for x in pads}=={str(i) for i in range(1,15)}
 for x in pads:
  n=int(x[1]);at=list(map(float,children(x,'at')[0][1:3]));sz=list(map(float,children(x,'size')[0][1:3]))
  assert at==([-2.475,round(-3.81+(n-1)*1.27,2)] if n<=7 else [2.475,round(3.81-(n-8)*1.27,2)])
  assert sz==[1.95,0.6]
 results.append({'variant':v,'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pads':14,'pitch_mm':1.27,'row_centers_mm':[-2.475,2.475],'pad_mm':[1.95,0.6],'right_inner_edge_mm':1.5,'right_outer_edge_mm':3.45})
print(json.dumps({'status':'PASS actual footprint extraction; NOT assembly acceptance','variants':results,'TI_D0014A_example':{'pdf_page_1based':41,'pitch_mm':1.27,'row_centers_mm':[-2.7,2.7],'pad_mm':[1.55,0.6],'right_inner_edge_mm':1.925,'right_outer_edge_mm':3.475},'comparison':'Same pitch and width. Actual copper extends 0.425mm farther inward, 0.025mm less outward. TI layout is an example, not a mandatory identical land pattern.'},indent=2))
