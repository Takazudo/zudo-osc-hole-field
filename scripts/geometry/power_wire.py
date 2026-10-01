"""Nominal wire reference curves; actual metal containment remains unqualified.

Each planar reference uses registered trial cuts, not independently staggered
strand endpoints. Geometry is shared by the loom screen and energy calculation.
"""
import math
from fractions import Fraction as F
from functools import lru_cache


@lru_cache(maxsize=1)
def pi_interval():
    """Machin identity with rational alternating-series remainder bounds."""
    def atan(q,n):
        total=sum((F((-1)**k,(2*k+1)*q**(2*k+1)) for k in range(n)),F())
        other=total+F((-1)**n,(2*n+1)*q**(2*n+1))
        return min(total,other),max(total,other)
    a,b=atan(5,20);c,d=atan(239,6)
    return 16*a-4*d,16*b-4*c


def sqrt_interval(value):
    scale=2**80
    root=math.isqrt(value.numerator*scale**2//value.denominator)
    lower=F(root,scale)
    return lower,lower if lower*lower==value else F(root+1,scale)


def directed(value,upper):
    result=float(value)
    if (F(result)<value if upper else F(result)>value):
        result=math.nextafter(result,math.inf if upper else -math.inf)
    return result


def finite(*values):
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
        raise ValueError('finite wire geometry required')


def curve_point(t,span,offset_y,bow_x=0.,profile='linear'):
    finite(t,span,offset_y,bow_x)
    if not 0<=t<=1 or span<=0 or profile not in ('linear','smoothstep'):
        raise ValueError('invalid wire curve')
    offset=t if profile=='linear' else t*t*(3-2*t)
    bow=math.sin(math.pi*t)**2
    return [bow_x*bow,offset_y*offset+10*bow,span*t]


def curve_bounds(span_lower,span_upper,offset_y,bow_x=0.,profile='linear'):
    finite(span_lower,span_upper,offset_y,bow_x)
    if not 0<span_lower<=span_upper or profile not in ('linear','smoothstep'):
        raise ValueError('invalid wire span/profile')
    smooth=profile=='smoothstep'
    lo,hi,dy,bx=map(F,(span_lower,span_upper,offset_y,bow_x))
    _,pi_hi=pi_interval();amplitude2=bx*bx+100
    _,amplitude_hi=sqrt_interval(amplitude2)
    # The mixed integral vanishes: offset derivative is symmetric about 1/2,
    # while sin(2*pi*t) is antisymmetric. Integral(smoothstep_prime²)=6/5.
    mean_derivative_square=(F(6,5) if smooth else 1)*dy**2+pi_hi**2*amplitude2/2
    second=2*pi_hi**2*amplitude_hi+(6*abs(dy) if smooth else 0)
    slope=(pi_hi*amplitude_hi+(F(3,2) if smooth else 1)*abs(dy))/lo
    _,length=sqrt_interval(hi**2+mean_derivative_square)
    return {'axis_length_upper_mm':directed(length,True),
        'slope_upper':directed(slope,True),
        'curvature_radius_lower_mm':directed(lo**2/second,False),
        'second_parameter_derivative_norm_upper_mm':directed(second,True),
        'axial_endpoint_tangents':smooth or offset_y==0}


def registered_endpoint(fan,adapter):
    """One explicit current-trial member, not a zero-tolerance real assembly.

    Actual metal must contain the registered reference supports/cores. The
    solder height is the fixed prism used by main_strand_trial, paid once.
    Arbitrary independently staggered roots are outside this construction.
    """
    heights=[fan[k] for k in ('initial_expansion_height_mm','main_fan_height_mm',
                              'redistribution_tip_height_mm','solder_height_upper_mm')]
    heights.append(adapter['arclength_mm'])
    finite(*heights)
    if min(heights)<=0:raise ValueError('positive solder/fan/adapter heights required')
    return {'axial_height_mm':math.fsum(heights),
        'axial_height_exact_mm':str(sum(map(F,heights),F())),
        'solder_trial_height_mm':heights[3],
        'adapter_tilt_deg':0.,'registered_trial_cuts':True,
        'scope':'Registered planar reference cores and fixed solder prisms; actual independent strand-end staggering and full-metal containment are NOT qualified.'}


def registered_route(source,board,index,fan,adapter,*,metal_radius):
    power=source['load_distribution'];branch=power['branches'][board]
    if branch.get('route_profile')!='registered-planar-smoothstep':
        raise ValueError('explicit registered-planar-smoothstep source required')
    cap=registered_endpoint(fan,adapter)
    front=-source['boards'][board]['face_z_mm']+source['boards'][board]['thickness_mm']
    rear=-source['boards']['K']['face_z_mm'];height=cap['axial_height_mm']
    # The already source-computed foil planes are the canonical numeric
    # inputs. All internal cuts share exact rational stage-height sums.
    exact_height=F(cap['axial_height_exact_mm'])
    start=F(front)+exact_height;end=F(rear)-exact_height
    exact_span=end-start;span=float(exact_span)
    span_lower=directed(exact_span,False);span_upper=directed(exact_span,True)
    x=branch['x_mm'][index];y=branch['pad_y_mm'];Y=branch['core_pad_y_mm'][index]
    bow_x=branch.get('bow_x_mm',0)
    if F(Y)-F(y)!=F(Y-y):
        raise ValueError('transverse endpoint difference is not exactly represented')
    if bow_x!=0 and Y-y!=0:raise ValueError('reference must be planar; endpoint roll not proved for a spatial curve')
    finite(metal_radius)
    if metal_radius<=0:raise ValueError('positive full-metal radius required')
    limits=curve_bounds(span_lower,span_upper,Y-y,bow_x,profile='smoothstep')
    bulk=[]
    for i in range(101):
        dx,dy,dz=curve_point(i/100,span,Y-y,bow_x,profile='smoothstep')
        bulk.append([x+dx,y+dy,float(start+exact_span*F(i,100))])
    half=branch['endpoint_metal_half_extent_mm']
    finite(half)
    if half<max(max(power['factory_solder_pad_mm'])/2,metal_radius):
        raise ValueError('endpoint metal reservation cannot shrink below the full solder land or bulk metal')
    caps=[[x-half,y-half,front,x+half,y+half,directed(start,True)],
          [x-half,Y-half,directed(end,False),x+half,Y+half,rear]]
    datums={k:str(v) for k,v in {'foil_front':F(front),'foil_rear':F(rear),
        'endpoint_height':exact_height,'bulk_front':start,'bulk_rear':end,
        'bulk_span':exact_span}.items()}
    stage_heights=[('solder',F(fan['solder_height_upper_mm'])),
        ('tip',F(fan['redistribution_tip_height_mm'])),
        ('main_fan',F(fan['main_fan_height_mm'])),
        ('expansion',F(fan['initial_expansion_height_mm'])),
        ('adapter',F(adapter['arclength_mm']))]
    stage_cuts=[]
    for foil,sign,target in ((F(front),1,start),(F(rear),-1,end)):
        cuts={'foil':str(foil)};position=foil
        for name,stage_height in stage_heights:
            position+=sign*stage_height;cuts[name]=str(position)
        if position!=target:raise ValueError('endpoint and bulk rational cuts disagree')
        stage_cuts.append(cuts)
    residuals=[abs(F(span)-exact_span),abs(F(height)-exact_height),
        abs(F(float(start))-start),abs(F(float(end))-end)]
    residuals.extend(abs(F(p[2])-(start+exact_span*F(i,100))) for i,p in enumerate(bulk))
    roundoff=max(residuals)
    if roundoff>F(1e-9):raise ValueError('preview axial rounding exceeds reserved sampling allowance')
    chord=directed(F(limits['second_parameter_derivative_norm_upper_mm'])/(8*100**2)+F(1e-9),True)
    return {'profile':branch['route_profile'],'board':board,'wire_label':power['wire_labels'][index],
        'bulk_metal_radius_mm':metal_radius,'endpoint_reference':cap,
        'bulk_points_mm_positive_rear':bulk,'points_mm_positive_rear':[[x,y,front]]+bulk+[[x,Y,rear]],
        'endpoint_reservations_mm_positive_rear':caps,
        'bulk_span_mm':span,'bulk_span_lower_mm':span_lower,'bulk_span_upper_mm':span_upper,
        'exact_axial_datums_mm':datums,'exact_endpoint_stage_cuts_mm':stage_cuts,
        'preview_axial_roundoff_upper_mm':directed(roundoff,True),'bulk_curve_bounds':limits,
        'continuous_centreline_length_upper_mm':directed(F(limits['axis_length_upper_mm'])+2*exact_height,True),
        'bulk_chord_error_upper_mm':chord,
        'physical_containment':'OPEN: actual full metal must remain inside both cap volumes and bulk tube; reference current cores must be contained. No manufactured fit or material admission.'}
