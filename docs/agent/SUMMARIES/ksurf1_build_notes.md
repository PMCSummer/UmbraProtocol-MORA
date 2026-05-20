# K-SURF1 Build Notes

## Inspected surfaces
- `src/substrate/umwelts_symbolic_contact/{models.py,policy.py,fixtures.py,downstream_contract.py}`
- `docs/agent/SUMMARIES/umwelts_contactspec_quickstart.md`
- `src/substrate/umwelt0_phenomenal_contact/{models.py,policy.py}`
- `src/substrate/contact_projection_gate/{models.py,policy.py,downstream_contract.py}`
- `src/substrate/ab07_recipe_automation_integration/*`
- `src/substrate/ab_subject_tick_integration/*`
- `docs/seams/W02.seam.md`
- `docs/seams/W06.seam.md`
- `docs/seams/G05.seam.md`

## Files added/changed
- `src/substrate/ksurf1_knowledge_affordance_surface/{__init__.py,models.py,policy.py,telemetry.py,downstream_contract.py,fixtures.py}`
- `tests/substrate/test_ksurf1_knowledge_affordance_surface_build/test_ksurf1_knowledge_affordance_surface_build.py`
- `tools/ksurf1_knowledge_affordance_demo.py`
- `docs/adr/ADR-K-SURF1-knowledge-affordance-surface.md`
- `docs/agent/EXPERIMENTS/ksurf1_knowledge_affordance_contract.md`

## Model/policy summary
- Typed provider/claim/hint/slot/conflict models.
- Strict authority profile (`KSurfAuthorityFlags`) with all action/truth/value/maturity permissions false.
- Source refs required for providers/claims/hints.
- Hidden/eval/scenario payloads blocked.
- Locked-slot unlock requires explicit public basis prefixes.
- Provider conflicts become unresolved `ProviderConflictFrame` (no winner).
- Stale/lossy surfaces require uncertainty/lossiness markers.

## Fixtures
- JEI-like index hint fixture
- Encyclopedia locked-slot fixture
- Encyclopedia partial unlock fixture
- Quest objective hint fixture
- Machine status hint fixture
- Scanner candidate fixture
- Manual claim fixture
- Provider conflict fixture
- Hidden provider blocked fixture
- Stale/lossy provider fixture
- UMWELT-S provider declaration integration fixture

## Test scope
- 25 required K-SURF1 behaviors covered plus explicit ablation locks:
  - selected action in provider payload blocked
  - provider default cannot invent source evidence

## Limitations
- No concrete provider backends.
- No K1 progression logic.
- No EXP1 inquiry behavior.
- No COST1 comparison behavior.
- No MICRO1 operation graph.
- No WORLD0 runner.

## Next recommended phase
Proceed with `MICRO1` (operation-graph discipline) or `COST1` (comparison discipline) before WORLD0.
