import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from settlement import collect, sha


class SettlementGate(unittest.TestCase):
    def fixture(self,root):
        base,clean,fresh=[root/n for n in ('base','clean','fresh')]
        for d in (base,clean,fresh):
            d.mkdir();(d/'osc-jack-left.kicad_pcb').write_text('test fixture')
        h=sha(base/'osc-jack-left.kicad_pcb')
        snapshot={'board_sha256':h,'version':'10.0.6','groups':{'N':[['pad']]},'objects':{'pad':{'net':'N'}},'native_open_edges':0}
        drc={'kicad_version':'10.0.6','schematic_parity':[],'violations':[],'unconnected_items':[]}
        comparison={'accepted_connectivity_only':True,'baseline_sha256':h,'candidate_sha256':h,'target_net_closed':{'N':True}}
        power={'version':'10.0.6','board_sha256':h,'accepted_native_connections_only':True,'paths':[{}]*6}
        audit={'raw_sha256':h,'accepted_identity_only':True,'new_objects':0}
        def put(d,n,v):(d/n).write_text(json.dumps(v))
        put(base,'connectivity-complete.json',snapshot);put(base,'drc-first.json',drc)
        put(clean,'prepare-receipt.json',{'canonical_sha256':h,'retired_private_copper':[],'retired_local_supply_copper':[],'private_net_owners':{'N':['U']}})
        (fresh/'prepare-receipt.json').write_bytes((clean/'prepare-receipt.json').read_bytes())
        audit.update(receipt_sha256=sha(clean/'prepare-receipt.json'),canonical_sha256=h)
        for n,v in [('drc-signals-pass1.json',drc),('connectivity-complete-pass1.json',snapshot),('connectivity-comparison-pass1.json',comparison),('power-connections-pass1.json',power),('identity-audit-pass1.json',audit)]:put(clean,n,v)
        for label,folder in [('2',clean),('3',clean),('fresh',fresh)]:
            for prefix,v in [('drc',drc),('connectivity',snapshot),('comparison',comparison),('power',power),('identity',audit)]:put(folder,f'{prefix}-pass{label}.json',v)
        return base,clean,fresh

    def run_case(self,mutation=None):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);args=self.fixture(root)
            if mutation:mutation(*args)
            collect(*args,root/'out.json')
            return json.loads((root/'out.json').read_text())

    def test_four_bound_passes(self):self.assertTrue(self.run_case()['accepted_bounded_native_electrical_pilot'])

    def test_fresh_membership_drift_rejected(self):
        def mutate(b,c,f):
            p=f/'connectivity-passfresh.json';d=json.loads(p.read_text());d['objects']['pad']['net']='OTHER';p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.run_case(mutate)

    def test_native_error_rejected(self):
        def mutate(b,c,f):
            p=c/'drc-pass2.json';d=json.loads(p.read_text());d['violations']=[{'severity':'error','type':'short','items':[]}];p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.run_case(mutate)

    def test_new_uncapped_warning_rejected(self):
        def mutate(b,c,f):
            p=c/'drc-pass3.json';d=json.loads(p.read_text());d['violations']=[{'severity':'warning','type':'track_dangling','items':[{'uuid':'new'}]}];p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.run_case(mutate)

    def test_changed_fresh_board_rejected(self):
        with self.assertRaises(ValueError):self.run_case(lambda b,c,f:(f/'osc-jack-left.kicad_pcb').write_text('changed'))

    def test_receipt_changed_after_native_audit_rejected(self):
        def mutate(b,c,f):
            p=c/'prepare-receipt.json';d=json.loads(p.read_text());d['retired_private_copper']=[{'uuid':'unreviewed'}]
            for folder in (c,f):(folder/'prepare-receipt.json').write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.run_case(mutate)

    def test_additional_capped_warning_category_rejected(self):
        def mutate(b,c,f):
            for p in [b/'drc-first.json',*c.glob('drc-*.json'),*f.glob('drc-*.json')]:
                d=json.loads(p.read_text());d['violations']=[{'type':'track_dangling','severity':'warning','items':[{'uuid':str(i)}]} for i in range(199)];p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.run_case(mutate)

if __name__=='__main__':unittest.main()
