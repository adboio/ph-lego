"""Orthogonal parts and explicit mating sites in LDraw units (0.4 mm)."""
import math
from functools import lru_cache
from pathlib import Path
import json
CAT=json.loads((Path(__file__).resolve().parents[1]/'references/catalog.json').read_text())['parts']

def mmul(a,b):return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def mv(a,v):return tuple(sum(a[i][j]*v[j] for j in range(3)) for i in range(3))
def add(a,b):return tuple(x+y for x,y in zip(a,b))

def basis(p):
    c,s={0:(1,0),90:(0,1),180:(-1,0),270:(0,-1)}[p['rotation']]
    rz=((c,-s,0),(s,c,0),(0,0,1))
    face={'up':((1,0,0),(0,1,0),(0,0,1)), 'front':((1,0,0),(0,0,-1),(0,1,0)), 'back':((-1,0,0),(0,0,1),(0,1,0)), 'right':((0,0,1),(1,0,0),(0,1,0)), 'left':((0,0,-1),(-1,0,0),(0,1,0))}[p.get('orientation','up')]
    return mmul(face,rz)

def dimensions(p):
    c=CAT[p['part']];return c['width']*20,c['depth']*20,c['height']*8

def transform(p):
    M=basis(p);w,d,h=dimensions(p)
    corners=[mv(M,(x,y,z)) for x in (0,w) for y in (0,d) for z in (0,h)]
    mins=tuple(min(v[i] for v in corners) for i in range(3))
    t=tuple(a-b for a,b in zip((p['x']*20,p['y']*20,p['z']*8),mins))
    return M,t

def world(p,v):
    M,t=transform(p);return tuple(round(x,5) for x in add(mv(M,v),t))

def shape(p):
    M=basis(p);d=dimensions(p);s=tuple(sum(abs(M[i][j])*d[j] for j in range(3)) for i in range(3))
    return s[0]/20,s[1]/20,s[2]/8

def bounds(p):
    w,d,h=shape(p);return (p['x']*20,p['y']*20,p['z']*8,(p['x']+w)*20,(p['y']+d)*20,(p['z']+h)*8)

def sites(p):
    c=CAT[p['part']];w,d,h=dimensions(p);M=basis(p);up=mv(M,(0,0,1));down=mv(M,(0,0,-1));tops=[];bottoms=[]
    for i in range(c['width']):
        for j in range(c['depth']):
            x,y=(i+.5)*20,(j+.5)*20
            if c.get('round') and (x-w/2)**2+(y-d/2)**2>(min(w,d)/2-2)**2:continue
            if c.get('studs',True) and p['part']!='15573':tops.append((world(p,(x,y,h)),up))
            if p['part'] not in ['11477','15068'] or j==0:bottoms.append((world(p,(x,y,0)),down))
    if 'top_sites' in c:tops=[(world(p,(x*20,y*20,h)),up) for x,y in c['top_sites']]
    if 'bottom_sites' in c:bottoms=[(world(p,(x*20,y*20,0)),down) for x,y in c['bottom_sites']]
    if p['part']=='15573':tops.append((world(p,(w/2,d/2,h)),up))
    if p['part'] in ['87087','11211']:
        for i in range(c['width']):tops.append((world(p,((i+.5)*20,0,14)),mv(M,(0,-1,0))))
    return tops,bottoms

def ldraw_transform(p):
    # Official meshes have differing origins; normalize through each part's documented bottom plane.
    c=CAT[p['part']];M,t=transform(p)
    from_ld=((1,0,0),(0,0,1),(0,-1,0));to_ld=((1,0,0),(0,0,-1),(0,1,0))
    offset=c.get('ldraw_offset',(c['width']*10,c['depth']*10,c['ldraw_bottom']))
    return mmul(to_ld,mmul(M,from_ld)),mv(to_ld,add(mv(M,offset),t))

@lru_cache(None)
def mesh(name):
    root=Path(__file__).resolve().parents[2]/'library/ldraw'
    name=name.replace('\\','/').lower()
    f=next((q for q in (root/'parts'/name,root/'p'/name) if q.is_file()),None)
    if f is None:raise FileNotFoundError(name)
    verts=[];faces=[]
    for line in f.read_text(errors='replace').splitlines():
        a=line.split()
        if not a:continue
        if a[0]=='1':
            v,fs=mesh(' '.join(a[14:]));t=tuple(map(float,a[2:5]));flat=list(map(float,a[5:14]));M=[flat[i:i+3] for i in (0,3,6)];n=len(verts)
            verts.extend(add(mv(M,vv),t) for vv in v);faces.extend(tuple(n+j for j in face) for face in fs)
        elif a[0] in ('3','4'):
            n=len(verts);numbers=list(map(float,a[2:]));verts.extend(tuple(numbers[i:i+3]) for i in range(0,len(numbers),3));faces.append(tuple(range(n,len(verts))))
    return verts,faces
