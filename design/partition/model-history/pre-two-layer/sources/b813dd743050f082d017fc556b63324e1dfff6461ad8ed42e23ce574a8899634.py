"""One canonical affine edge partition shared by sheet and barrel fields."""
import numpy as np
import shapely
from shapely.geometry import LineString,Point


def canonical_interfaces(xy,edges,boundary_ids,interfaces,vertical,horizontal):
    metric=np.rint(xy*1e9).astype(np.longdouble)/np.longdouble(1e9)
    tree=shapely.STRtree(shapely.linestrings(xy[edges[boundary_ids]]))
    records={};assigned={};maximum=0.
    for ib,interface in enumerate(interfaces):
        centre=np.rint(np.asarray(interface['centre'],dtype=float)*1e6).astype(np.longdouble)/np.longdouble(1e6)
        polygon=centre+np.asarray(interface['relative'],dtype=np.longdouble)
        for sector,(a0,b0) in enumerate(zip(polygon,np.roll(polygon,-1,axis=0))):
            a=np.asarray(a0,dtype=np.longdouble);b=np.asarray(b0,dtype=np.longdouble);d=b-a
            line=LineString(np.asarray([a0,b0],dtype=float));parameters={};pieces=[]
            for candidate in tree.query(line.buffer(2e-9)):
                face=int(boundary_ids[candidate]);vertices=edges[face]
                if max(Point(p).distance(line) for p in xy[vertices])>2e-9:continue
                for vertex in vertices:
                    vertex=int(vertex)
                    if vertex in parameters:continue
                    point=xy[vertex]
                    if tuple(point)==tuple(round(float(v),9) for v in a):t=np.longdouble(0)
                    elif tuple(point)==tuple(round(float(v),9) for v in b):t=np.longdouble(1)
                    else:
                        choices=[]
                        for axis,grid in ((0,vertical),(1,horizontal)):
                            if point[axis] in grid and abs(d[axis])>1e-18:
                                fixed=np.longdouble(round(float(point[axis])*1e9))/np.longdouble(1e9)
                                value=(fixed-a[axis])/d[axis]
                                choices.append((float(np.linalg.norm(a+value*d-point)),value))
                        if not choices:raise ValueError('interface vertex has no canonical cell-edge intersection')
                        distance,t=min(choices,key=lambda item:item[0])
                        if distance>2e-9:raise ValueError('canonical interface projection exceeds retained geometry guard')
                    if not 0<=t<=1:raise ValueError('interface parameter lies outside its canonical edge')
                    location=a+t*d
                    if vertex in assigned and np.max(abs(assigned[vertex]-location))>1e-15:
                        raise ValueError('canonical interface vertex has conflicting physical locations')
                    assigned[vertex]=location;metric[vertex]=location;parameters[vertex]=t
                    maximum=max(maximum,float(np.linalg.norm(location-point)))
                va,vb=map(int,vertices);ta,tb=parameters[va],parameters[vb]
                if ta==tb:raise ValueError('collapsed canonical interface face')
                pieces.append({'face':face,'vertices':(va,vb),'parameters':(ta,tb)})
            ordered=sorted((min(p['parameters']),max(p['parameters'])) for p in pieces)
            if not ordered or ordered[0][0]!=0 or ordered[-1][1]!=1 or any(a[1]!=b[0] for a,b in zip(ordered,ordered[1:])):
                raise ValueError('canonical interface faces do not telescope exactly from zero to one')
            records[ib,sector]=pieces
    return metric,records,maximum
