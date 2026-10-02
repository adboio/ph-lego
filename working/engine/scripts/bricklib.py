"""Shared contract, grid checks and deterministic data exports (no Blender dependency)."""
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'references/catalog.json').read_text())
PARTS, COLORS = CATALOG['parts'], CATALOG['colors']
VIEWS = {'front-right': (1,-1), 'back-right': (1,1), 'back-left': (-1,1), 'front-left': (-1,-1)}
VERSION = 'max-extension-1.0'

def dumps(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'

def read_json(path):
    p = Path(path)
    if p.stat().st_size > 8_000_000:
        raise ValueError('JSON exceeds 8 MB')
    def unique(pairs):
        result = {}
        for k,v in pairs:
            if k in result:
                raise ValueError(f'Duplicate JSON key: {k}')
            result[k] = v
        return result
    return json.loads(p.read_text(encoding='utf-8'), object_pairs_hook=unique)

from geometry import shape

def footprint(p):
    w,d,_ = shape(p)
    return {(x,y) for x in range(p['x'],p['x']+w) for y in range(p['y'],p['y']+d)}

def bbox(model):
    ps=model['parts']
    import math
    return (math.floor(min(p['x'] for p in ps)), math.floor(min(p['y'] for p in ps)), 0,
            math.ceil(max(p['x']+shape(p)[0] for p in ps)), math.ceil(max(p['y']+shape(p)[1] for p in ps)),
            max(p['z']+shape(p)[2] for p in ps))

def validate(model):
    from jsonschema import Draft202012Validator
    errors = [f'{"/".join(map(str,e.path)) or "model"}: {e.message}'
              for e in Draft202012Validator(read_json(ROOT/'references/model.schema.json')).iter_errors(model)]
    report = {'schema_version':'1.0','validator_version':VERSION,'passed':False,'errors':errors,'warnings':[],
              'physical_build':'unverified','visual_review':'unverified',
              'checks':['schema','unique instances','step coverage','body collisions','stud overlap','assembly order','final connectivity'],
              'not_checked':['clutch force','stability and tipping','part/color market availability','full insertion path','underside mechanics']}
    if errors: return report
    from validate_extended import run
    return run(model,report)

def inventory(parts):
    counts=Counter((p['part'],p['color']) for p in parts)
    return [{'part_id':pid,'part_name':PARTS[pid]['name'],'color_id':c,'color_name':COLORS[c]['name'],'quantity':n}
            for (pid,c),n in sorted(counts.items())]

def parts_csv(model):
    out=io.StringIO(newline=''); w=csv.DictWriter(out,fieldnames=['part_id','part_name','color_id','color_name','quantity'],lineterminator='\n')
    w.writeheader();w.writerows(inventory(model['parts']));return out.getvalue()

def ldraw(model):
    from geometry import ldraw_transform
    rows=[f'0 {model["title"]}',f'0 Name: {model["id"]}.ldr',f'0 Author: {model["author"]}', '0 // GoBricks custom colors; official LDraw part library required.']
    for code,c in COLORS.items():
        rows.append(f'0 !COLOUR GoBricks_{c["name"].replace(" ","_")} CODE {10000+int(code)} VALUE {c["hex"]} EDGE #333333')
    by={p['id']:p for p in model['parts']}
    for step in model['steps']:
        rows.append('0 // '+step['title'])
        for id in step['parts']:
            p=by[id];M,t=ldraw_transform(p)
            rows.append('1 '+str(10000+int(p['color']))+' '+' '.join(f'{n:g}' for n in (*t,*(v for row in M for v in row)))+' '+p['part']+'.dat')
        rows.append('0 STEP')
    return '\n'.join(rows)+'\n'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def output_names(model,style='studio'):
    names={'model.json','model.ldr','catalog.json','parts.csv','validation.json','instructions.pdf','instructions/index.html','instructions/steps.json'}
    names.update(f'renders/{v}.png' for v in VIEWS)
    for n in range(1,len(model['steps'])+1):
        names.add(f'instructions/step-{n:03}.png');names.add(f'instructions/map-{n:03}.svg')
    if style=='technical':
        names.update(f'instructions/parts/{p["part_id"]}-{p["color_id"]}.png' for p in inventory(model['parts']))
    return names
