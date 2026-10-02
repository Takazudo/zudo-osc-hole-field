"""Routing orchestration regressions; all KiCad/router processes are simulated.

These tests run the real route.main and file handling against temporary fixtures.
They do not run pcbnew, the pinned KiCad oracle, Freerouting, or physical hardware.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from scripts.pcbgen import route


def drc_report(*, open_edges=0, rule_errors=0, parity_errors=0, warnings=0):
    return {
        'kicad_version': '10.0.6',
        'source': 'fixture-native-gate.kicad_pcb',
        'included_severities': ['error','warning','exclusion'],
        'violations': [{'severity': 'error'} for _ in range(rule_errors)]
                      + [{'severity': 'warning'} for _ in range(warnings)],
        'unconnected_items': [
            {'items': [{'description': f'Pad [NET{i}]'}]}
            for i in range(open_edges)
        ],
        'schematic_parity': [{} for _ in range(parity_errors)],
    }


class RoutingGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.board_id = 'fixture-native-gate'
        self.board = self.root / 'boards' / self.board_id / f'{self.board_id}.kicad_pcb'
        self.board.parent.mkdir(parents=True)
        # An opaque fixture. Never a native CAD or fabrication artifact.
        self.board.write_text('TEST FIXTURE ONLY - NOT A KICAD BOARD\n')
        self.project = self.board.with_suffix('.kicad_pro')
        self.project.write_text(json.dumps({'net_settings': {'classes': [{'name': 'Default'}]}}))
        self.report = self.board.parent / 'reports/routing.json'
        self.report.parent.mkdir()
        self.native = self.report.parent / 'ratsnest.json'
        self.definition = {
            'schema_version': 1, 'board_id': self.board_id,
            'outline': [[0, 0], [20, 0], [20, 20], [0, 20]],
            'corner_radius_mm': 0, 'layers': 2, 'thickness_mm': 1.6,
            'stackup': [{'layer': 'F.Cu'}, {'layer': 'B.Cu'}],
            'mounting_holes': [], 'keepouts': [], 'domains': [], 'placement_uids': [],
            'netlist': 'fixture.net', 'schematic': 'fixture.kicad_sch',
            'routing': {
                'min_track_width_mm': 0.2,
                'net_classes': [{'name': 'Default', 'nets': [], 'track_width_mm': 0.2,
                                 'clearance_mm': 0.2, 'via_diameter_mm': 0.6, 'via_drill_mm': 0.3}],
                'zones': [],
            },
        }
        path = self.root / 'design/boards' / f'{self.board_id}.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(self.definition))
        self.drc_reports = [drc_report(), drc_report()]
        self.native_data = {
            'schema_version': 2, 'board': str(self.board.relative_to(self.root)),
            'board_sha256': hashlib.sha256(self.board.read_bytes()).hexdigest(),
            'native_open_edges_by_net': {}, 'native_open_net_count': 0,
            'named_edge_count_sum': 0, 'named_edge_basis': 'Mock native clusters',
            'native_unconnected_edges': 0, 'multi_pad_candidate_net_count': 2,
        }
        self.native_mode = 'write'
        self.native_calls = 0
        self.commands = []
        self.router_code = 124
        self.router_calls = 0
        self.drc_exit = 0
        self.log = ''

    def set_native_edges(self, edges):
        self.native_data.update(native_open_edges_by_net=edges, native_open_net_count=len(edges),
                                named_edge_count_sum=sum(edges.values()),
                                native_unconnected_edges=sum(edges.values()))

    def run_process(self, command, log=None, check=True):
        self.commands.append(command)
        if 'kicad-cli' in command:
            if self.drc_exit:
                return SimpleNamespace(returncode=self.drc_exit, stdout='simulated oracle failure')
            if not self.drc_reports:
                self.fail('unexpected additional DRC invocation')
            path = self.root / command[command.index('-o') + 1]
            path.write_text(json.dumps(self.drc_reports.pop(0)))
        elif 'scripts/pcbgen/ratsnest.py' in command:
            self.native_calls += 1
            if self.native_mode == 'raise':
                raise RuntimeError('simulated missing native oracle')
            if self.native_mode == 'no-output':
                return SimpleNamespace(returncode=0, stdout='')
            if self.native_mode == 'mutate-board':
                self.board.write_text('changed during native check\n')
            if self.native_mode == 'invalid-json':
                self.native.write_text('{')
            else:
                self.native.write_text(json.dumps(self.native_data))
        elif 'scripts/pcbgen/route_kicad.py' in command and '--stats' in command:
            path = self.root / command[command.index('--stats') + 1]
            path.write_text(json.dumps({
                'via_count': 0, 'via_nets': [], 'total_track_length_mm': 0.0,
                'track_uuids': [], 'zone_count': 0,
                'preexisting_tracks_preserved': 0, 'preexisting_zones_preserved': 0,
            }))
        elif 'scripts/pcbgen/route_kicad.py' not in command:
            self.fail(f'unexpected subprocess: {command}')
        return SimpleNamespace(returncode=0, stdout='')

    def run_router(self, dsn, ses, *args, **kwargs):
        self.router_calls += 1
        if self.router_code == 0:
            ses.write_text('SIMULATED SESSION ONLY\n')
        return self.router_code, 0.01, 0.0, 'synthetic router result\n'

    def invoke(self, *options):
        args = ['route.py', self.board_id, '--threads', '1', '--heap-mb', '256', *options]
        captured = io.StringIO()
        with patch.object(route, 'ROOT', self.root), \
             patch.object(route, 'run', side_effect=self.run_process), \
             patch.object(route, 'read_env', return_value=('not-executed-test-image', 256, 1)), \
             patch.object(route, 'router', side_effect=self.run_router), \
             patch.object(route.sys, 'argv', args), \
             contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            code = route.main()
        self.log = captured.getvalue()
        return code, json.loads(self.report.read_text())

    def retained_report(self, status='ROUTED DRAFT'):
        self.report.write_text(json.dumps({
            'status': status, 'native_unconnected_edge_count': 0,
            'native_board_sha256': 'old-receipt',
            'native_ratsnest_error': 'old-error',
        }))

    def test_missing_or_malformed_drc_categories_cannot_mean_zero(self):
        for key in ('violations','unconnected_items','schematic_parity'):
            for value in ('missing',None,{},0,'', [None]):
                with self.subTest(key=key,value=value):
                    data=drc_report()
                    if value=='missing':del data[key]
                    else:data[key]=value
                    self.drc_reports=[data]
                    code,result=self.invoke()
                    self.assertEqual(code,2)
                    self.assertEqual(result['status'],'PIPELINE FAILED DRAFT')
                    self.assertIn('DRC report requires',result['error'])
                    self.assertEqual(self.router_calls,0)

    def test_wrong_board_scope_and_untyped_violations_fail_closed(self):
        for change in ({'source':'other.kicad_pcb'},
                       {'included_severities':['warning']},
                       {'violations':[{}]}, {'violations':[{'severity':'unknown'}]}):
            with self.subTest(change=change):
                self.drc_reports=[{**drc_report(),**change}]
                code,result=self.invoke()
                self.assertEqual(code,2)
                self.assertEqual(result['status'],'PIPELINE FAILED DRAFT')
                self.assertEqual(self.router_calls,0)

    def test_same_spec_hash_does_not_bypass_changed_project_rules(self):
        code,_=self.invoke()
        self.assertEqual(code,0)
        data=json.loads(self.project.read_text())
        data['net_settings']['classes'][0]['clearance']=0
        data['board']['design_settings']['rules']['min_track_width']=.01
        data['owner_note']='preserve me'
        self.project.write_text(json.dumps(data))
        before=self.board.read_bytes()
        original=self.run_process
        def verify_settings(command,**kwargs):
            if 'kicad-cli' in command:
                project=json.loads(self.project.read_text())
                self.assertEqual(project['net_settings']['classes'][0]['clearance'],.2)
                self.assertEqual(project['board']['design_settings']['rules']['min_track_width'],.2)
                self.assertEqual(project['owner_note'],'preserve me')
            return original(command,**kwargs)
        self.run_process=verify_settings
        self.drc_reports=[drc_report()]
        code,result=self.invoke()
        self.assertEqual(code,0)
        self.assertEqual(result['status'],'UPDATED DRAFT')
        self.assertTrue(result['project_settings_refreshed'])
        self.assertEqual(self.board.read_bytes(),before)
        restored=self.project.read_bytes()
        self.drc_reports=[drc_report()]
        code,result=self.invoke()
        self.assertEqual(code,0)
        self.assertFalse(result['project_settings_refreshed'])
        self.assertEqual(self.project.read_bytes(),restored)

    def test_clean_drc_and_native_zero_succeed(self):
        code, result = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'UPDATED DRAFT')
        self.assertEqual(result['native_gate_status'], 'ZERO OPEN EDGES')
        self.assertEqual(result['native_board_sha256'], hashlib.sha256(self.board.read_bytes()).hexdigest())
        self.assertEqual(self.router_calls, 0)

    def test_native_failure_cannot_leave_success_exit(self):
        self.native_mode = 'raise'
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'PIPELINE FAILED DRAFT')
        self.assertIn('native_ratsnest_error', result)

    def test_positive_native_count_cannot_leave_success_badge(self):
        self.set_native_edges({'NATIVE_NET': 3})
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'INCOMPLETE DRAFT')
        self.assertEqual(result['native_unconnected_edge_count'], 3)

    def test_stale_native_report_is_not_reused(self):
        self.native.write_text(json.dumps(self.native_data))
        self.native_mode = 'no-output'
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'PIPELINE FAILED DRAFT')
        self.assertNotIn('native_unconnected_edge_count', result)
        self.assertFalse(self.native.exists())

    def test_invalid_native_counts_fail_closed(self):
        for key in ('native_unconnected_edges', 'multi_pad_candidate_net_count'):
            for value in (False, True, -1, 0.0, '0', None):
                with self.subTest(key=key, value=value):
                    self.native_data = {'board': str(self.board), 'native_unconnected_edges': 0,
                                        'multi_pad_candidate_net_count': 0}
                    self.native_data[key] = value
                    self.drc_reports = [drc_report(), drc_report()]
                    code, result = self.invoke()
                    self.assertEqual(code, 2)
                    self.assertEqual(result['native_gate_status'], 'NOT RUN')

    def test_non_object_native_report_fails_closed(self):
        self.native_data = []
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn('must be an object', result['native_ratsnest_error'])

    def test_invalid_json_native_report_fails_closed(self):
        self.native_mode = 'invalid-json'
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn('native_ratsnest_error', result)

    def test_wrong_board_receipt_fails_closed(self):
        self.native_data['board'] = 'boards/another-board.kicad_pcb'
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn('different board', result['native_ratsnest_error'])

    def test_changed_board_during_native_check_fails_closed(self):
        self.native_mode = 'mutate-board'
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn('board changed', result['native_ratsnest_error'])

    def test_prepared_rule_errors_skip_router(self):
        self.drc_reports = [drc_report(open_edges=2), drc_report(open_edges=2, rule_errors=1)]
        self.set_native_edges({'NATIVE_NET': 2})
        code, result = self.invoke()
        self.assertEqual(self.router_calls, 0)
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'PIPELINE FAILED DRAFT')

    def test_prepared_parity_errors_skip_router(self):
        self.drc_reports = [drc_report(open_edges=2), drc_report(open_edges=2, parity_errors=1)]
        self.set_native_edges({'NATIVE_NET': 2})
        code, result = self.invoke()
        self.assertEqual(self.router_calls, 0)
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'PIPELINE FAILED DRAFT')

    def test_preparation_can_repair_preexisting_errors(self):
        self.drc_reports = [drc_report(open_edges=2, rule_errors=1), drc_report()]
        code, result = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(self.router_calls, 0)
        self.assertEqual(result['status'], 'ROUTED DRAFT')

    def test_warning_only_prepared_report_allows_router(self):
        self.drc_reports = [drc_report(open_edges=2), drc_report(open_edges=2, warnings=1)]
        self.set_native_edges({'NATIVE_NET': 2})
        code, result = self.invoke()
        self.assertEqual(self.router_calls, 1)
        self.assertEqual(code, 3)
        self.assertEqual(result['status'], 'TIMEOUT DRAFT')

    def test_timeout_is_not_promoted_by_native_zero(self):
        self.drc_reports = [drc_report(open_edges=2), drc_report(open_edges=2)]
        code, result = self.invoke()
        self.assertEqual(code, 3)
        self.assertEqual(result['status'], 'TIMEOUT DRAFT')

    def test_native_failure_preserves_timeout_exit(self):
        self.drc_reports = [drc_report(open_edges=2), drc_report(open_edges=2)]
        self.native_mode = 'raise'
        code, result = self.invoke()
        self.assertEqual(code, 3)
        self.assertEqual(result['status'], 'TIMEOUT DRAFT')
        self.assertEqual(result['native_gate_status'], 'NOT RUN')

    def test_drc_invocation_failure_is_not_promoted(self):
        self.drc_exit = 1
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'PIPELINE FAILED DRAFT')
        self.assertEqual(self.router_calls, 0)

    def test_router_success_still_requires_native_zero(self):
        self.router_code = 0
        self.drc_reports = [drc_report(open_edges=2), drc_report(open_edges=2), drc_report()]
        self.set_native_edges({'NATIVE_NET': 1})
        code, result = self.invoke()
        self.assertEqual(self.router_calls, 1)
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'INCOMPLETE DRAFT')

    def test_router_success_with_both_checks_clear(self):
        self.router_code = 0
        self.drc_reports = [drc_report(open_edges=2), drc_report(open_edges=2), drc_report()]
        code, result = self.invoke()
        self.assertEqual(self.router_calls, 1)
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'ROUTED DRAFT')

    def test_unchanged_path_requires_native_zero(self):
        definition = route.load_definition(self.root / 'design/boards' / f'{self.board_id}.json')
        digest = hashlib.sha256(json.dumps({'routing': definition.routing,
            'outline': definition.outline, 'layers': definition.layers},
            sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.report.write_text(json.dumps({'routing_spec_sha256': digest}))
        self.drc_reports = [drc_report()]
        self.native_mode = 'raise'
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'PIPELINE FAILED DRAFT')

    def test_refresh_does_not_preserve_a_routing_success_badge(self):
        self.retained_report()
        code, result = self.invoke('--refresh-ratsnest-only')
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'RATSNEST ONLY DRAFT')
        self.assertEqual(result['prior_routing_status'], 'ROUTED DRAFT')
        self.assertNotIn('native_ratsnest_error', result)
        self.assertEqual(len(self.drc_reports), 2)  # Neither DRC report was consumed.
        self.assertEqual(self.router_calls, 0)

    def test_refresh_with_open_edges_returns_incomplete(self):
        self.retained_report()
        self.set_native_edges({'NATIVE_NET': 4})
        code, result = self.invoke('--refresh-ratsnest-only')
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'INCOMPLETE DRAFT')
        self.assertEqual(result['native_unconnected_edge_count'], 4)

    def test_refresh_failure_writes_failure_receipt(self):
        self.retained_report()
        self.native_mode = 'raise'
        code, result = self.invoke('--refresh-ratsnest-only')
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'PIPELINE FAILED DRAFT')
        self.assertNotIn('native_unconnected_edge_count', result)
        self.assertNotIn('native_board_sha256', result)

    def test_native_freshness_check_does_not_modify_board(self):
        before = self.board.read_bytes()
        self.invoke()
        self.assertEqual(self.board.read_bytes(), before)

    def test_complete_native_names_replace_truncated_drc_sample(self):
        self.set_native_edges({'NATIVE_A': 2, 'NATIVE_B': 3})
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(result['unrouted_net_names'], ['NATIVE_A', 'NATIVE_B'])
        self.assertEqual(result['unrouted_net_count'], 2)
        self.assertEqual(result['native_unconnected_edge_count'], 5)
        self.assertEqual(result['native_open_edges_by_net'], {'NATIVE_A': 2, 'NATIVE_B': 3})

    def test_inconsistent_native_names_fail_closed(self):
        original = dict(self.native_data)
        mutations = [
            {'native_open_edges_by_net': {'HIDDEN_OPEN': 1}},
            {'native_open_edges_by_net': []},
            {'native_open_edges_by_net': {'BAD': True}},
            {'native_open_edges_by_net': {'BAD': 0}},
            {'native_open_net_count': True},
            {'named_edge_count_sum': 1},
            {'named_edge_basis': None},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.native_data = {**original, **mutation}
                self.drc_reports = [drc_report(), drc_report()]
                code, result = self.invoke()
                self.assertEqual(code, 2)
                self.assertEqual(result['native_gate_status'], 'NOT RUN')
                self.assertNotIn('native_board_sha256', result)

    def test_native_receipt_hash_must_match_inspected_bytes(self):
        self.native_data['board_sha256'] = '0' * 64
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn('hash differs', result['native_ratsnest_error'])

    def test_failed_refresh_clears_old_native_names(self):
        self.retained_report()
        old = json.loads(self.report.read_text())
        old.update(native_open_edges_by_net={'OLD': 1}, unrouted_net_names=['OLD'],
                   unrouted_net_count=1, unrouted_name_basis='Old native result')
        self.report.write_text(json.dumps(old))
        self.native_mode = 'raise'
        code, result = self.invoke('--refresh-ratsnest-only')
        self.assertEqual(code, 2)
        for key in ('native_open_edges_by_net', 'unrouted_net_names',
                    'unrouted_net_count', 'unrouted_name_basis'):
            self.assertNotIn(key, result)

    def test_refresh_preserves_original_drc_sample(self):
        self.retained_report()
        old = json.loads(self.report.read_text())
        old.update(drc_unrouted_net_name_sample=['DRC_SAMPLE'],
                   unrouted_net_names=['OLD_NATIVE'])
        self.report.write_text(json.dumps(old))
        code, result = self.invoke('--refresh-ratsnest-only')
        self.assertEqual(code, 0)
        self.assertEqual(result['drc_unrouted_net_name_sample'], ['DRC_SAMPLE'])
        self.assertEqual(result['unrouted_net_names'], [])

    def test_native_receipt_removal_failure_clears_old_receipt(self):
        self.retained_report()
        with patch.object(Path, 'unlink', side_effect=PermissionError('cannot remove receipt')):
            code, result = self.invoke('--refresh-ratsnest-only')
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'PIPELINE FAILED DRAFT')
        self.assertEqual(result['native_gate_status'], 'NOT RUN')
        self.assertNotIn('native_unconnected_edge_count', result)
        self.assertNotIn('native_board_sha256', result)


if __name__ == '__main__':
    unittest.main()
