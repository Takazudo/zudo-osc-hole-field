"""Concrete nominal clamp solids; retention/material/fasteners are unqualified."""
import math
import numpy as np


def exit_proof(controls, start_direction, end_direction, wire_radius):
    """Bound finite-radius wire against its own flat-ended collet annulus.

    Near the exit a>=m*t, transverse rho<=M*t^2/2. If m^2>=r*M,
    a^2>=2*r*rho suffices for distance>=r to the entire annulus behind
    the exit plane. Beyond t0 the axial projection exceeds r monotonically.
    Both reflections and reversal preserve these bounds.
    """
    t0=.05;global_m=math.inf;m=math.inf;M=0.;axial=math.inf
    for original in controls:
        for p,w in [(original,start_direction),(original[::-1],-end_direction)]:
            q=3*np.diff(p,axis=0)
            restricted=np.array([q[0],(1-t0)*q[0]+t0*q[1],
                                 (1-t0)**2*q[0]+2*(1-t0)*t0*q[1]+t0*t0*q[2]])
            global_m=min(global_m,float((q@w).min()))
            m=min(m,float((restricted@w).min()))
            d0=6*(p[2]-2*p[1]+p[0]);d1=6*(p[3]-2*p[2]+p[1])
            for a in [d0,(1-t0)*d0+t0*d1]:
                M=max(M,float(np.linalg.norm(a-(a@w)*w)))
            pos=(1-t0)**3*p[0]+3*(1-t0)**2*t0*p[1]+3*(1-t0)*t0*t0*p[2]+t0**3*p[3]
            axial=min(axial,float((pos-p[0])@w))
    # Explicit floating arithmetic padding, same engineering scope as sweep.
    global_m-=1e-9;m-=1e-9;M+=1e-9;axial-=1e-9
    valid=global_m>0 and m>0 and m*m>=wire_radius*M and axial>wire_radius
    if not valid:raise ValueError('finite wire tube may intersect own collet annulus')
    return {'t0':t0,'global_axial_derivative_lower':global_m,
            'near_exit_axial_derivative_lower':m,'transverse_second_derivative_upper':M,
            'm_squared_minus_rM':m*m-wire_radius*M,'axial_at_t0_lower_mm':axial,
            'wire_radius_mm':wire_radius,'finite_tube_exclusion':True,
            'scope':'All g/h corner hulls, both ends and Y reflections; floating engineering bound, not formal roundoff certificate.'}


def assembly(coords, signs, anchors, direction, wire_radius):
    solids=[];collets=[]
    outer=1.7954
    for board,anchor,dx,zsign in [('KA',anchors['KA'],1,-1),('KB',anchors['KB'],-1,1)]:
        def global_point(p):
            # Input Z is local depth from face, positive into the inter-board gap.
            return np.array([p[0],p[1],anchor+zsign*(p[2]-1.5)])
        def solid(name,low,high,kind,owner=None):
            a,b=global_point(np.array(low)),global_point(np.array(high))
            obj={'id':board+'/'+name,'board':board,'kind':kind,'wire':owner,
                 'box':np.r_[np.minimum(a,b),np.maximum(a,b)].tolist()}
            solids.append(obj)
            return obj
        ends={}
        for i,(x,y) in enumerate(coords):
            if board=='KB':x+=52
            w=np.array([dx*direction[0],signs[i]*direction[1],-direction[2]])
            a=np.array([x,y,1.5]);c=a+1.375*w
            normal=(np.array([0,0,-1])+w[2]*w)/math.sqrt(1-w[2]**2)
            s=c+1.75*normal;e=np.array([s[0],s[1],.35])
            lo=np.minimum(a+.75*w,a+2*w)-outer
            hi=np.maximum(a+.75*w,a+2*w)+outer
            obj=solid(f'collet-{i+1}',lo,hi,'collet-capsule-bound',i)
            collets.append({'id':obj['id'],'wire':i+1,'board':board,
                            'axis_endpoints_xyz_mm':[global_point(a+.75*w).tolist(),global_point(a+2*w).tolist()],
                            'outer_radius_mm':outer,'bore_radius_nominal_mm':wire_radius,
                            'PCB_facing_stem_attachment_xyz_mm':global_point(s).tolist()})
            # Stem's square cross section is horizontal. Include .15 at both ends
            # as an explicit larger box, conservative for collision checking.
            solid(f'stem-{i+1}',np.minimum(s,e)-.15,np.maximum(s,e)+.15,'stem',i)
            d=e+np.array([dx*.5,0,0])
            solid(f'dogleg-{i+1}',np.minimum(e,d)-.2,np.maximum(e,d)+.2,'dogleg',i)
            rail_y=y+4
            solid(f'stub-{i+1}',[d[0]-.2,min(d[1],rail_y)-.2,.15],
                  [d[0]+.2,max(d[1],rail_y)+.2,.55],'stub',i)
            ends.setdefault(y,[]).append(d[0])
        for row,xs in ends.items():
            solid(f'rail-{row}',[-1.5,row+3.5,.15],[max(xs)+.2,row+4.5,.55],'rail')
    return {'type':'Twelve custom split collets, twelve stems/doglegs/stubs and four side-frame rails',
            'solids':solids,'collets':collets,
            'intentional_contacts':'Each own wire occupies its collet bore. Stem joins own collet; dogleg joins stem to stub; stub joins shared rail; rail ends at carrier interface X=-1.5. Each row is connected; the common frame connection and fasteners are unqualified.',
            'own_stem_analytic_wire_gap_mm':1.75-.15*np.linalg.norm(normal,ord=1)-wire_radius,
            'bare_PCB_capsule_clearance_mm':1.5+.75*(-direction[2])-outer,
            'bare_PCB_arm_clearance_mm':.15,
            'carrier_rule':'KA fixed; KB carrier/collets move with KB over 10 mm. Rails mount to independent side-frame/tray carriers, never to new PCB holes or solder joints.',
            'qualification':'Nominal collision envelopes only. Material, collet compression, retention, fasteners, stiffness, tolerance, insulation and assembly process remain unqualified; no orderable part selected.'}
