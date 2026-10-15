import copy
import json
import math
import unittest
import stage4_regions as r

class RegionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=json.loads((r.OUT/'direct-study-report.json').read_text())['best']
        cls.rows=cls.b['paths']
    def test_octile_halfplanes(self):
        for x in range(-12,13):
            for y in range(-12,13):
                self.assertAlmostEqual(r.octile((0,0),(x,y)),max(a*x+b*y for a,b in r.NORMALS))
    def test_domains_and_triangle_inequality(self):
        for row in self.rows:
            d=r.endpoint_domain(row)
            if row['total_mm']<=300:
                self.assertTrue(all(a*row['other_pad_mm'][0]+b*row['other_pad_mm'][1]<=c+1e-8 for a,b,c in d['halfplanes']))
            if row['DIN_pad_mm'] is not None:
                f=r.endpoint_domain(row,row['DIN_pad_mm']);inside=all(a*row['other_pad_mm'][0]+b*row['other_pad_mm'][1]<=c+1e-8 for a,b,c in f['halfplanes'])
                self.assertEqual(inside,row['total_mm']<=300)
    def test_negative_radius_empty(self):
        self.assertEqual([],r.polygon([[x,y,-1] for x,y in r.NORMALS]))
    def test_disjoint_octagons_empty(self):
        h=[[x,y,1] for x,y in r.NORMALS]+[[x,y,1+10*x] for x,y in r.NORMALS]
        self.assertEqual([],r.polygon(h))
    def test_touching_octagons_not_empty(self):
        h=[[x,y,1] for x,y in r.NORMALS]+[[x,y,1+2*x] for x,y in r.NORMALS]
        self.assertTrue(r.polygon(h))
    def test_preserved_path_recalculation(self):
        vals=r.evaluate_paths(self.rows,{r.signature(x):x['other_pad_mm'] for x in self.rows},{r.signature(x):x['DIN_pad_mm'] for x in self.rows if x['DIN_pad_mm'] is not None})
        for a,b in zip(vals,self.rows):self.assertAlmostEqual(a['total_mm'],b['total_mm'])
    def test_missing_duplicate_rows_rejected(self):
        for rows in (self.rows[:-1],self.rows[:-1]+self.rows[:1]):
            with self.assertRaises(ValueError):r.evaluate_paths(rows,{}, {})
    def test_wrong_net_instance_uid_rejected(self):
        for field,value in (('net','WRONG'),('instance','O6')):
            rows=copy.deepcopy(self.rows);rows[0][field]=value
            with self.assertRaises(ValueError):r.validate_rows(rows)
        rows=copy.deepcopy(self.rows);rows[0]['actual_identity']['actual_panel_uid']='C:O5.WRONG'
        with self.assertRaises(ValueError):r.validate_rows(rows)
    def test_changed_front_budget_rejected(self):
        rows=copy.deepcopy(self.rows);next(x for x in rows if 'link' in x)['segments']['front_trace_mm']-=1
        with self.assertRaises(ValueError):r.validate_rows(rows)
    def test_connector64_halfplanes_match_exact_sum(self):
        rows=[x for x in self.rows if x['instance']=='O5' and x['DIN_pad_mm'] is not None]
        domain=r.connector_translation_domain(rows)
        for x in (-100,-20,0,20,100):
            for y in (-100,-20,0,20,100):
                for row,c in zip(rows,domain['constraints']):
                    fixed,n,anchor=r.budget(row)
                    if 'link' not in row:anchor=[anchor[0]+6,anchor[1]]
                    d=[row['DIN_pad_mm'][0]+x,row['DIN_pad_mm'][1]+y]
                    length=fixed+14+1.15*(r.octile(anchor,d)+r.octile(d,row['other_pad_mm']))
                    inside=all(a*x+b*y<=z+1e-8 for a,b,z in c['halfplanes_translation_mm'])
                    self.assertEqual(inside,length<=300+1e-8)
        self.assertTrue(domain['domain_empty'])
        self.assertEqual(1,len(domain['conflict_row_indices']))
        row=rows[domain['conflict_row_indices'][0]];fixed,n,anchor=r.budget(row)
        if 'link' not in row:anchor=[anchor[0]+6,anchor[1]]
        self.assertGreater(fixed+14+1.15*r.octile(anchor,row['other_pad_mm']),300)
    def test_budget_mutations_rejected(self):
        row=next(x for x in self.rows if x['DIN_pad_mm'] is not None and 'link' in x)
        for field in ('wire_max_mm','GH_pair_mm','DIN_mm'):
            q=copy.deepcopy(row);q['segments'][field]-=1
            with self.assertRaises(ValueError):r.endpoint_domain(q)
        q=copy.deepcopy(row);q['length_limit_mm']=301
        with self.assertRaises(ValueError):r.endpoint_domain(q)
    def test_shared_octave_and_reference_translation(self):
        octrow=next(x for x in self.rows if x['net']=='OSC_OCT0');refrow=next(x for x in self.rows if 'link' not in x)
        for row in (octrow,refrow):
            domain=r.translation_domain([row],'shared');h=domain['constraints'][0]['halfplanes_translation_mm'];self.assertEqual(8,len(h))
            self.assertTrue(all(math.isfinite(v) for hp in h for v in hp))

if __name__=='__main__':unittest.main()
