#!/usr/bin/env python3
from pathlib import Path
import json,xml.etree.ElementTree as ET
import cairosvg,fitz
from PIL import Image,ImageOps,ImageDraw
R=Path(__file__).resolve().parents[1];src=(R/'panels/panel.svg').read_text()
ET.register_namespace('','http://www.w3.org/2000/svg')
def crop(name,x,y,w,h,scale=8):
 root=ET.fromstring(src);root.set('viewBox',f'{x} {y} {w} {h}');root.set('width',f'{w}mm');root.set('height',f'{h}mm');s=ET.tostring(root,encoding='unicode')
 (R/f'studies/{name}.svg').write_text(s)
 cairosvg.svg2png(bytestring=s.encode(),write_to=str(R/f'studies/{name}.png'),output_width=round(w*scale),output_height=round(h*scale))
cairosvg.svg2png(bytestring=src.encode(),write_to=str(R/'panels/panel.png'),output_width=2226,output_height=2086)
cairosvg.svg2pdf(bytestring=src.encode(),write_to=str(R/'panels/panel-1to1.pdf'))
crop('jack-grid',0,16,318,152,7)
crop('control-grid',0,170,318,128,7)
crop('utility-jacks',4,131.5,207,32,8)
crop('utility-controls',91,261.8,51,28.6,20)
crop('env-offset',208,171,104,124,9)
# A single comparison study of the user grid and reconstructed gold/black version.
im1=Image.open(R/'reference/user-jack-grid.png').convert('RGB');im2=Image.open(R/'studies/jack-grid.png').convert('RGB')
w=1600
a=im1.resize((w,round(im1.height*w/im1.width)));b=im2.resize((w,round(im2.height*w/im2.width)))
canvas=Image.new('RGB',(w,a.height+b.height+80),'#101211');draw=ImageDraw.Draw(canvas)
draw.text((18,10),'USER GRID / source screenshot',fill='#edece5');canvas.paste(a,(0,35));draw.text((18,a.height+47),'R21 / same occupied jack cells, physical pitch 17 x 14 mm',fill='#edece5');canvas.paste(b,(0,a.height+80));canvas.save(R/'studies/screenshot-comparison.png')
pdf=fitz.open(R/'panels/panel-1to1.pdf');p=pdf[0];mm=[p.rect.width*25.4/72,p.rect.height*25.4/72];p.get_pixmap(matrix=fitz.Matrix(1,1)).save(R/'reports/pdf-proof.png')
(R/'reports/pdf-check.json').write_text(json.dumps({'pages':len(pdf),'page_mm':mm,'expected_mm':[318,298],'pass':abs(mm[0]-318)<.02 and abs(mm[1]-298)<.02,'scope':'1:1 visual layout proof; not a drill or fabrication drawing'},indent=2))
print('Proofs written; PDF dimensions',mm)
