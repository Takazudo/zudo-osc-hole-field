import json,unittest,xml.etree.ElementTree as ET
import stage10_visualize as v
class DrawingTests(unittest.TestCase):
 def test_all_packages_once_and_source_boundary(self):
  r=json.loads((v.OUT/'mechanical-report.json').read_text());body=v.draw(r);root=ET.fromstring(body)
  ids=[x.attrib['id'][8:]for x in root.iter()if x.attrib.get('id','').startswith('package-')]
  self.assertEqual(len(ids),90);self.assertEqual(set(ids),set(r['placements']));self.assertIn('physical acceptance OPEN',body)
 def test_board_plane_change_visible(self):
  r=json.loads((v.OUT/'mechanical-report.json').read_text());r['board_pad_faces_mm']['A01-core']['panel']=77.123
  self.assertIn('Z77.123 mm',v.draw(r))
if __name__=='__main__':unittest.main()
