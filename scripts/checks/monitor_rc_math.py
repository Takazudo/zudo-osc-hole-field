"""Exact linear RC reference for prescribed GOOD_FAST waveforms, not IC models."""
import bisect
import math


def parameters(r1,r2,cap,pin_cap):
    if any(isinstance(v,bool) or not math.isfinite(v) for v in (r1,r2,cap,pin_cap)):
        raise ValueError('finite RC parameters required')
    if min(r1,r2,cap)<=0 or pin_cap<0:
        raise ValueError('positive resistance/capacitance and nonnegative pin capacitance required')


def advance(state,u0,u1,dt,r1,r2,cap,pin_cap):
    """Advance both nodes under a linear input ramp, including finite edges."""
    parameters(r1,r2,cap,pin_cap)
    if len(state)!=2 or any(not math.isfinite(v) for v in (*state,u0,u1)):
        raise ValueError('finite two-node state and drive required')
    if dt<0 or not math.isfinite(dt): raise ValueError('invalid time interval')
    if dt==0:return tuple(state)
    slope=(u1-u0)/dt
    if pin_cap==0:
        tau=r1*cap;e=math.expm1(-dt/tau)
        value=state[0]+(state[0]-u0)*e+slope*(dt+tau*e)
        return value,value
    a=-(1/r1+1/r2)/cap;b=1/(r2*cap);c=1/(r2*pin_cap);d=-c
    determinant=1/(r1*r2*cap*pin_cap)
    fast=(a+d-math.sqrt((a-d)**2+4*b*c))/2
    slow=determinant/fast
    z0=-r1*(cap+pin_cap)*slope;z1=z0-r2*pin_cap*slope
    w0=state[0]-u0-z0;w1=state[1]-u0-z1
    c0=((a-fast)*w0+b*w1)/(slow-fast)
    c1=(c*w0+(d-fast)*w1)/(slow-fast)
    es=math.expm1(slow*dt);ef=math.expm1(fast*dt)
    return (state[0]+slope*dt+c0*es+(w0-c0)*ef,
            state[1]+slope*dt+c1*es+(w1-c1)*ef)


class Trajectory:
    def __init__(self,points,initial,r1,r2,cap,pin_cap):
        parameters(r1,r2,cap,pin_cap)
        if any(len(p)!=2 or not all(math.isfinite(v) for v in p) for p in points):
            raise ValueError('finite waveform points required')
        if len(points)<2 or points[0][0]!=0 or any(b[0]<=a[0] for a,b in zip(points,points[1:])):
            raise ValueError('strictly increasing waveform from t=0 required')
        self.points=points;self.times=[p[0] for p in points]
        self.rc=(r1,r2,cap,pin_cap);self.states=[tuple(initial)]
        for (t0,u0),(t1,u1) in zip(points,points[1:]):
            self.states.append(advance(self.states[-1],u0,u1,t1-t0,*self.rc))

    def value(self,time):
        if time<0 or time>self.times[-1]+1e-15:raise ValueError('time outside forcing history')
        i=min(bisect.bisect_right(self.times,time)-1,len(self.points)-2)
        t0,u0=self.points[i];t1,u1=self.points[i+1]
        value=u0+(u1-u0)*(time-t0)/(t1-t0)
        return advance(self.states[i],u0,value,time-t0,*self.rc)


def observer(rows,high,low,initial):
    """Ideal hysteretic observer; brackets are sampled crossings, not latch timing."""
    if not 0<low<high:raise ValueError('ordered positive observer thresholds required')
    state=initial;events=[]
    for before,after in zip(rows,rows[1:]):
        threshold=low if state else high
        crossed=(before[2]>threshold>=after[2]) if state else (before[2]<threshold<=after[2])
        if crossed:
            fraction=(threshold-before[2])/(after[2]-before[2])
            events.append({'transition':'fall_low' if state else 'rise_high',
                           'bracket_s':[before[0],after[0]],
                           'linear_interpolation_s':before[0]+fraction*(after[0]-before[0])})
            state=not state
    return {'initial':initial,'final':state,'crossings':events}


def integrate(rows,index):
    return sum((b[0]-a[0])*(a[index]+b[index])/2 for a,b in zip(rows,rows[1:]))
