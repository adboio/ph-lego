"""Embed the assembly's LDraw meshes without fetches or a local server."""
import array
import base64
import json
import re
import sys
from pathlib import Path

from bricklib import COLORS, PARTS
from geometry import ldraw_transform, mesh

ROOT = Path(__file__).resolve().parents[1]


def encoded(values, kind):
    data = array.array(kind, values)
    if sys.byteorder != 'little':
        data.byteswap()
    return base64.b64encode(data.tobytes()).decode('ascii')


def assembly_data(model):
    geometries = {}
    for pid in sorted({p['part'] for p in model['parts']}):
        vertices, faces = mesh(pid + '.dat')
        c = PARTS[pid]
        center = (0, c['ldraw_bottom'] - c['height'] * 4, 0)
        positions = [center[i] + (v[i] - center[i]) * .995 for v in vertices for i in range(3)]
        triangles = [n for face in faces for j in range(1, len(face)-1)
                     for n in (face[0], face[j], face[j+1])]
        geometries[pid] = {'positions': encoded(positions, 'f'), 'indices': encoded(triangles, 'I')}
    step_of = {pid: i for i, step in enumerate(model['steps']) for pid in step['parts']}
    instances = []
    for p in model['parts']:
        m, t = ldraw_transform(p)
        matrix = [v * .04 for row, sign in ((0, 1), (2, 1), (1, -1))
                  for v in (*[sign * n for n in m[row]], sign * t[row])]
        matrix += [0, 0, 0, 1]
        instances.append({'id': p['id'], 'part': p['part'], 'color': COLORS[p['color']]['hex'],
                          'step': step_of[p['id']], 'matrix': matrix})
    return {'geometries': geometries, 'instances': instances}


def embed(page, model):
    controls = (ROOT/'vendor/OrbitControls-0.160.1.js').read_text()
    controls = re.sub(r"import\s*\{([\s\S]*?)\}\s*from 'three';", r'const {\1} = THREE;', controls, count=1)
    controls = controls.replace('export { OrbitControls };', 'window.OrbitControls = OrbitControls;')
    library = (ROOT/'vendor/three-0.160.1.min.js').read_text()
    license_text = (ROOT/'vendor/THREE-LICENSE.txt').read_text()
    asset = json.dumps(assembly_data(model), separators=(',', ':'))
    css = (ROOT/'scripts/viewer.css').read_text()
    js = (ROOT/'scripts/viewer.js').read_text()
    controls_html = '''<div class="viewer-toolbar" role="group" aria-label="Model view">
<button id="view-3d" type="button" aria-pressed="true">3D model</button>
<button id="view-image" type="button" aria-pressed="false">Step illustration</button>
<label>Show <select id="model-scope"><option value="full">Complete model</option><option value="step">Current step</option></select></label>
<button id="model-reset" type="button">Reset view</button>
</div><div id="model-viewer" class="model-viewer"><p id="viewer-loading">Loading 3D model…</p></div>
<p id="viewer-status" class="view" aria-live="polite"></p>
<p id="viewer-help" class="view">Drag to rotate · scroll or pinch to zoom · right-drag to pan. Focus the model and use arrow keys to pan, + / − to zoom, or Home to reset.</p>'''
    page = page.replace('</style>', css + '</style>', 1)
    page = page.replace('<img class="assembly" id="assembly"', controls_html + '<img class="assembly" hidden id="assembly"', 1)
    page = page.replace("function show(){const s=", "function show(){window.maxViewer?.setStep(index);const s=", 1)
    page = page.replace("matches('select,input,textarea')", "matches('select,input,textarea,canvas')")
    scripts = '\n'.join([
        '<!-- Three.js and OrbitControls: MIT license\n' + license_text + '\n-->',
        '<!-- Meshes: LDraw Parts Library contributors, CC BY 4.0. https://www.ldraw.org/ -->',
        '<script type="application/json" id="model-geometry">' + asset + '</script>',
        '<script>' + library.replace('</script', '<\\/script') + '</script>',
        '<script>(()=>{' + controls + '})();</script>',
        '<script>' + js + '</script>'])
    return page.replace('</html>', scripts + '</html>')
