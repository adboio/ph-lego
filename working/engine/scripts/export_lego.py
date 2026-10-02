"""Create a LEGO sourcing variant without changing the GoBricks model."""
import copy
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from bricklib import COLORS, PARTS, dumps, inventory, ldraw, validate
from geometry import bounds

BRICKLINK_COLORS = {'031': 2, '081': 88, '082': 120, '080': 11}
LDRAW_COLORS = {'031': 19, '081': 70, '082': 308, '080': 0}
PLANS = {
    '3010': [('3004', 0, 0, 0), ('3004', 2, 0, 0)],
    '3002': [('3003', 0, 0, 0), ('3004', 2, 0, 90)],
    '3034': [('3020', 0, 0, 0), ('3020', 4, 0, 0)],
    '3032': [('3020', 0, 0, 90), ('3020', 2, 0, 90), ('3020', 4, 0, 90)],
    '3036': [('3035', 0, 0, 0), ('3020', 0, 4, 0), ('3020', 4, 4, 0)],
}


def cells(part):
    box = bounds(part)
    return {(x, y, z) for x in range(round(box[0]), round(box[3]), 20)
            for y in range(round(box[1]), round(box[4]), 20)
            for z in range(round(box[2]), round(box[5]), 8)}


def replace(part):
    if part['color'] != '082' or part['part'] not in PLANS:
        return [copy.deepcopy(part)]
    assert part.get('orientation', 'up') == 'up'
    assert part['rotation'] in (0, 90)
    children = []
    for i, (pid, dx, dy, rotation) in enumerate(PLANS[part['part']]):
        width, depth = PARTS[pid]['width'], PARTS[pid]['depth']
        if rotation == 90:
            width, depth = depth, width
        if part['rotation'] == 90:
            dx, dy = PARTS[part['part']]['depth'] - dy - depth, dx
        children.append(dict(part, id=f'{part["id"]}-{i+1}', part=pid,
                             x=part['x']+dx, y=part['y']+dy,
                             rotation=(part['rotation']+rotation) % 180))
    coverage = Counter(cell for child in children for cell in cells(child))
    assert set(coverage) == cells(part) and set(coverage.values()) == {1}
    return children


def xml_wanted(rows, condition=None):
    root = ET.Element('INVENTORY')
    for row in rows:
        item = ET.SubElement(root, 'ITEM')
        values = dict(ITEMTYPE='P', ITEMID=row['bricklink_part_id'],
                      COLOR=row['bricklink_color_id'], MINQTY=row['quantity'])
        if condition:
            values['CONDITION'] = condition
        for key, value in values.items():
            ET.SubElement(item, key).text = str(value)
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='unicode') + '\n'


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export(source, out):
    original = json.loads(source.read_text())
    model = copy.deepcopy(original)
    replacements = {p['id']: replace(p) for p in original['parts']}
    model['parts'] = [q for p in original['parts'] for q in replacements[p['id']]]
    model['id'] = 'max-posthog-lego'
    model['title'] = 'Max the PostHog Hedgehog - LEGO sourcing variant'
    model['description'] = ('LEGO sourcing variant with cataloged colors. Smaller bricks and plates '
                            'replace five difficult Dark Brown part types in the same occupied spaces. '
                            'Follow the original guide with the substitution sheet. Not physically tested.')
    changes = []
    by_id = {p['id']: p for p in original['parts']}
    for number, step in enumerate(model['steps'], 1):
        for pid in step['parts']:
            children = replacements[pid]
            if len(children) > 1:
                old = by_id[pid]
                changes.append(dict(step=number, original_instance=pid, original_part=old['part'],
                                    color='Dark Brown', x=old['x'], y=old['y'], z=old['z'],
                                    rotation=old['rotation'], replacements='; '.join(
                                        f'{p["part"]} at x{p["x"]} y{p["y"]} z{p["z"]} rot{p["rotation"]}'
                                        for p in children)))
        step['parts'] = [p['id'] for pid in step['parts'] for p in replacements[pid]]
    report = validate(model)
    if not report['passed']:
        raise ValueError(dumps(report))
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for item in inventory(model['parts']):
        pid = '3069' if item['part_id'] == '3069b' else item['part_id']
        color = BRICKLINK_COLORS[item['color_id']]
        rows.append(dict(bricklink_part_id=pid, part_name=item['part_name'],
                         bricklink_color_id=color, color_name=item['color_name'],
                         quantity=item['quantity'],
                         catalog_url=f'https://www.bricklink.com/v2/catalog/catalogitem.page?P={pid}&C={color}'))
    for name, condition in [('max-lego-new.xml', 'N'), ('max-lego-any-condition.xml', None)]:
        text = xml_wanted(rows, condition)
        parsed = ET.fromstring(text)
        assert sum(int(i.findtext('MINQTY')) for i in parsed) == len(model['parts'])
        assert len(parsed) == len(rows)
        (out/name).write_text(text)
    write_csv(out/'parts.csv', rows)
    write_csv(out/'substitutions.csv', changes)
    (out/'model.json').write_text(dumps(model))
    (out/'validation.json').write_text(dumps(report))
    lines = []
    for line in ldraw(model).splitlines():
        if line.startswith('0 !COLOUR') or 'GoBricks custom colors' in line:
            continue
        if line.startswith('1 '):
            words = line.split()
            words[1] = str(LDRAW_COLORS[f'{int(words[1])-10000:03}'])
            line = ' '.join(words)
        lines.append(line)
    (out/'max-lego.ldr').write_text('\n'.join(lines)+'\n')
    print(dumps(dict(pieces=len(model['parts']), lots=len(rows), substitutions=len(changes),
                     validation=report['passed'], warnings=len(report['warnings']))))


if __name__ == '__main__':
    export(Path(sys.argv[1]), Path(sys.argv[2]))
