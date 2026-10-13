"""Authored geometry only. Import/build permitted only after design review.
Primitives use exact oriented boxes/cylinders and named boolean subtractions.
No native, file reads/writes, collision calculation or placement search.
"""
import math

def add(a,b): return [x+y for x,y in zip(a,b)]
def mul(a,s): return [x*s for x in a]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def norm(a):return math.sqrt(sum(x*x for x in a))
def unit(a):return mul(a,1/norm(a))
E=[[1.,0,0],[0,1.,0],[0,0,1.]]

def primitive_vertices(obj,inner=False):
 """Conservative outer cylinders / inscribed negative bores,64 facets."""
 if obj['shape']=='oriented_box':
  C=obj['center_xyz_mm'];A=obj['axes_xyz'];H=obj['half_extents_mm'];out=[]
  for i in (-1,1):
   for j in (-1,1):
    for k in (-1,1):
     q=C[:]
     for ax,h,sgn in zip(A,H,[i,j,k]):q=add(q,mul(ax,h*sgn))
     out.append(q)
  return out
 a,b=obj['axis_endpoints_xyz_mm'];w=unit(add(b,mul(a,-1)));ref=[1.,0,0] if abs(w[0])<.8 else [0,1.,0];u=unit(cross(w,ref));v=cross(w,u);r=obj['radius_mm']/(1 if inner else math.cos(math.pi/64));out=[]
 for c in (a,b):
  for j in range(64):
   t=2*math.pi*j/64;out.append(add(c,add(mul(u,r*math.cos(t)),mul(v,r*math.sin(t)))))
 return out

def common_format(solids,cuts):
 lookup={x['id']:x for x in solids+cuts}
 for obj in solids:
  obj['vertices_xyz_mm']=primitive_vertices(obj)
  obj['holes']=[{'id':lookup[k]['id'],'kind':lookup[k]['kind'],'wire':lookup[k].get('wire'),'shape':lookup[k]['shape'],'vertices_xyz_mm':primitive_vertices(lookup[k],inner=True),'analytic_primitive':{a:b for a,b in lookup[k].items() if a not in ['vertices_xyz_mm','holes','subtract']}} for k in obj['subtract']]
  obj['polyhedral_scope']='Outer64facet circumscribed cylinder; negativebores inscribed. Retain exact analyticalprimitive for ownwirebore/contact handling.'
 return solids

