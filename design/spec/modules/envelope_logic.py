"""G07 proposal, frozen before capture: synchronous, retrigger from current level.

Bool expressions are the single source for NAND capture and behavioural SPICE.
State is one-hot RISE/HOLD/FALL; all zero is IDLE. START has priority.
"""
INSTANCES=tuple(f'E{i}' for i in range(1,7))

def NOT(a):return ('not',a)
def AND(*a):return ('and',*a)
def OR(*a):return ('or',*a)
IDLE=NOT(OR('RISE','HOLD','FALL'))
START=OR(AND('GATE',NOT('GATE_PREV')),AND('LOOP',IDLE,NOT('EOC')))
SUSTAIN=AND('ASR','GATE')
EXPRESSIONS={
 'IDLE':IDLE,
 'START':START,
 'D_RISE':OR('START',AND('RISE',NOT('TOP'),OR(NOT('ASR'),'GATE'))),
 'D_HOLD':AND(NOT('START'),'ASR','GATE',OR('HOLD',AND('RISE','TOP'))),
 'D_FALL':AND(NOT('START'),OR(AND('FALL',NOT('BOTTOM')),AND('RISE',OR(AND('TOP',NOT(SUSTAIN)),AND('ASR',NOT('GATE')))),AND('HOLD',NOT(SUSTAIN)))),
 'D_COMPLETE':AND('READY','FALL','BOTTOM',NOT('START')),
 'STAGE_HIGH':OR(AND('STAGE_FALL','FALL'),AND(NOT('STAGE_FALL'),'RISE')),
 'RESET_CAP':OR(NOT('READY'),'IDLE',AND('FALL','BOTTOM_RAW')),
 'HOLD_ENABLE':OR('HOLD',AND('RISE','TOP_RAW')),
 'RISE_LINEAR':AND('READY','RISE',NOT('CURVED')),
 'RISE_CURVE':AND('READY','RISE','CURVED'),
 'FALL_LINEAR':AND('READY','FALL',NOT('CURVED')),
 'FALL_CURVE':AND('READY','FALL','CURVED'),
}

def evaluate(expr,signals):
 if isinstance(expr,str):return bool(signals[expr])
 op,*args=expr;v=[evaluate(x,signals) for x in args]
 return not v[0] if op=='not' else all(v) if op=='and' else any(v)

def tick(state,*,gate,previous,asr,loop,top,bottom,eoc=False):
 values=dict(RISE=state=='rise',HOLD=state=='sustain',FALL=state=='fall',GATE=gate,GATE_PREV=previous,ASR=asr,LOOP=loop,TOP=top,BOTTOM=bottom,EOC=eoc,READY=True)
 for k in ('IDLE','START','D_RISE','D_HOLD','D_FALL'):values[k]=evaluate(EXPRESSIONS[k],values)
 outputs=[n for n,k in [('rise','D_RISE'),('sustain','D_HOLD'),('fall','D_FALL')] if values[k]]
 assert len(outputs)<=1,values
 return outputs[0] if outputs else 'idle'

TRUTH_TABLE=[
 {'mode':mode,'state':state,'rising_edge':'rise from present level; no capacitor reset','falling_edge':('fall from present level' if mode=='ASR' and state in ('rise','sustain') else 'no state change'),'no_edge':('auto-start after EOC ends' if mode=='LOOP' and state=='idle' else 'top -> sustain' if mode=='ASR' and state=='rise' else 'top -> fall' if state=='rise' else 'bottom -> idle plus EOC' if state=='fall' else 'hold while gate high' if state=='sustain' and mode=='ASR' else 'sustain -> fall' if state=='sustain' else 'remain idle')}
 for mode in ('ASR','AR','LOOP') for state in ('idle','rise','sustain','fall')]


def captured_logic(parts):
 """Recover canonical NAND/FF terminals from packed physical pin numbers."""
 gates=[];flops=[]
 nand=[('1','2','3'),('4','5','6'),('9','10','8'),('12','13','11')]
 ff=[('2','3','1','5','6'),('12','11','13','9','8')]
 for p in parts:
  if p.symbol.endswith('SN74HC00DR') and p.unit<=4:
   a,b,z=(p.pins[k] for k in nand[p.unit-1])
   if z is not None:gates.append((p.key,a,b,z))
  if p.symbol.endswith('SN74HC74DR') and p.unit<=2:
   d,clk,clr,q,qn=(p.pins[k] for k in ff[p.unit-1])
   if q is not None or qn is not None:flops.append((p.key,d,clk,clr,q,qn))
 return gates,flops
