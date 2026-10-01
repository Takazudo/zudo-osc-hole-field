import copy
import json
from pathlib import Path
import unittest
from scripts.pcbgen.ground_network_incidence import build,bind_native_contacts


class GroundNetworkIncidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=[json.loads(Path(p).read_text()) for p in ['design/partition/partition.json','design/reports/io-partition.json','design/partition/loom-candidate.json','design/partition/harness-wire-evidence.json']]
        cls.graph=build(*cls.inputs)

    def test_actual_complete_source_graph_and_exact_column_balance(self):
        graph=self.graph
        self.assertEqual(graph['counts']['GH_ground_wires'],380)
        self.assertEqual(graph['counts']['main_ground_wires'],9)
        self.assertEqual(graph['counts']['JL_P_utility_ground_wires'],4)
        self.assertEqual(graph['counts']['source_own_load_contacts'],{'JL':1070,'JR':896,'P':214,'K':1903,'EL':60,'O1':0,'O2':0,'O3':0,'O4':0,'O5':0})
        nodes={r['id'] for r in graph['contacts']}
        for edge in graph['wire_edges']:
            self.assertEqual(sum(edge['incidence'].values()),0)
            self.assertEqual(set(edge['incidence']),{edge['from_contact'],edge['to_contact']})
            self.assertTrue(set(edge['incidence'])<=nodes)

    def test_missing_utility_wrong_pin_and_duplicate_source_fail(self):
        for mutation in ['utility','pin','duplicate']:
            p,io,loom,wire=copy.deepcopy(self.inputs)
            if mutation=='utility':p['harnesses']=[h for h in p['harnesses'] if h['id']!='JL-P-1']
            elif mutation=='pin':
                h=next(h for h in p['connectors'] if h['id']=='JL-P-1-P');h['pin_map']['2']='FOREIGN'
            else:p['connectors'].append(p['connectors'][0])
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):build(p,io,loom,wire)

    def test_missing_own_load_and_wrong_terminal_face_fail_native_binding(self):
        source=next(r for r in self.graph['contacts'] if r['board']=='JL' and r['kind']=='fitted_source_contact')
        terminal=next(r for r in self.graph['contacts'] if r['board']=='JL' and r['kind']=='GH_terminal')
        graph={**self.graph,'contacts':[source,terminal],
            'board_fitted_package_refs':{'JL':[source['ref']]}}
        def pad(row,uid):return {'ref':row['ref'],'pad':row['pad'],'uuid':uid,'net':'AGND','copper':{'B.Cu':[]},'xy_mm':[0,0]}
        native={'board_id':'osc-jack-left','board_sha256':'fixture','coordinate_frame':{'source_to_native_translation_mm':[100,50]},
            'items':[pad(source,'own'),pad(terminal,'GH')],'main_rail_members':{'AGND':['own','GH']}}
        self.assertEqual(bind_native_contacts(graph,{'JL':native})['boards']['JL']['contact_count'],2)
        changed={**graph,'contacts':[terminal]}
        with self.assertRaisesRegex(ValueError,'own-load'):bind_native_contacts(changed,{'JL':native})
        changed=copy.deepcopy(native);changed['items'][1]['copper']={'F.Cu':[]}
        with self.assertRaisesRegex(ValueError,'physical face'):bind_native_contacts(graph,{'JL':changed})


if __name__=='__main__':unittest.main()