def build(travel_mm=0.):
 if not 0<=travel_mm<=10.1:raise ValueError('fixed admitted service domain')
 solids=[];cuts=[];joints=[];terminations=[]
 for board,face,normal in [('KA',-101.6,-1),('KB',-126.-travel_mm,1)]:
  prefix=board+'/'
  def point(p):return [p[0],p[1],face+normal*p[2]]
  def vector(v):return [v[0],v[1],normal*v[2]]
  def box(name,origin,axes,lo,hi,kind,owner=None,cut=False):
   center=origin[:]
   for ax,l,h in zip(axes,lo,hi):center=add(center,mul(ax,(l+h)/2))
   obj={'id':prefix+name,'board':board,'shape':'oriented_box','center_xyz_mm':point(center),'axes_xyz':[vector(a) for a in axes],'half_extents_mm':[(h-l)/2 for l,h in zip(lo,hi)],'kind':kind,'wire':owner,'subtract':[]}
   (cuts if cut else solids).append(obj);return obj
  def axisbox(name,lo,hi,kind,owner=None,cut=False):return box(name,[0,0,0],E,lo,hi,kind,owner,cut)
  def cyl(name,origin,axis,s0,s1,radius,kind,owner=None,cut=False):
   obj={'id':prefix+name,'board':board,'shape':'finite_cylinder','axis_endpoints_xyz_mm':[point(add(origin,mul(axis,s))) for s in [s0,s1]],'radius_mm':radius,'kind':kind,'wire':owner,'subtract':[]}
   (cuts if cut else solids).append(obj);return obj
  def subtract(obj,*holes):obj['subtract'].extend(h['id'] for h in holes)
  beam=axisbox('top-beam',[3.5,0,-6.35],[314.5,7,2.65],'dielectric_sleeved_beam')
  # Actual inner conductor/metal structure separately bounded, no exposed metal.
  core=axisbox('top-beam-metal-core',[4.5,1,-5.35],[313.5,6,1.65],'structural_metal_core')
  subtract(beam,core);joints.append({'a':beam['id'],'b':core['id'],'type':'captured_sleeve_fit'})
  for s,x in enumerate([6.5,311.5],1):
   lug=axisbox(f'support-{s}/lug',[x-3,6,.65],[x+3,13.5,4.65],'support_lug')
   bore=cyl(f'support-{s}/bore',[x,10.5,0],[0,0,1],-4,7,1.1,'void',cut=True);subtract(lug,bore)
   shaft=cyl(f'support-{s}/M2-shaft',[x,10.5,0],[0,0,1],-3.1,5.15,1.,'support_fastener')
   for side,d0,d1 in [('face',0,.65),('opposite',-2.1,-1.6)]:
    washer=cyl(f'support-{s}/{side}-washer',[x,10.5,0],[0,0,1],d0,d1,2.5,'insulating_washer');subtract(washer,bore)
   for side,d0,d1 in [('head',-3.6,-2.1),('nut',4.65,5.65)]:
    cap=cyl(f'support-{s}/{side}-outer-cap',[x,10.5,0],[0,0,1],d0,d1,2.5,'insulated_fastener_envelope')
    inner=cyl(f'support-{s}/{side}-metal',[x,10.5,0],[0,0,1],d0+.25,d1-.25,1.9,'fastener_metal');subtract(cap,inner)
    shaft_clear=cyl(f'support-{s}/{side}-shaft-clearance',[x,10.5,0],[0,0,1],(-3.1 if side=='head' else 4.5),(-2.0 if side=='head' else 5.15),1.05,'void',cut=True);subtract(cap,shaft_clear)
   joints.extend([{'a':beam['id'],'b':lug['id'],'type':'monolithic_overlap'},{'a':lug['id'],'b':shaft['id'],'type':'own_support_hole_clamp','existing_support_xy_mm':[x,10.5],'source_hole_mm':2.2}])
  for i,sign in enumerate([1,-1,1,1,-1,1]):
   k=i+1;x=23+17*(i%3)+(58 if board=='KB' else 0);y=15.5+9*(i//3);A=[x,y,2.]
   w=[(.5933040689317951 if board=='KA' else -.5933040689317951),sign*.5927989259019525,.5445913286478836]
   rho=math.hypot(w[0],w[1]);n=[-w[2]*w[0]/rho,-w[2]*w[1]/rho,rho];v=cross(w,n)
   collet=cyl(f'w{k}/collet',A,w,1,2.5,2.,'split_collet',k)
   bore=cyl(f'w{k}/wire-bore',A,w,.5,3.,1.2954,'own_wire_bore',k,True)
   split=box(f'w{k}/split-slot',A,[w,n,v],[.5,-2.5,-.1],[3,6,.1],'void',k,True)
   subtract(collet,bore,split)
   tongue=box(f'w{k}/lug-tongue',A,[w,n,v],[1,1.7,-1.5],[1.5,2.6,1.5],'clamp_lug_tongue',k);subtract(tongue,split,bore)
   lug=box(f'w{k}/lug',A,[w,n,v],[1,2.6,-1.5],[2.5,5.5,1.5],'clamp_lug',k);subtract(lug,split,bore)
   bc=add(add(A,mul(w,1.75)),mul(n,4))
   hole=cyl(f'w{k}/M1-bore',bc,v,-2,2,.55,'void',k,True);subtract(lug,hole)
   cyl(f'w{k}/M1-shaft',bc,v,-1.8,3.2,.5,'clamp_metal',k)
   cyl(f'w{k}/M1-head',bc,v,-2.0,-1.5,1.,'clamp_metal',k)
   cyl(f'w{k}/M1-nut',bc,v,1.5,2.3,1.2,'clamp_metal',k)
   for nm,s0,s1 in [('head',-2.3,-1.5),('nut',1.5,3.5)]:
    cap=cyl(f'w{k}/{nm}-cap',bc,v,s0,s1,1.4,'insulation_cap',k)
    void=cyl(f'w{k}/{nm}-cap-cavity',bc,v,(1.4 if nm=='nut' else s0+.1),(3.4 if nm=='nut' else s1),1.25,'void',k,True);subtract(cap,void)
   P=add(add(A,mul(w,.75)),mul(n,5.5));lane=x+(-6 if board=='KA' else 6)
   back_y=P[1]-sign*4
   path=[P,[P[0],back_y,P[2]],[P[0],back_y,1.65],[lane,back_y,1.65],[lane,5.5,1.65]];finger=[]
   for j,(a,b) in enumerate(zip(path,path[1:])):
    if norm(add(a,mul(b,-1)))<1e-10:continue
    finger.append(axisbox(f'w{k}/finger-{j}',[min(a[t],b[t])-1 for t in range(3)],[max(a[t],b[t])+1 for t in range(3)],'carrier_finger',k))
   joints.append({'a':collet['id'],'b':tongue['id'],'type':'monolithic_overlap'})
   joints.append({'a':tongue['id'],'b':lug['id'],'type':'monolithic_overlap'})
   for a,b in zip([lug]+finger,finger+[beam]):joints.append({'a':a['id'],'b':b['id'],'type':'monolithic_overlap'})
   # Tangent continuation reaches board face exactly. Sleeve is outer material,
   # not additional electrical metal or permission to consume free service length.
   length=2/w[2];land=add(A,mul(w,-length))
   terminations.append({'board':board,'wire':k,'land_xyz_mm':point(land),'axis_from_land_xyz':vector(w),'bridge_axis_length_mm':length,'insulation_start_axis_mm':3.75,'insulation_start_tolerance_mm':.05,'insulation_outer_radius_mm':1.2954,'insulation_end_cut':'flat plane normal to ownaxis at station 3.75 +/- 0.05 mm','metal_outer_radius_mm':1.0,'metal_low_trim':'boardparallel plane locald=0.05; electrical contactproducer supplies clippedsolid','metal_trim_plane_global_z_mm':face+normal*.05,'insulation_qualification':False,'stripping_accounting':'Two 3.75mm installed stripped ends lie within existing completepath; no extra 7.5mm cut cost. Minimum4.5mm preparation remains separate reservedcutlength, not servicelength.','redundant_bridge_sleeve':'REMOVED'})
   shroud=axisbox(f'w{k}/termination-shroud',[land[0]-2.5,land[1]-2.5,0],[land[0]+2.5,land[1]+2.5,1.5],'termination_insulator',k)
   cavity=axisbox(f'w{k}/termination-cavity',[land[0]-2,land[1]-2,-.1],[land[0]+2,land[1]+2,1.0],'void',k,True)
   entry=cyl(f'w{k}/termination-entry',land,w,-1,5,1.7,'void',k,True);subtract(shroud,cavity,entry)
   axisbox(f'w{k}/solder-envelope',[land[0]-2,land[1]-2,0],[land[0]+2,land[1]+2,.05],'own_net_solder_envelope',k)
 common_format(solids,cuts)
 return {'status':'UNVALIDATED_CONSTRUCTIVE_SOURCE_SOLIDS','travel_mm':travel_mm,'solids':solids,'boolean_cutters':cuts,'wire_termination_regions':terminations,'intended_structural_joints':joints,'existing_support_interface':'Only two top2.2mm NPTH collars eachboard; preserved existing independent board carrier/service-guide structure. No enclosure receiver redesign.','same_carrier_union':'All carrier_finger solids on sameboard may intentionally merge where they share column; never exempt foreign wires/terminals.','negative_gates':{'continuous_clearance':False,'load_retention':False,'material_qualification':False,'all100_access':False,'physical_fit':False,'native':False}}
