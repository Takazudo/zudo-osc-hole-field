import unittest,copy,json
from adapter import mapping,bind_native,warning_compare,fingerprint
from scripts.pcbgen.copper_identity import propose_normalization
U='11111111-1111-4111-8111-111111111111'
def fixture():return '(kicad_pcb\n'+''.join(f'(segment (start {x} 0) (end {x+1} 0) (width 0.3) (layer "F.Cu") (net "AGND") (uuid "{U}"))\n' for x in (0,2))+')\n'
class Adapter(unittest.TestCase):
 def setUp(self):self.raw=fixture();self.manifest,self.after=propose_normalization(self.raw);self.maps=mapping(self.raw,self.after,self.manifest)
 def test_duplicate_uuid_distinct_occurrences_retained(self):
  for m in self.maps:self.assertEqual(set(bind_native([{'signature':json.loads(k)} for k in reversed(m)],m)),{'copper:0','copper:1'})
 def test_missing_duplicate_unknown(self):
  m=self.maps[0];rows=[{'signature':json.loads(k)} for k in m]
  for bad in [rows[:-1],rows+rows[:1],[{'signature':['unknown']}]]:
   with self.assertRaises(ValueError):bind_native(bad,m)
 def test_malformed_manifest(self):
  for key,value in [('input_board_sha256','0'*64),('renames',[]),('output_board_sha256','0'*64)]:
   m=copy.deepcopy(self.manifest);m[key]=value
   with self.assertRaises(ValueError):mapping(self.raw,self.after,m)
 def test_changed_geometry(self):
  with self.assertRaises(ValueError):mapping(self.raw,self.after.replace('(width 0.3)','(width 0.4)',1),self.manifest)
 def test_capped_warning_never_invariance_pass(self):
  d={'kicad_version':'10.0.6','schematic_parity':[],'violations':[{'type':'silk_overlap','severity':'warning','items':[{'uuid':U}]}]*199}
  self.assertFalse(warning_compare(d,d,self.maps)['complete'])
 def test_ambiguous_warning_never_collapsed(self):
  d={'kicad_version':'10.0.6','schematic_parity':[],'violations':[{'type':'silk_overlap','severity':'warning','items':[{'uuid':U}]}]}
  self.assertFalse(warning_compare(d,d,self.maps)['complete'])
 def test_raw_warning_multiplicity_changed(self):
  d={'kicad_version':'10.0.6','schematic_parity':[],'violations':[{'type':'other','severity':'warning','items':[{'uuid':'pad-id'}]}]};e=copy.deepcopy(d);e['violations']*=2
  with self.assertRaises(ValueError):warning_compare(d,e,self.maps)
 def test_uncapped_empty_only_scoped_pass(self):
  d={'kicad_version':'10.0.6','schematic_parity':[],'violations':[]};self.assertTrue(warning_compare(d,d,self.maps)['complete'])


class Serialization(unittest.TestCase):
 def test_serialized_full_metadata_changes_detected(self):
  from adapter import serialized_capture,mapping
  raw=fixture();manifest,after=propose_normalization(raw);maps=mapping(raw,after,manifest)
  self.assertEqual(serialized_capture(raw,maps[0]),serialized_capture(after,maps[1]))
  changed=after.replace('(kicad_pcb','(kicad_pcb (setup (mask_clearance 0.2))',1)
  self.assertNotEqual(serialized_capture(raw,maps[0]),serialized_capture(changed,maps[1]))
  # A flag omitted by simple numeric geometry binding still changes full copper capture.
  changed=after.replace('(width 0.3)','(width 0.3) (locked yes)',1)
  self.assertNotEqual(serialized_capture(after,maps[1]),serialized_capture(changed,maps[1]))
 def test_protocol_requires_four_and_three_settled_states(self):
  from adapter import validate_protocol,SHAPE_KEYS
  def row(phase):return dict(phase=phase,native_version='10.0.6',mapping_sha256='m',producer_sha256={'x':'p'},context_sha256={'r':'c'},input_sha256={'x':'i'},**{k:[] for k in SHAPE_KEYS})
  phases={p:[row(p) for _ in range(3)] for p in ('before','after','before_fresh','after_fresh')}
  self.assertFalse(validate_protocol(phases)['adopted'])
  missing=copy.deepcopy(phases);missing.pop('after_fresh')
  with self.assertRaises(ValueError):validate_protocol(missing)
  short=copy.deepcopy(phases);short['after'].pop()
  with self.assertRaises(ValueError):validate_protocol(short)
  drift=copy.deepcopy(phases);drift['after'][1]['zones']=['changed']
  with self.assertRaises(ValueError):validate_protocol(drift)
  drift=copy.deepcopy(phases)
  for r in drift['after_fresh']:r['native_noncopper_blocks']=['changed']
  with self.assertRaises(ValueError):validate_protocol(drift)

if __name__=='__main__':unittest.main()
