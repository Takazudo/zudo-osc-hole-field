# Issue 38: current-epoch PTH nominal geometry bridge

## Requested result and scope

Transfer the retained historical nominal PTH source-geometry cover to the current J, P v4, and K v7 native epochs, without changing historical receipts or treating conditional plating geometry as physical acceptance.

## Evidence and affected records

- Historical certificate: `.circuit-cache/issue38-recovery/pth-source-geometry-certificate-v2.json` (SHA-256 `777af6fb22334f140a9b4a649e843c62957ed093ba4004835f45933d330cd245`), with 305 nominal records, zero unresolved, and zero actual finished-plating qualifications.
- Historical fitted source inventory: `.circuit-cache/issue38-recovery/own-source-flux-boundaries-v2.json` (SHA-256 `bc766e053d76791c68afd41f65ea9ce184b93fdf11725d9b019c7d018e9b9ad4`).
- Existing current J bridge: `.circuit-cache/issue38-recovery/jack-ground-source-epoch-bridge-v4.json`; verified again in full.
- Current P v4 and K v7 native export, board, manifest, DRC and source closures: admitted with their respective `require_native_prerequisite` gates. No new native export or model run was made.

## Actions and result

The new `scripts/pcbgen/verify_pth_current_epoch.py` requires exact historical receipt hashes, verifies the J bridge, calls the full P/K native gates, compares the historical and current AGND source pad records plus complete native holes, outline and stackup, then matches each historical PTH certificate to the current fitted source pad UUID, drill and foil primitives. It checks the exact board bytes and repeats dependency hashes before returning. The current receipt is `.circuit-cache/issue38-recovery/pth-current-epoch-bridge-v2.json` (SHA-256 `9e2da4e763bb84341860e18d680fee0720eef165daa1132970f983edb367b2b4`). The earlier v1 is historical after the helper was tightened to capture its own source hash before verification.

All 305 local nominal PTH records transfer exactly: J left 100, J right 80, P 120, K 5. The J conclusion is delegated to the reviewed J bridge; P and K are checked directly against their current native epochs. Four adversarial tests pass, including changed drill, changed foil primitive and duplicate/non-fitted witness rejection. `pnpm circuit:check` passed before and after the edit.

The historical certificate retains its own source-code epoch. The new bridge verifies its frozen receipt and historical native export binding; it does not demand that old model/generator source digests equal newer source code or rebind historical numerical outputs.

## Remaining

Finished plating, real contact, source flux, 3D/primal geometry, materials, process tolerances, current and joined electrical acceptance remain open. The nominal geometry bridge is not a fabrication or release qualification.
