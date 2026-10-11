"""Source-only sufficient contact/capsule/via checks; never emits copper or routes."""
import math
import shapely

EPS=1e-6  # mm: reject numerical/tangent contact; never reduce required clearance.


def point(xy):
    if len(xy)!=2 or not all(math.isfinite(v) for v in xy):raise ValueError('finite XY required')
    return shapely.Point(xy)


class Geometry:
    def __init__(self,dump):
        self.dump=dump;self.layers=tuple(dump['layers']);self.pads={p['uuid']:p for p in dump['pads']}
        self.outline=shapely.build_area(shapely.MultiLineString([[(e[0]/1e6,e[1]/1e6),(e[2]/1e6,e[3]/1e6)] for e in dump['edges']]))
        if self.outline.is_empty or not self.outline.is_valid:raise ValueError('valid closed board outline required')
        self.objects=[];self.holes=[];self.smd=[];self.keepouts=[]
        for p in dump['pads']:
            if p['poly']:
                shape=shapely.Polygon([(x/1e6,y/1e6) for x,y in p['poly']])
                if not shape.is_valid:raise ValueError('invalid pad polygon '+p['uuid'])
                self.objects.append((shape,0,p['net'],set(p['layers']),p['uuid']))
                if not p['drill']:self.smd.append((shape,p['uuid']))
            if p['drill']:
                shape=point([x/1e6 for x in p['xy']]);radius=p['drill']/2e6
                self.holes.append((shape,radius,p['uuid']))
                if p['npth']:self.objects.append((shape,radius,None,set(self.layers),p['uuid']+':NPTH'))
        for t in dump['tracks']:
            shape=shapely.LineString([[v/1e6 for v in t[k]] for k in ('a','b')])
            self.objects.append((shape,t['width']/2e6,t['net'],{t['layer']},t['uuid']))
        for v in dump['vias']:
            shape=point([x/1e6 for x in v['xy']])
            self.objects.append((shape,v['diameter']/2e6,v['net'],set(self.layers),v['uuid']))
            self.holes.append((shape,v['drill']/2e6,v['uuid']))
        for k in dump['keepouts']:
            if len(k['poly'])<3:continue
            if k.get('name')=='NECKDOWN' or str(k.get('name','')).endswith(':neckdown'):continue
            self.keepouts.append((shapely.Polygon([(x/1e6,y/1e6) for x,y in k['poly']]),k))
        self.hole_tree=shapely.STRtree([r[0] for r in self.holes]);self.hole_max=max((r[1] for r in self.holes),default=0)
        self.smd_tree=shapely.STRtree([r[0] for r in self.smd])
        self.keep_tree=shapely.STRtree([r[0] for r in self.keepouts])
        self.tree=shapely.STRtree([r[0] for r in self.objects]);self.max_radius=max((r[1] for r in self.objects),default=0)

    def copper_margin(self,geometry,radius,net,layers,clearance):
        reach=radius+clearance+self.max_radius+EPS
        x0,y0,x1,y1=geometry.bounds
        candidates=self.tree.query(shapely.box(x0-reach,y0-reach,x1+reach,y1+reach))
        best=(float('inf'),None)
        for index in candidates:
            shape,r,other,occupied,identity=self.objects[int(index)]
            if other==net or not occupied.intersection(layers):continue
            value=geometry.distance(shape)-r-radius-clearance
            if value<best[0]:best=(value,identity)
        return best

    def limits(self,geometry,radius,net,layers,clearance,kind):
        copper,identity=self.copper_margin(geometry,radius,net,set(layers),clearance)
        edge=geometry.distance(self.outline.boundary)-radius-.5 if self.outline.covers(geometry) else -1.
        keep=float('inf')
        x0,y0,x1,y1=geometry.bounds
        for index in self.keep_tree.query(shapely.box(x0-radius-EPS,y0-radius-EPS,x1+radius+EPS,y1+radius+EPS)):
            shape,k=self.keepouts[int(index)]
            if not k[kind] or (kind=='tracks' and not set(k['layers']).intersection(layers)):continue
            keep=min(keep,geometry.distance(shape)-radius)
        margins={'foreign_copper':copper,'board_edge':edge,'keepout':keep}
        return {'pass':all(v>=EPS for v in margins.values()),'checked_margins_mm':{k:(v if math.isfinite(v) else None) for k,v in margins.items()},'nearest_foreign':identity,'margin_scope':'Censored collision-screen values, not global minimum clearance. None means no potentially violating object within the complete bounding-box query; no infinite physical margin is claimed.'}

    def segment(self,a,b,net,layer,width,clearance=.25):
        if not math.isfinite(width) or width<=0 or not math.isfinite(clearance) or clearance<0:raise ValueError('invalid width/clearance')
        point(a);point(b)
        if layer not in self.layers:raise ValueError('unknown layer')
        line=point(a) if tuple(a)==tuple(b) else shapely.LineString([a,b])
        return self.limits(line,width/2,net,[layer],clearance,'tracks')

    def contact(self,anchor_uuid,start,net,layer):
        """Sufficient named-anchor contact; no blanket endpoint collision exemption."""
        p=self.pads.get(anchor_uuid)
        if p is None or p['net']!=net or layer not in p['layers'] or not p['poly']:
            return {'pass':False,'reason':'wrong anchor/net/layer'}
        polygon=shapely.Polygon([(x/1e6,y/1e6) for x,y in p['poly']]);q=point(start)
        margin=q.distance(polygon.boundary) if polygon.contains(q) else -q.distance(polygon)
        return {'pass':margin>=EPS,'reason':'center strictly inside exact named anchor' if margin>=EPS else 'off-pad/boundary/tangent contact not certified',
                'interior_margin_mm':margin,'anchor_uuid':anchor_uuid}

    def terminal_edge(self,anchor_uuid,a,b,net,layer,width,clearance=.25):
        contact=self.contact(anchor_uuid,a,net,layer);sweep=self.segment(a,b,net,layer,width,clearance)
        return {'pass':contact['pass'] and sweep['pass'],'contact':contact,'sweep':sweep,
                'scope':'Full-width swept capsule and sufficient named-anchor geometric contact only; no thermal/current/native acceptance.'}

    def via(self,xy,net,diameter=.6,drill=.3,clearance=.25,hole_clearance=.25):
        if not all(math.isfinite(v) for v in (diameter,drill,clearance,hole_clearance)) or not 0<drill<diameter or min(clearance,hole_clearance)<0:raise ValueError('invalid via dimensions')
        q=point(xy);r=diameter/2;result=self.limits(q,r,net,self.layers,clearance,'vias')
        # Preserve the frozen conservative barrel-to-existing-hole policy (outer radius).
        reach=r+hole_clearance+self.hole_max+EPS
        hole_ids=self.hole_tree.query(shapely.box(xy[0]-reach,xy[1]-reach,xy[0]+reach,xy[1]+reach))
        hole=min((q.distance(self.holes[int(i)][0])-self.holes[int(i)][1]-r-hole_clearance for i in hole_ids),default=float('inf'))
        smd_ids=self.smd_tree.query(shapely.box(xy[0]-r-EPS,xy[1]-r-EPS,xy[0]+r+EPS,xy[1]+r+EPS))
        smd=min((q.distance(self.smd[int(i)][0])-r for i in smd_ids),default=float('inf'))
        result['checked_margins_mm'].update(existing_hole=hole if math.isfinite(hole) else None,smd=smd if math.isfinite(smd) else None)
        result['pass']=result['pass'] and hole>=EPS and smd>=EPS
        result['scope']='New through-via disk on every copper layer; all holes and own/foreign SMD restrictions; no native acceptance.'
        return result


