#!/usr/bin/env python3
"""Transcribe the user grid once; derive every view from integer cells.
No manufacturing dimensions are inferred from screenshot pixels.
"""
from pathlib import Path
import json,copy,hashlib
R=Path(__file__).resolve().parents[1]
old=json.loads((R/'reference/panel.json').read_text())
ports=[]; controls=[];groups=[];blocks={}
old_ports={p['id']:p for p in old['ports']};old_controls={p['id']:p for p in old['controls']}
def block(b,f,name):blocks[b]={'id':b,'family':f,'name':name}
def group(b,field,c,r,w,h):groups.append(dict(block=b,field=field,col=c,row=r,cols=w,rows=h))
def port(b,key,label,c,r,d='in',accent=False,led=True,clip=False):
 p=dict(uid=f'J:{b}.{key}',id=f'{b}.{key}',block=b,key=key,label=label,col=c,row=r,field='jacks',kind='jack',direction=d,accent=accent,led=led,clip=clip,nut_diameter_mm=8.3,plug_diameter_mm=9.6,component='qingpu-wqp518ma',geometry_status='Nut and full footprint unqualified; 8.3 mm is a retained trial envelope.')
 ports.append(p)
 return p
def control(b,key,label,c,r,kind='pot',accent=False,positions=None):
 prev=old_controls.get(f'{b}.{key}',{})
 part='bourns-ptv09a-4020f-b103'
 if kind=='switch':part='dailywell-2ms1' if len(positions)==2 else 'dailywell-2ms3'
 if kind=='button':part='omron-b3f1020'
 if kind=='octave':part='alps-srbv160803'
 p=dict(uid=f'C:{b}.{key}',id=f'{b}.{key}',block=b,key=key,label=label,col=c,row=r,field='controls',kind=kind,accent=accent,component=part,diameter_mm=8 if kind=='octave' else 5 if kind=='button' else 6)
 if positions:p['positions']=positions
 if b.startswith('E') and key in ['RISE','FALL']:p['stage']=key.lower()
 controls.append(p);return p
# Screenshot: 18 columns by 10 occupied rows, zero-indexed here.
for i in range(5):
 b=f'O{i+1}';block(b,'OSC',f'OSC {i+1}');group(b,'jacks',i,0,1,8);group(b,'controls',i,0,1,8)
 for r,(key,label) in enumerate([('1V','1V/OCT'),('FM','FM'),('PWM','PWM'),('SYNC','SYNC CV'),('SIN','SIN'),('TRI','TRI'),('SAW','SAW'),('PUL','PUL')]):port(b,key,label,i,r,'in' if r<4 else 'out',r==0 or r>=4,False)
 for r,(key,label,kind,ac,states) in enumerate([('OCT','OCT','octave',True,[-2,-1,0,1,2,3]),('VCO/LFO','RANGE','switch',False,['LFO','VCO']),('SYNC','SYNC','switch',False,['SOFT','OFF','HARD']),('TUNE','TUNE','pot',False,None),('FINE','FINE','pot',False,None),('FM±','FM ±','pot',False,None),('PW','PW','pot',False,None),('PWM±','PWM ±','pot',False,None)]):control(b,key,label,i,r,kind,ac,states)
for i in range(3):
 b=f'F{i+1}';c=5+i;block(b,'VCF',f'FILTER {i+1}');group(b,'jacks',c,0,1,8);group(b,'controls',c,0,1,6)
 for r,(key,label) in enumerate([('IN','IN'),('FREQ','FREQ CV'),('RES','RES CV'),('GAIN','GAIN CV'),('LP','LP'),('BP','BP'),('HP','HP'),('OUT','OUT')]):port(b,key,label,c,r,'in' if r<4 else 'out',r==0 or r>=4,r<4)
 for r,key in enumerate(['FREQ','RES','FREQ±','RES±','GAIN','GAIN±']):control(b,key,key,c,r,accent=key in ['FREQ','GAIN'])
for c,b in enumerate(['M5A','M5B','M4A','M4B'],8):
 is5=b.startswith('M5');n=5 if is5 else 4;block(b,'MIX5' if is5 else 'MIX4',f'MIX{n} {b[-1]}');group(b,'jacks',c,0,1,6);group(b,'controls',c,0,1,6)
 for r in range(n):port(b,str(r+1),str(r+1),c,r,accent=True);control(b,f'{r+1}±',f'{r+1} ±',c,r)
 if not is5:port(b,'ATTEN','ATTEN',c,4,accent=False);control(b,'CV±','CV ±',c,4,accent=True)
 port(b,'SUM','SUM',c,5,'out',True,True,True);control(b,'LEVEL','LEVEL' if is5 else 'SUM GAIN',c,5,accent=True)
# Preserve the user's explicit FOLD 2 (left), FOLD 1 (right) order.
for i,c in [(2,8),(1,10)]:
 b=f'W{i}';block(b,'FOLD',f'FOLD {i}');group(b,'jacks',c,6,2,2);group(b,'controls',c,6,2,2)
 for key,label,cc,rr,d in [('IN','IN',c,6,'in'),('FOLD','FOLD CV',c+1,6,'in'),('BIAS','BIAS CV',c,7,'in'),('OUT','OUT',c+1,7,'out')]:port(b,key,label,cc,rr,d,key in ['IN','OUT'],d=='in')
 for key,label,cc,rr in [('FOLD','FOLD',c,6),('FOLD±','FOLD ±',c+1,6),('BIAS','BIAS',c,7),('LEVEL','LEVEL',c+1,7)]:control(b,key,label,cc,rr,accent=key in ['FOLD','LEVEL'])
