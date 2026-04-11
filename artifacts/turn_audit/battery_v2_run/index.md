# Turn Audit Battery V2
- battery_version: `turn_audit_battery_v2`
- generated_at: `2026-04-11T15:53:21.652358+00:00`
- output_directory: `artifacts\turn_audit\battery_v2_run`
- case_count: `12`

| case_id | route_class | final outcome | overall | mechanistic | claim_honesty | path_affecting | epistemic_status | epistemic_should_abstain | regulation_override_scope | regulation_gate_accepted | unresolved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bounded_clean_production_turn` | `production_contour` | `continue` | `PARTIAL` | `PASS` | `PASS` | `PARTIAL` | `report` | `False` | `none` | `False` | `3` |
| `route_boundary_or_nonproduction_case` | `helper_path` | `UNRESOLVED_FOR_V1` | `UNRESOLVED` | `PARTIAL` | `UNRESOLVED` | `UNRESOLVED` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `4` |
| `authority_mismatch_repair_detour` | `production_contour` | `repair` | `PASS` | `PASS` | `PASS` | `PASS` | `report` | `False` | `none` | `False` | `3` |
| `downstream_obedience_shared_domain_revalidate` | `production_contour` | `revalidate` | `PASS` | `PASS` | `PASS` | `PASS` | `report` | `False` | `none` | `False` | `3` |
| `t01_unresolved_laundering_guard` | `production_contour` | `revalidate` | `PASS` | `PASS` | `PASS` | `PASS` | `report` | `False` | `none` | `False` | `3` |
| `t02_raw_vs_propagated_integrity_pressure` | `production_contour` | `revalidate` | `PASS` | `PASS` | `PASS` | `PASS` | `report` | `False` | `none` | `False` | `3` |
| `t03_nonconvergence_preservation_honesty` | `production_contour` | `continue` | `PASS` | `PASS` | `PASS` | `PASS` | `report` | `False` | `none` | `False` | `3` |
| `epistemic_unknown_abstain_detour` | `production_contour` | `revalidate` | `PASS` | `PASS` | `PASS` | `PASS` | `report` | `False` | `none` | `False` | `3` |
| `epistemic_observation_requirement_block` | `production_contour` | `repair` | `PASS` | `PASS` | `PASS` | `PASS` | `report` | `False` | `none` | `False` | `3` |
| `regulation_high_override_scope_detour` | `production_contour` | `UNRESOLVED_FOR_V1` | `UNRESOLVED` | `PARTIAL` | `UNRESOLVED` | `UNRESOLVED` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `4` |
| `regulation_no_strong_override_claim_guard` | `production_contour` | `UNRESOLVED_FOR_V1` | `UNRESOLVED` | `PARTIAL` | `UNRESOLVED` | `UNRESOLVED` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `UNRESOLVED_FOR_V1` | `4` |
| `regulation_pressure_tradeoff_shift` | `production_contour` | `revalidate` | `PASS` | `PASS` | `PASS` | `PASS` | `report` | `False` | `none` | `False` | `3` |

## Failed / partial / unresolved cases
- failed: none
- partial: bounded_clean_production_turn
- unresolved: bounded_clean_production_turn, route_boundary_or_nonproduction_case, authority_mismatch_repair_detour, downstream_obedience_shared_domain_revalidate, t01_unresolved_laundering_guard, t02_raw_vs_propagated_integrity_pressure, t03_nonconvergence_preservation_honesty, epistemic_unknown_abstain_detour, epistemic_observation_requirement_block, regulation_high_override_scope_detour, regulation_no_strong_override_claim_guard, regulation_pressure_tradeoff_shift
