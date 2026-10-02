"""Retain the seated body while rebuilding Max's facial details."""
import json
import sys
from pathlib import Path
from bricklib import dumps, validate

model=json.loads(Path(sys.argv[1]).read_text())
start=next(i for i,s in enumerate(model['steps']) if s['title']=='Build the projecting muzzle')
end=next(i for i,s in enumerate(model['steps']) if s['title'].startswith('Texture the'))
keep={pid for s in model['steps'][:start]+model['steps'][end:] for pid in s['parts']}
model['parts']=[p for p in model['parts'] if p['id'] in keep]
steps=[]

def group(title):
    steps.append(dict(title=title,parts=[],view='front-right'))

def add(pid,color,x,y,z,rotation=0):
    p=dict(id=f'face-{sum(len(s["parts"]) for s in steps)+1:03}',part=pid,color=color,
           x=x,y=y,z=z,rotation=rotation,orientation='front')
    model['parts'].append(p);steps[-1]['parts'].append(p['id'])

group('Build the soft tan muzzle')
add('3795','031',-3,-1.4,34)
add('15068','031',-3,-2.2,34,270)
add('15068','031',1,-2.2,34,90)
add('3022','031',-1,-1.8,34)
group('Finish the muzzle and brown nose')
add('3069b','031',-1,-2.2,34)
add('15573','031',-1,-2.2,36.5)
add('98138','081',-.5,-2.6,36.5)

for x,side in [(-4,'left'),(2,'right')]:
    group('Mount the '+side+' eye')
    add('4032','080',x,-1.4,42.5)
    group('Add the '+side+' eye and white glint')
    # Each quarter's square corner points toward the center of the eye.
    for dx,dz,rotation,color in [(0,0,270,'080'),(1,0,0,'080'),(0,2.5,180,'090'),(1,2.5,90,'080')]:
        add('25269',color,x+dx,-1.8,42.5+dz,rotation)

for x,side in [(-6,'left'),(2,'right')]:
    group('Build the centered '+side+' ear')
    add('60474','031',x,-1.4,48.5)
    add('14769','081',x+1,-1.8,51)

model['steps']=model['steps'][:start]+steps+model['steps'][end:]
model['description']='Seated Max with unchanged Tan skin, thin tan ears with centered brown interiors, a simple tan muzzle, a brown nose, and brick-built black eyes with white quarter-tile glints. Physical assembly has not been tested.'
model['id']='max-posthog-face-v2'
report=validate(model)
if not report['passed']:
    raise ValueError(dumps(report))
Path(sys.argv[2]).write_text(dumps(model))
print(dumps(dict(parts=len(model['parts']),steps=len(model['steps']),report=report)))