def terminal_clearance_upper_bound(geometry,anchor_uuid,width,clearance=.25,tolerance=.001,max_cells=20000):
    """Lipschitz upper bound over whole pad using nearest two foreign pad shapes.

    Using a subset of obstacles can only overestimate actual clearance. This
    certifies only the center-inside contact policy, never physical impossibility.
    """
    import heapq
    p=geometry.pads[anchor_uuid];polygon=shapely.Polygon([(x/1e6,y/1e6) for x,y in p['poly']])
    candidates=[]
    for shape,r,net,layers,uid in geometry.objects:
        if r==0 and uid in geometry.pads and net!=p['net'] and layers.intersection(p['layers']):
            candidates.append((polygon.distance(shape),uid,shape))
    candidates=sorted(candidates,key=lambda x:(x[0],x[1]))[:2]
    if len(candidates)<2:return {'status':'NOT CERTIFIED: fewer than two foreign pad constraints'}
    value=lambda xy:min(point(xy).distance(q[2]) for q in candidates)
    lower=0.;best=None;heap=[];seq=0
    def add(box):
        nonlocal lower,best,seq
        cell=shapely.box(*box)
        if not polygon.intersects(cell):return
        x0,y0,x1,y1=box;center=((x0+x1)/2,(y0+y1)/2)
        upper=value(center)+math.hypot(x1-x0,y1-y0)/2+1e-9
        sample=polygon.intersection(cell).representative_point();v=value((sample.x,sample.y))
        if v>lower:lower=v;best=[sample.x,sample.y]
        seq+=1;heapq.heappush(heap,(-upper,seq,box))
    add(polygon.bounds);splits=0
    while heap and -heap[0][0]-lower>tolerance and splits<max_cells:
        upper,_,(x0,y0,x1,y1)=heapq.heappop(heap)
        if -upper<=lower:continue
        xm,ym=(x0+x1)/2,(y0+y1)/2
        for box in ((x0,y0,xm,ym),(xm,y0,x1,ym),(x0,ym,xm,y1),(xm,ym,x1,y1)):add(box)
        splits+=1
    upper=max(lower,-heap[0][0] if heap else lower);required=width/2+clearance
    return {'status':'CENTER_INSIDE_CONTACT_BLOCKED_BY_FOREIGN_PADS' if upper<required-EPS else 'NO_BLOCKAGE_CERTIFICATE',
            'foreign_pad_uuids':[q[1] for q in candidates],'maximum_center_clearance_lower_mm':lower,
            'maximum_center_clearance_upper_mm':upper,'required_center_clearance_mm':required,
            'upper_margin_mm':upper-required,'best_sample_mm':best,'cells_split':splits,'tolerance_mm':tolerance,
            'method':'Distance to each exact polygon is1-Lipschitz; minimum retains that bound. Every intersecting pad-box cell has upper=f(center)+half-diagonal+1e-9. Two-obstacle subset overestimates clearance to all obstacles. Ordinary floating engineering enclosure, not directed-rounding proof.',
            'scope':'Any start center within this exact pad under full-width capsule and unchanged clearance; off-pad pad-end contacts and altered widths are outside this certificate.'}
