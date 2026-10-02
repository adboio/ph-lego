import unittest,copy
from bricklib import validate,ldraw,PARTS
from geometry import sites,shape,mesh,ldraw_transform,mv,add

def part(i,p='3005',x=0,y=0,z=0,r=0,face='up'):
 return dict(id=i,part=p,color='082',x=x,y=y,z=z,rotation=r,orientation=face)
def model(ps):
 return dict(schema_version='max-1.0',id='test',title='Test',description='Test assembly',author='Test',license='UNLICENSED',parts=ps,steps=[dict(title='Add part',parts=[p['id']]) for p in ps])
class Connections(unittest.TestCase):
 def test_vertical(self):self.assertTrue(validate(model([part('a'),part('b',z=3)]))['passed'])
 def test_missing_stud(self):self.assertFalse(validate(model([part('a','3070b'),part('b',z=1)]))['passed'])
 def test_float(self):self.assertFalse(validate(model([part('a'),part('b',z=4)]))['passed'])
 def test_overlap(self):self.assertFalse(validate(model([part('a'),part('b',z=2)]))['passed'])
 def test_snot(self):self.assertTrue(validate(model([part('a','87087'),part('b','98138',y=-.4,z=.5,face='front')]))['passed'])
 def test_wrong_side_height(self):self.assertFalse(validate(model([part('a','87087'),part('b','98138',y=-.4,z=1,face='front')]))['passed'])
 def test_curved_no_top_studs(self):self.assertFalse(validate(model([part('a','3004',r=90),part('b','11477',z=3),part('c',z=5)]))['passed'])
 def test_rotation_width(self):self.assertEqual(shape(part('a','3001',r=90)),(2,4,3))
 def test_front_dimensions(self):self.assertEqual(shape(part('a','3020',r=90,face='front')),(2,.4,10))
 def test_ldraw_side_transform(self):
  p=part('a','98138',y=-.4,z=.5,face='front');M,t=ldraw_transform(p)
  self.assertEqual(add(mv(M,(0,8,0)),t),(10,-14,0))
 def test_muzzle_endpoints(self):self.assertEqual(len(sites(part('a','27925'))[1]),2)
 def test_round_brick_has_no_center_studs(self):
  tops,bottoms=sites(part('a','87081'));self.assertEqual(len(tops),8);self.assertEqual(len(bottoms),8);self.assertNotIn((30,30,24),[pos for pos,normal in tops])
 def test_round_brick_rim_support(self):
  self.assertTrue(validate(model([part('a','87081'),part('b','14769',x=1,y=2,z=3)]))['passed'])
 def test_round_brick_center_tile_floats(self):
  self.assertFalse(validate(model([part('a','87081'),part('b','14769',x=1,y=1,z=3)]))['passed'])
 def test_mesh_dimensions(self):
  for pid,c in PARTS.items():
   v,f=mesh(pid+'.dat');self.assertTrue(v and f,pid)
   # Mesh coordinates and the export share the identical transform.
   p=part('a',pid);M,t=ldraw_transform(p);v=[add(mv(M,q),t) for q in v]
   for axis,extent in [(0,c['width']*20),(2,c['depth']*20)]:
    self.assertGreaterEqual(min(q[axis] for q in v),-4.5 if pid in ['87087','11211'] else -.5,pid)
    self.assertLessEqual(max(q[axis] for q in v),extent+4.5,pid)
if __name__=='__main__':unittest.main()
