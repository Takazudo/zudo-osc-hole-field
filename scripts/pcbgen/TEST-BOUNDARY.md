# Python verification boundary

The portable unit suite is `bash scripts/checks/run-python-tests.sh`. It discovers
`test_*.py` under `scripts/` and `design/`. Its inputs are committed source,
committed small fixtures, and temporary synthetic fixtures. Passing this suite
establishes software regression coverage only, not native board acceptance.

Both commands use `python3` from `PATH`; activate an environment with
`scripts/pcbgen/numerical-requirements.txt` installed first. Missing numerical
dependencies are setup failures, not passed or skipped tests.

Run retained issue-38 artifact integration regressions explicitly with:

```sh
bash scripts/checks/run-retained-artifact-tests.sh
```

These regressions are in `scripts/pcbgen/*_retained_regression.py`. They consume
preserved `.circuit-cache/issue38-recovery/` exports, receipts, historical solver
checkpoints, and experimental board/project siblings under `boards/`. Those large
local artifacts are intentionally not part of the source checkpoint. A clean
checkout therefore cannot run this suite without restoring the exact preserved
artifacts. Missing inputs fail; assertions are not skipped, substituted, or
rebound to new hashes. The previous optional historical drill-fixture skip is
now a mandatory read when this explicit suite runs. Restoring just the latest
geometry is insufficient: historical mutation and epoch comparisons require the
older evidence too.

Default portable results must report this suite as **NOT RUN — retained local
artifacts required**. An explicit retained-suite failure stays a failure. Neither
suite substitutes for the separate pinned KiCad native checks, a completed
current-source electrical calculation, or physical qualification. The native
verification command surface is unchanged.

Mixed modules retain their portable methods in `test_*.py`; their artifact-based
methods were moved without changing assertions. Whole modules were moved only
where all cases depend on local artifacts (including shared setup). Fixture helper
methods copied into mixed retained modules do not introduce inherited portable
tests. The exact moved case inventory follows.

- `core_ground_inventory_retained_regression.py`: `test_all_selected_contacts_and_independent_source_inventory`, `test_missing_source_pad_and_wrong_selected_net_or_face_fail`
- `core_full_ground_inventory_retained_regression.py`: `test_exact_full_basis_and_source_native_failures`
- `core_stitch_ownership_retained_regression.py`: `test_complete_actual_source_ownership_and_wrong_source_identity`, `test_missing_or_duplicate_or_foreign_stitch_is_rejected`
- `core_model_entry_retained_regression.py`: `test_complete_basis_and_coupling_remain_distinct`, `test_complete_selection_checks_identity_and_face`, `test_driver_rejects_missing_or_stale_authority_before_extraction`, `test_immutable_input_and_final_dependency_mismatch_reject`
- `peripheral_model_entry_retained_regression.py`: `test_missing_failed_stale_and_partial_source_rejects`, `test_actual_complete_faces_reference_and_uuid_mapping`, `test_actual_positive_and_bound_wrong_board_companion_changes`, `test_actual_two_foil_extraction_keeps_all_71_functions`, `test_generic_driver_cannot_extract_without_native_authority`
- `jack_white_current_binding_retained_regression.py`: `test_actual_positive_and_wrong_board_companion_drc`, `test_sheet_exporter_and_mid_check_mutation`
- `verify_pth_current_epoch_retained_regression.py`: `test_exact_epoch_and_witness`, `test_reject_changed_drill`, `test_reject_changed_native_foil_primitive`, `test_reject_non_fitted_or_duplicate_witness`
- `current_j_rail_entry_retained_regression.py`: `test_exact_current_jl_rail_and_wrong_role`
- `current_j_rail_wrapper_retained_regression.py`: `test_missing_authority_stale_feed_and_occupied_selected_path`
- `contact_support_frame_retained_regression.py`: `test_actual_o1_and_normal_sign`
- `peripheral_stack_serialization_retained_regression.py`: `test_exact_stopped_v2_editor_delta_and_all_other_values_reject`
- `peripheral_ground_bridge_retained_regression.py`: `test_actual_optical_board_exact_single_bridge`
- `control_hidden_field_preservation_retained_regression.py`: `test_actual_three_hidden_deltas_restore_every_original_footprint`, `test_changed_value_visible_style_or_other_geometry_is_not_hidden`
- `refresh_white_land_retained_regression.py`: `test_all_actual_native_copies_and_negatives`
- `control_project_source_retained_regression.py`: `test_exact_native_stopped_run_project_matches_independent_source_derivation`, `test_foreign_class_semantics_or_destination_are_rejected`
- `control_source_epoch_bridge_retained_regression.py`: `test_current_actual_local_bridge_and_projected_source_mutations`
- `control_model_entry_retained_regression.py`: `test_actual_native_positive_and_generic_missing_receipt_bypass_rejection`
- `assemble_nominal_ground_network_retained_regression.py`: `test_production_source_set_is_exact`
- `core_coupling_screen_retained_regression.py`: `test_current_authority_and_wrong_native_board_or_failed_receipt`
- `core_model_gate_retained_regression.py`: `test_actual_failed_v2_is_rejected_before_modeling`
- `drilled_face_lift_trial_retained_regression.py`: `test_two_drill_historical_overlap_fixture_is_exact`
- `pth_source_geometry_retained_regression.py`: `test_actual_native_drift_rejects_without_output`
- `peripheral_ground_source_retained_regression.py`: `test_exact_observed_fresh_native_stage_and_foreign_rule_rejection`
- `jack_ground_source_epoch_retained_regression.py`: `test_current_exact_nominal_source_bridge`
