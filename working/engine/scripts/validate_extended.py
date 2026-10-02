"""Conservative body envelopes and explicit oriented stud mating, not physics."""
from collections import defaultdict,Counter
from geometry import bounds,sites,basis

def run(model,report):
    ps=model['parts'];errors=report['errors'];warnings=report['warnings'];by={p['id']:p for p in ps}
    ids=[i for s in model['steps'] for i in s['parts']]
    if len(by)!=len(ps):errors.append('Duplicate instance IDs')
    if Counter(ids)!=Counter(by.keys()):errors.append('Steps must cover every instance exactly once')
    if errors:return report
    order={i:n for n,i in enumerate(ids)};box={p['id']:bounds(p) for p in ps};graph=defaultdict(set);studs=defaultdict(list)
    for p in ps:
        top,_=sites(p)
        for pos,normal in top:studs[(pos,normal)].append(p['id'])
    for n,p in enumerate(ps):
        a=box[p['id']]
        for q in ps[:n]:
            b=box[q['id']]
            if all(min(a[i+3],b[i+3])-max(a[i],b[i])>1e-5 for i in range(3)):
                errors.append('Body envelope collision: '+p['id']+' / '+q['id'])
        _,bottom=sites(p);supported=0;previous=0
        for pos,normal in bottom:
            matches=studs[(pos,tuple(-v for v in normal))]
            for other in matches:
                if other==p['id']:continue
                graph[p['id']].add(other);graph[other].add(p['id']);supported+=1
                if order[other]<order[p['id']]:previous+=1
        if a[2]>1e-5 and not previous:errors.append(p['id']+': no mating stud on an earlier part')
        elif previous and previous<len(bottom):warnings.append(f'{p["id"]}: {previous}/{len(bottom)} underside sites connected; inspect overhang')
        # Sweep the body envelope outward along its insertion axis. Stud insertion itself is a legal mating overlap.
        normal=tuple(-v for v in bottom[0][1]) if bottom else (0,0,1)
        axis=next(i for i,v in enumerate(normal) if v);sgn=normal[axis]
        for q in ps:
            if order[q['id']]>=order[p['id']]:continue
            b=box[q['id']]
            if all(min(a[i+3],b[i+3])-max(a[i],b[i])>1e-5 for i in range(3) if i!=axis):
                if (sgn>0 and b[axis]>=a[axis+3]-1e-5) or (sgn<0 and b[axis+3]<=a[axis]+1e-5):
                    errors.append(p['id']+': insertion blocked by '+q['id']);break
    unseen=set(by);components=[]
    while unseen:
        stack=[min(unseen)];comp=set()
        while stack:
            i=stack.pop()
            if i in comp:continue
            comp.add(i);stack.extend(graph[i]-comp)
        unseen-=comp;components.append(sorted(comp))
    if len(components)!=1:errors.append(f'{len(components)} disconnected assemblies')
    mins=[min(b[i] for b in box.values()) for i in range(3)];maxs=[max(b[i+3] for b in box.values()) for i in range(3)]
    report.update(passed=not errors,part_count=len(ps),step_count=len(model['steps']),connection_components=len(components),dimensions_mm=[round((b-a)*.4,2) for a,b in zip(mins,maxs)])
    report['checks']=['extended schema','unique instances','step coverage','conservative body envelopes','oriented stud mating','assembly order','axis insertion envelopes','final connectivity']
    report['not_checked']+=['exact concave mesh interference','material tolerances','physical load capacity']
    if sum(p['z']==0 for p in ps)>1:warnings.append('Foundation parts start loose; align them on a flat table until the crossing plates join them.')
    return report