for i in range(6):
 c=12+i;b=f'E{i+1}';a=f'A{i+1:02}';block(b,'AR',f'ENV {i+1}');block(a,'AO',f'OFFSET {i+1}');group(b,'jacks',c,0,1,7);group(b,'controls',c,0,1,6);group(a,'jacks',c,7,1,3);group(a,'controls',c,6,1,2)
 for r,(key,label) in enumerate([('SIG','SIG'),('RISE','RISE'),('FALL','FALL'),('ENV','ENV'),('BIP','BIP'),('EOC','EOC'),('STG','STG')]):port(b,key,label,c,r,'in' if r<3 else 'out',r in [0,3,4],r<3)
 for r,(key,kind,states) in enumerate([('MODE','switch',['ASR','AR','LOOP']),('SHAPE','switch',['LINEAR','CURVED']),('STAGE','switch',['RISE','FALL']),('TRIG','button',None),('RISE','pot',None),('FALL','pot',None)]):control(b,key,key,c,r,kind,key in ['RISE','FALL'],states)
 for r,key in enumerate(['IN','OFFSET','OUT'],7):port(a,key,key,c,r,'out' if key=='OUT' else 'in',key!='OFFSET',True,key=='OUT')
 control(a,'ATTEN','ATTEN ±',c,6,accent=True);control(a,'OFFSET','OFFSET',c,7)
for i,c in [(1,0),(2,2)]:
 b=f'B{i}';block(b,'MULT',f'MULT {i}');group(b,'jacks',c,8,2,2)
 for key,label,cc,rr,d in [('IN','IN',c,8,'in'),('1','1',c+1,8,'out'),('2','2',c,9,'out'),('3','3',c+1,9,'out')]:port(b,key,label,cc,rr,d,key=='IN',key=='IN')
for i,r in [(1,8),(2,9)]:
 b=f'H{i}';block(b,'SH',f'S&H {i}');group(b,'jacks',4,r,3,1)
 for c,key,d in [(4,'TRIGGER','in'),(5,'IN','in'),(6,'OUT','out')]:port(b,key,key,c,r,d,True,True)
 # Preserve SAMPLE/A-B cells. Add one SLEW knob per channel in column 7.
 group(b,'controls',5+i-1,6,1,1);control(b,'SAMPLE','SAMPLE',5+i-1,6,'button',True)
 group(b,'controls',7,5+i,1,1)
 q=control(b,'SLEW','SLEW',7,5+i,'pot',True);q['component']='bourns-ptv09a-4020f-b504';q['default_value']=0.0
 b=f'X{i}';block(b,'SWITCH',f'SWITCH {i}');group(b,'jacks',7,r,3,1)
 for c,key,d in [(7,'IN-A','in'),(8,'IN-B','in'),(9,'OUT','out')]:port(b,key,key,c,r,d,True,True)
 group(b,'controls',5+i-1,7,1,1);control(b,'SELECT','A / B',5+i-1,7,'switch',False,['A','B'])
b='N1';block(b,'NOISE','Noise');group(b,'jacks',10,8,2,2)
for key,c,r in [('WHITE',10,8),('PINK',11,8),('BLUE',10,9),('BROWN',11,9)]:port(b,key,key,c,r,'out',True,False)
model=dict(schema_version=1,revision='R21',title='zudo-osc-hole-field',source='reference/user-jack-grid.png',columns=18,jack_rows=10,control_rows=8,ports=ports,controls=controls,groups=groups,blocks=blocks,presets={'compact':{'px':17,'py':14,'label':'Compact orthogonal grid'},'square':{'px':17,'py':17,'label':'Square-cell reference'}},default_preset='compact',no_interblock_normals=True,construction_note='Different interface PCB depths; all electrical joints factory soldered. Board planes and component envelopes remain pre-CAD assumptions.')
assert len(ports)==180 and len(controls)==144
assert len({(p['col'],p['row']) for p in ports})==180
assert {(p['col'],p['row']) for p in ports}=={(c,r) for c in range(18) for r in range(10)}
assert len({(p['col'],p['row']) for p in controls})==144
(R/'layout/grid.json').write_text(json.dumps(model,ensure_ascii=False,indent=2))
baseline=json.loads((R/'reference/r20-grid.json').read_text())
prior={q['uid']:q for q in baseline['controls']}
assert all(q==prior[q['uid']] for q in controls if q['uid'] in prior)
assert ports==baseline['ports']
(R/'layout/changes.json').write_text(json.dumps({'baseline':'R20 original grid, retained byte copy in reference/r20-grid.json','revision':'R21','unchanged_jacks':180,'unchanged_controls':142,'added_controls':[q for q in controls if q['uid'] not in prior],'removed_controls':[],'new_jacks':[],'notes':['Only H1.SLEW and H2.SLEW added in the two empty control cells.','No default noise connections, bypass switches, new CV inputs or extra output jacks.','RC glide values are prototype proposals; not ADDAC215 circuit or performance claims.'],'counts':{'jacks':len(ports),'pots':sum(x['kind']=='pot' for x in controls),'octave':5,'toggles':sum(x['kind']=='switch' for x in controls),'buttons':sum(x['kind']=='button' for x in controls),'magnitude_leds':sum(x['led'] for x in ports),'clip_leds':sum(x['clip'] for x in ports),'stage_leds':12}},indent=2))
print((R/'layout/changes.json').read_text())
