"""Bounded ideal integrator/comparator and captured NAND/DFF behavioural model.

No vendor OTA, analog switch, opamp, RC oscillator, converter or HC221 dynamics.
The EOC hold-time fixture tracks completion for one state-clock interval; thus
its pulse is nominal width plus up to one clock, not the physical HC221 model.
"""
import hashlib,json,math,subprocess
from pathlib import Path
from design.spec.modules.envelope import ROOT,family
from design.spec.modules.envelope_logic import captured_logic
DIR=ROOT/'design/spec/modules/spice'
CACHE=ROOT/'.circuit-cache/envelope-spice'
OUT=ROOT/'design/reports/spice/envelope.json'
CAP=100e-9;ATTEN=1/900;WIDTH=.7*47000*100e-9;IBIAS=500e-6

def node(x):return {'AGND':'0','+5V':'VCC'}.get(x,x or 'NC')

def common(mode,curved,scenario='normal'):
 f=family();gates,flops=captured_logic(f.parts)
 lines=['* Actual packed NAND and DFF pin graph; analogue boundary is ideal.', '.param ibias=500u', 'VVCC VCC 0 5','VCLOCK CLOCK 0 PULSE(0 5 25u 1n 1n 24.999u 50u)','VRESET RESET_N 0 PWL(0 0 5m 0 5.001m 5)',f'VASR ASR_RAW 0 {5 if mode=="ASR" else 0}',f'VLOOP LOOP_RAW 0 {5 if mode=="LOOP" else 0}',f'VSHAPE CURVED 0 {5 if curved else 0}','VSTAGE STAGE_FALL 0 0','VBUTTON TRIG_ACTIVE 0 0']
 if scenario=='early-release':sig='PWL(0 0 10m 0 10.001m 5 13m 5 13.001m 0)'
 elif scenario=='retrigger':sig='PWL(0 0 10m 0 10.001m 5 12m 5 12.001m 0 38m 0 38.001m 5 40m 5 40.001m 0)'
 else:sig='PWL(0 0 10m 0 10.001m 5 55m 5 55.001m 0)'
 lines.append('VSIG SIG_GATE 0 '+sig)
 for index,(_,a,b,z) in enumerate(gates):lines.append(f'BN{index} {node(z)} 0 V=5*(1-(v({node(a)})>2.5)*(v({node(b)})>2.5))')
 lines+=['.subckt EDGE_FF D CLK CLR Q QN','BNCLK NC 0 V=5-v(CLK)','BDATA DATA 0 V=(v(CLR)>2.5 ? v(D) : 0)','SM DATA M NC 0 SWLOG','CM M 0 10p IC=0','BM MB 0 V=v(M)','SS MB S CLK 0 SWLOG','CS S 0 10p IC=0','BQ Q 0 V=(v(CLR)>2.5 ? (v(S)>2.5 ? 5 : 0) : 0)','BQN QN 0 V=5-v(Q)','.ends EDGE_FF','.model SWLOG SW(Ron=100 Roff=1e15 Vt=2.5 Vh=.1)']
 for index,(_,d,clk,clr,q,qn) in enumerate(flops):lines.append(f'XFF{index} {node(d)} {node(clk)} {node(clr)} {node(q) if q else "NCQ"+str(index)} {node(qn) if qn else "NCFF"+str(index)} EDGE_FF')
 lines+=['BENV ENV_BUFFER 0 V=v(ENV_STORAGE)','SCT VCC TOP_STATE ENV_BUFFER 0 CMP_TOP','RCT TOP_STATE 0 10k','BTOP TOP_RAW 0 V=(v(TOP_STATE)>2.5 ? 5 : 0)','BINVERT ENV_NEG 0 V=-v(ENV_BUFFER)','SCB VCC BOTTOM_STATE ENV_NEG 0 CMP_BOTTOM','RCB BOTTOM_STATE 0 10k','BBOTTOM BOTTOM_RAW 0 V=(v(BOTTOM_STATE)>2.5 ? 5 : 0)','.model CMP_TOP SW(Ron=1 Roff=1e15 Vt=7.93564356436 Vh=.02475247525)','.model CMP_BOTTOM SW(Ron=1 Roff=1e15 Vt=-.075 Vh=.025)',f'CENV ENV_STORAGE 0 {CAP} IC=0',
 'BRISE 0 RISE_CURRENT I=19.2*ibias*(v(RISE_LINEAR)>2.5 ? 9/900 : (v(RISE_CURVE)>2.5 ? (9-v(ENV_BUFFER))/900 : 0))',
 'BFALL FALL_CURRENT 0 I=19.2*ibias*(v(FALL_LINEAR)>2.5 ? 9/900 : (v(FALL_CURVE)>2.5 ? (v(ENV_BUFFER)+1)/900 : 0))',
 'RRISE RISE_CURRENT ENV_STORAGE 100','RFALL FALL_CURRENT ENV_STORAGE 100',
 'VPEAK PEAK 0 8','SHOLD PEAK HC HOLD_ENABLE 0 SWLOG','RHOLD HC ENV_STORAGE 100','SIDLE ENV_STORAGE IC RESET_CAP 0 SWLOG','RIDLE IC 0 100',
 'BTIME NOW 0 V=time','SLAST NOW LAST COMPLETE 0 SWLOG','CLAST LAST 0 10p IC=0',f'BEOC EOC 0 V=(v(READY)>2.5 && v(LAST)>.01 && time-v(LAST)<{WIDTH} ? 5 : 0)',
 'BBIP BIP 0 V=1.25*v(ENV_BUFFER)-5',
 'BRISE_LED RISE_LED 0 V=(v(RISE)>2.5 ? max(v(ENV_BUFFER),0)/16 : 0)','BFALL_LED FALL_LED 0 V=(v(FALL)>2.5 ? max(v(ENV_BUFFER),0)/16 : 0)',
 '* LED proxy volts correspond to current across the 1k sense resistor.']
 return '\n'.join(lines)+'\n'

