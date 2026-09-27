"""Panel-frame outline geometry, including convex fillets."""
from __future__ import annotations
import math

def outline_segments(points, radius):
    """Return ('line', start, end) or ('arc', start, mid, end) segments."""
    if radius==0:return [('line',p,points[(i+1)%len(points)]) for i,p in enumerate(points)]
    n=len(points);cross=[]
    for i,p in enumerate(points):
        a=points[i-1];b=points[(i+1)%n]
        cross.append((p[0]-a[0])*(b[1]-p[1])-(p[1]-a[1])*(b[0]-p[0]))
    if any(abs(v)<1e-9 for v in cross) or any(v*cross[0]<0 for v in cross):raise ValueError('rounded outline must be strictly convex')
    corners=[]
    for i,p in enumerate(points):
        prev=points[i-1];nxt=points[(i+1)%n]
        vin=(prev[0]-p[0],prev[1]-p[1]);vout=(nxt[0]-p[0],nxt[1]-p[1])
        lin=math.hypot(*vin);lout=math.hypot(*vout)
        u=(vin[0]/lin,vin[1]/lin);v=(vout[0]/lout,vout[1]/lout)
        theta=math.acos(max(-1,min(1,u[0]*v[0]+u[1]*v[1])))
        d=radius/math.tan(theta/2)
        if d>=min(lin,lout)/2:raise ValueError('corner radius consumes an outline edge')
        bis=(u[0]+v[0],u[1]+v[1]);bl=math.hypot(*bis);bis=(bis[0]/bl,bis[1]/bl)
        start=(p[0]+u[0]*d,p[1]+u[1]*d);end=(p[0]+v[0]*d,p[1]+v[1]*d)
        m=radius*(1/math.sin(theta/2)-1);mid=(p[0]+bis[0]*m,p[1]+bis[1]*m)
        corners.append((start,mid,end))
    result=[]
    for i,(start,mid,end) in enumerate(corners):
        result.append(('arc',start,mid,end))
        result.append(('line',end,corners[(i+1)%n][0]))
    return result
