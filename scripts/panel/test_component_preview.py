"""Fast source checks for browser-only component display, no CAD dependencies."""
from pathlib import Path
import hashlib,json,subprocess,unittest
R=Path(__file__).resolve().parents[2]
P=R/'project/osc-hole-field/workbench/component-preview'
class ComponentPreviewSourceTest(unittest.TestCase):
 def test_receipts_and_deterministic_builds(self):
  r=json.loads((P/'models/receipt.json').read_text())
  for name,digest in r['sha256'].items():self.assertEqual(hashlib.sha256((P/'models'/name).read_bytes()).hexdigest(),digest)
  for command in [['python3',str(P/'build.py'),'--check'],['node',str(P.parent/'current-editor/build.cjs'),'--check']]:subprocess.run(command,cwd=R,check=True,capture_output=True)
 def test_mesh_orientation_and_shaft_dimension(self):
  m=json.loads((P/'models/meshes.json').read_text())
  def volume(s,transform):
   p=s['positions'];v=[transform(*p[i:i+3]) for i in range(0,len(p),3)];ind=s['indices'];total=0
   for i in range(0,len(ind),3):
    a,b,c=[v[ind[i+j]] for j in range(3)]
    total+=sum(a[j]*(b[(j+1)%3]*c[(j+2)%3]-b[(j+2)%3]*c[(j+1)%3]) for j in range(3))/6
   return total
  # Pin the runtime rigid transforms; a reflection previously reversed pot normals.
  js=(P/'viewer.js').read_text()
  transforms={'pot':('[x-6.9960603727775,y-2.5,z-9.89]',lambda x,y,z:(x-6.9960603727775,y-2.5,z-9.89)), 'jack':('[x-.8,-z,y-12]',lambda x,y,z:(x-.8,-z,y-12))}
  for name,(code,transform) in transforms.items():
   self.assertIn(code,js)
   for solid in m[name]['solids']:
    original=volume(solid,lambda x,y,z:(x,y,z));derived=volume(solid,transform)
    self.assertGreater(original,0);self.assertAlmostEqual(original,derived,places=6)
  p=m['pot']['solids'][0]['positions'];shaft=[p[i:i+3] for i in range(0,len(p),3) if 8<p[i+2]<19.5]
  self.assertTrue(shaft)
  self.assertLessEqual(max(((x-6.9960603727775)**2+(y-2.5)**2)**.5 for x,y,z in shaft),3.000001)
if __name__=='__main__':unittest.main()