def crossings(rows,col):
 return [rows[i][0] for i in range(1,len(rows)) if rows[i-1][col]<2.5<=rows[i][col]]

def run(mode,curved,scenario='normal'):
 stem='envelope-'+mode.lower()+'-'+('curved' if curved else 'linear')+'-'+scenario
 p=DIR/(stem+'.cir');data=CACHE/(stem+'.txt')
 p.write_text('Envelope model only: '+stem+'\n'+common(mode,curved,scenario)+f'.control\nset wr_singlescale\nset wr_vecnames\ntran 5u 120m uic\nwrdata {data.relative_to(ROOT)} v(ENV_BUFFER) v(RISE) v(HOLD) v(FALL) v(EOC) v(BIP) v(STAGE_HIGH) v(RISE_LED) v(FALL_LED)\nquit\n.endc\n.end\n')
 result=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(p.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
 (CACHE/(stem+'.log')).write_text(result.stdout+'\n'+result.stderr)
 if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
 rows=[[float(v) for v in l.split()] for l in data.read_text().splitlines()[1:]]
 assert all(math.isfinite(v) for r in rows for v in r)
 assert min(r[1] for r in rows)>-.025 and max(r[1] for r in rows)<8.1
 assert all(sum(r[k]>2.5 for k in (2,3,4))<=1 for r in rows)
 starts=crossings(rows,2);falls=crossings(rows,4);eocs=crossings(rows,5)
 assert starts and falls and eocs,(stem,starts,falls,eocs)
 durations=[]
 for a in starts:
  end=next((r[0] for r in rows if r[0]>a+1e-6 and r[2]<2.5),None)
  if end:durations.append(end-a)
 gm=19.2*IBIAS
 expect_rise=CAP/gm/ATTEN*(math.log(9/(9-804/101)) if curved else (804/101)/9)
 expect_fall=CAP/gm/ATTEN*(math.log(9/1.05) if curved else 7.95/9)
 if scenario=='normal':
  assert abs(durations[0]/expect_rise-1)<.03,(stem,durations[0],expect_rise)
  actual_fall=eocs[0]-falls[0]
  assert abs(actual_fall/expect_fall-1)<.03,(stem,actual_fall,expect_fall)
  if mode=='ASR':assert max(r[3] for r in rows if .04<r[0]<.05)>4.9
  if mode=='LOOP':assert len(starts)>=2,(stem,starts)
  for r in rows:
   assert abs(r[6]-(1.25*r[1]-5))<1e-5
   assert (r[7]>2.5)==(r[2]>2.5)
   assert abs(r[8])<1e-8 if r[2]<2.5 else True
   assert abs(r[9])<1e-8 if r[4]<2.5 else True
 elif scenario=='early-release':
  assert .0129<falls[0]<.0133,(stem,falls)
  assert max(r[1] for r in rows)<4,(stem,max(r[1] for r in rows))
 else:
  assert len(starts)>=2,(stem,starts)
  retrigger=starts[1]
  before=min(rows,key=lambda r:abs(r[0]-(retrigger-1e-6)))[1]
  after=min(rows,key=lambda r:abs(r[0]-(retrigger+1e-6)))[1]
  assert before>.2 and abs(after-before)<.05,(stem,before,after)
  assert eocs[0]>retrigger,(stem,eocs,retrigger)
 first=eocs[0];off=next(r[0] for r in rows if r[0]>first+1e-6 and r[5]<2.5)
 assert abs((off-first)-WIDTH)<.0001,(stem,off-first)
 report={'deck':str(p.relative_to(ROOT)),'mode':mode,'shape':'CURVED' if curved else 'LINEAR','scenario':scenario,'status':'PASS - ideal/behavioural model only','OTA_bias_fixture_A':IBIAS,'expected_full_rise_s':expect_rise,'expected_full_fall_s':expect_fall,'first_rise_s':durations[0],'first_fall_to_EOC_s':eocs[0]-falls[0],'first_EOC_width_s':off-first,'peak_V':max(r[1] for r in rows),'rise_starts_s':starts,'fall_starts_s':falls,'EOC_starts_s':eocs}
 print(stem,'PASS',report['first_rise_s'],report['first_fall_to_EOC_s'])
 return report

def main():
 CACHE.mkdir(parents=True,exist_ok=True)
 runs=[run(mode,shape) for mode in ('ASR','AR','LOOP') for shape in (False,True)]
 runs.extend([run('ASR',False,'early-release'),run('AR',True,'retrigger')])
 report={'schema_version':1,'module':'envelope','authority':'PROPOSAL (planning, owner-delegated)','oracle':'KiCad 10.0.6 pinned wrapper ngspice','status':'PASS - bounded model only','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'design/spec/modules/envelope.py',ROOT/'design/spec/modules/io_partition.py',ROOT/'design/spec/modules/envelope_logic.py',Path(__file__).resolve()]},'runs':runs,'limitations':['Ideal OTA gm=19.2*IABC, ideal amplifier/analogue switches/comparators; no device spread, offset or leakage.','Actual packed NAND/DFF graph is exercised with behavioural gates and master/slave latches; no HC propagation or metastability claim.','Clock fixed at50us, reset asserted until5ms, converter current imposed500uA; physical RC oscillator/reset, transistor converters and power sequencing NOT RUN.','EOC timing tracks completion for one state clock then adds0.7RC; actual HC221 non-retriggerability and coefficient/corners NOT RUN.','Real output protection/loading, diode clamps, noise, rail current, PCB/harness and bench behavior NOT RUN.']}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
