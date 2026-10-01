"""Read the first native VRML coordinate mesh with its enclosing transforms.

This deliberately bounded reader supports the Transform fields emitted by the
pinned KiCad exporter. Unknown fields and malformed numbers fail closed.
"""
import math
import re

NUMBER=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
TOKEN=re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|'+NUMBER+r'|[A-Za-z_][A-Za-z_0-9]*|[{}\[\],]')


def identity():
    return [[float(i==j) for j in range(4)] for i in range(4)]


def product(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def translation(v):
    out=identity()
    for i in range(3):out[i][3]=v[i]
    return out


def scaling(v):
    out=identity()
    for i in range(3):out[i][i]=v[i]
    return out


def rotation(v):
    x,y,z,angle=v
    if angle==0:return identity()
    length=math.sqrt(x*x+y*y+z*z)
    if length==0:raise ValueError('zero VRML rotation axis')
    x,y,z=x/length,y/length,z/length
    c=math.cos(angle);s=math.sin(angle);k=1-c
    out=identity()
    out[:3]=[[c+x*x*k,x*y*k-z*s,x*z*k+y*s,0],
             [y*x*k+z*s,c+y*y*k,y*z*k-x*s,0],
             [z*x*k-y*s,z*y*k+x*s,c+z*z*k,0]]
    return out


def numeric(values):
    if any(not re.fullmatch(NUMBER,v) for v in values):raise ValueError('invalid VRML number')
    out=list(map(float,values))
    if not all(math.isfinite(v) for v in out):raise ValueError('nonfinite VRML number')
    return out


def transform(tokens,start,end):
    fields={};i=start+1
    arities={'center':3,'rotation':4,'scale':3,'scaleOrientation':4,'translation':3}
    while i<end:
        key=tokens[i];i+=1
        if key in fields:raise ValueError('duplicate VRML transform field')
        if key=='children':
            if tokens[i]!='[':raise ValueError('expected VRML children array')
            depth=1;i+=1
            while i<end and depth:
                if tokens[i]=='[':depth+=1
                elif tokens[i]==']':depth-=1
                i+=1
            if depth:raise ValueError('unterminated VRML children')
            fields[key]=True
        elif key in arities:
            n=arities[key];fields[key]=numeric(tokens[i:i+n]);i+=n
            if len(fields[key])!=n:raise ValueError('incomplete VRML transform')
        else:raise ValueError('unsupported VRML transform field: '+key)
    c=fields.get('center',[0,0,0]);r=fields.get('rotation',[0,0,1,0])
    sr=fields.get('scaleOrientation',[0,0,1,0]);s=fields.get('scale',[1,1,1])
    t=fields.get('translation',[0,0,0]);out=identity()
    # VRML97: T C R SR S inverse(SR) inverse(C).
    for item in (translation(t),translation(c),rotation(r),rotation(sr),scaling(s),
                 rotation(sr[:3]+[-sr[3]]),translation([-v for v in c])):
        out=product(out,item)
    return out


def first_coordinate_geometry(text):
    matches=list(TOKEN.finditer(text))
    # Reject unrecognized syntax instead of dropping it during tokenization.
    cursor=0;tokens=[]
    for m in matches:
        if text[cursor:m.start()].strip():raise ValueError('unsupported VRML syntax')
        cursor=m.end()
        if not m[0].startswith('#') and m[0]!=',':tokens.append(m[0])
    if text[cursor:].strip():raise ValueError('unsupported trailing VRML syntax')
    stack=[];pairs={}
    for i,t in enumerate(tokens):
        if t in ('{','['):stack.append(i)
        elif t in ('}',']'):
            if not stack:raise ValueError('unbalanced VRML')
            start=stack.pop()
            if tokens[start]+t not in ('{}','[]'):raise ValueError('mismatched VRML brackets')
            pairs[start]=i
    if stack:raise ValueError('unterminated VRML node')
    coordinate=next((i for i in range(len(tokens)-2) if tokens[i:i+3]==['Coordinate','{','point']),None)
    if coordinate is None:raise ValueError('no explicit VRML coordinate mesh')
    point=coordinate+3
    if tokens[point]!='[':raise ValueError('expected VRML point array')
    numbers=numeric(tokens[point+1:pairs[point]])
    if len(numbers)<24 or len(numbers)%3:raise ValueError('incomplete VRML mesh coordinates')
    if pairs[point]+1!=pairs[coordinate+1]:raise ValueError('unsupported Coordinate field')
    for i in pairs:
        if tokens[i]=='{' and i>0 and i<coordinate<pairs[i] and tokens[i-1] not in ('Transform','Shape','IndexedFaceSet','Group'):
            raise ValueError('unsupported enclosing VRML node: '+tokens[i-1])
    ancestors=[i for i in pairs if tokens[i]=='{' and i>0 and tokens[i-1]=='Transform'
               and i<coordinate<pairs[i]]
    matrix=identity()
    for i in sorted(ancestors):matrix=product(matrix,transform(tokens,i,pairs[i]))
    points=[]
    for i in range(0,len(numbers),3):
        p=numbers[i:i+3]+[1]
        points.append([sum(matrix[j][k]*p[k] for k in range(4)) for j in range(3)])
    bounds=[(min(p[i] for p in points),max(p[i] for p in points)) for i in range(3)]
    local_points=list(zip(*(iter(numbers),)*3))
    axis_sizes=tuple((max(p[i] for p in local_points)-min(p[i] for p in local_points))
                    * math.sqrt(sum(matrix[j][i]**2 for j in range(3))) for i in range(3))
    return {'bounds':bounds,'size':tuple(b-a for a,b in bounds),'mesh_axis_sizes':axis_sizes,
            'center':tuple((a+b)/2 for a,b in bounds),'transform_count':len(ancestors)}
