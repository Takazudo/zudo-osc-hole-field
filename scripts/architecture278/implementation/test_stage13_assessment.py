import copy
import json
import unittest
import stage13_assessment as study


class PreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads((study.OUT / 'scope.json').read_text())

    def test_complete_predecessor_freeze(self):
        self.assertEqual(study.preserve(self.scope), 289)

    def test_cannot_omit_or_rehash_prior_resistance_and_geometry(self):
        for name in ('stage12/budget-report.json', 'stage11/support-input.json'):
            for mode in ('omit', 'rehash'):
                r = copy.deepcopy(self.scope)
                key = 'design/architecture-278/implementation/' + name
                if mode == 'omit': r['preserved_prior_source_sha256'].pop(key)
                else: r['preserved_prior_source_sha256'][key] = '0' * 64
                with self.assertRaises(ValueError): study.preserve(r)

    def test_no_instrument_scope_reduction(self):
        r = copy.deepcopy(self.scope)
        r['instrument_invariants']['OSC'] = 1
        with self.assertRaises(ValueError): study.preserve(r)


    def test_historical_mutable_review_checks_exact_old_bytes(self):
        import hashlib,subprocess
        path='design/architecture-278/implementation/README.md'
        raw=subprocess.check_output(['git','show',study.BASE+':'+path],cwd=study.ROOT)
        study.historical_review_binding(path,hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError): study.historical_review_binding(path,'0'*64)
        with self.assertRaises(ValueError): study.historical_review_binding(path,study.digest(study.ROOT/path))

    def test_historical_nonmutable_review_cannot_use_old_bytes(self):
        path='design/architecture-278/implementation/stage12/budget-report.json'
        sha=study.digest(study.ROOT/path)
        study.historical_review_binding(path,sha)
        with self.assertRaises(ValueError): study.historical_review_binding(path,sha,current_digest=lambda p:'0'*64)


class CalibrationCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((study.OUT / 'calibration-report.json').read_text())

    def test_independent_closed_form_and_derivatives(self):
        self.assertEqual(study.calibration(self.report)['residual_points'],315)

    def test_cannot_remove_control_coupling(self):
        r = copy.deepcopy(self.report)
        r['observability']['control_jacobian_structure'][2][0] = 0
        with self.assertRaises(ValueError): study.calibration(r)
        r = copy.deepcopy(self.report)
        r['offset_coupling_examples'][0]['preset']['actual_control_jacobian'][2][0] = 0
        with self.assertRaises(ValueError): study.calibration(r)

    def test_cannot_drop_CV_or_endpoint_observation(self):
        for mode in ('preset','grid','case'):
            r = copy.deepcopy(self.report)
            if mode=='preset': r['cases'][0]['bounded_presets'].pop()
            elif mode=='grid': r['cases'][0]['bounded_presets'][0]['residuals'].pop()
            else: r['cases'].pop()
            with self.assertRaises(ValueError): study.calibration(r)

    def test_fit_does_not_prove_hardware(self):
        for key,value in (('realized_in_hardware',True),):
            r = copy.deepcopy(self.report)
            r['cases'][0]['bounded_presets'][0]['mathematical_fit'][key] = value
            with self.assertRaises(ValueError): study.calibration(r)

    def test_unreachable_endpoint_cannot_be_called_calibrated(self):
        r = copy.deepcopy(self.report)
        r['cases'][0]['bounded_presets'][2]['atten_setting']['reachable'] = True
        with self.assertRaises(ValueError): study.calibration(r)

    def test_hidden_residual_or_output_load_cannot_be_zeroed(self):
        for mode in ('residual','load','headroom','criterion'):
            r = copy.deepcopy(self.report)
            preset = r['cases'][1]['bounded_presets'][0]
            if mode=='residual': preset['CV_only_residual_at5V'] = 0
            elif mode=='load': preset['residuals'][0]['output_load_change_V'] = 0
            elif mode=='headroom': preset['residuals'][0]['actual_headroom_proven'] = True
            else: r['criteria']['static_target_V'] = .02
            with self.assertRaises(ValueError): study.calibration(r)


    def test_retained_corner_and_saturation_source_binding(self):
        for mode in ('corner','extra','saturation'):
            r = copy.deepcopy(self.report)
            if mode=='corner': r['cases'][1]['params']['gcv']=1.1
            elif mode=='extra':
                extra=copy.deepcopy(r['cases'][0]);extra['name']='invented';r['cases'].append(extra)
            else: r['saturation_cases'][0]['mathematical_output_V']=0
            with self.assertRaises(ValueError): study.calibration(r)


class PackageCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cap = json.loads((study.OUT/'capacitor-report.json').read_text())
        cls.pack = json.loads((study.OUT/'package-report.json').read_text())
        cls.prior = [json.loads((study.OUT.parent/'stage10'/(name+'.json')).read_text()) for name in ('inventory-report','mechanical-report','interfaces-report')]

    def check(self,cap,pack):
        return study.capacitor_package(cap,pack,*self.prior)

    def test_capacitor_identity_and_actual_pad_composition(self):
        self.assertEqual(self.check(self.cap,self.pack)['changed_pad_endpoints'],4)

    def test_changed_package_or_pad_not_silently_accepted(self):
        for mode in ('unrelated','polarity','pad','identity'):
            cap,pack = copy.deepcopy(self.cap),copy.deepcopy(self.pack)
            if mode=='unrelated': pack['placements']['C7107']['origin_mm'][0]+=1
            elif mode=='polarity': pack['placements']['C7101']['pins']['1']='AGND'
            elif mode=='pad': pack['placements']['C7101']['pads_xyz_mm']['1'][0][0]+=1
            else: cap['parts']['C7101']['MPN']='T491C475K035AT'
            with self.assertRaises(ValueError): self.check(cap,pack)

    def test_conditional_primary_data_not_service_guarantees(self):
        for mode in ('C','ESR','noise','inrush','interval'):
            cap,pack = copy.deepcopy(self.cap),copy.deepcopy(self.pack)
            if mode=='C': cap['parts']['C7101']['effective_service_C_guaranteed_F']=4e-6
            elif mode=='ESR': cap['output_comparison']['stability_qualified']=True
            elif mode=='noise': cap['output_comparison']['noise_1_to1p5ohm_recommendation_established']=True
            elif mode=='inrush': cap['parts']['C7102']['startup']['actual_peak_inrush_A']=.01
            else: cap['parts']['C7102']['temperature_qualification_intervals_F']['125'][0]=20e-6
            with self.assertRaises(ValueError): self.check(cap,pack)

    def test_cannot_omit_return_or_preserve_stale_paths(self):
        for mode in ('return','length','delta','edge','fullpath'):
            cap,pack = copy.deepcopy(self.cap),copy.deepcopy(self.pack)
            if mode=='return': pack['local_reference_pad_paths'].pop()
            elif mode=='length': pack['local_reference_pad_paths'][1]['after_straight_floor_mm']=0
            elif mode=='delta': pack['endpoint_delta_and_invalidation']['changed_source_pads'].pop()
            elif mode=='edge': pack['endpoint_delta_and_invalidation']['changed_source_pads'][0]['invalidated_incident_graph_edges']=[]
            else: pack['endpoint_delta_and_invalidation']['current_overlay_complete_path_metrics']={}
            with self.assertRaises(ValueError): self.check(cap,pack)


if __name__ == '__main__':
    unittest.main()
