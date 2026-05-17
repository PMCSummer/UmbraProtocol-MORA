# Embodied Playground P4: ACP01 Internal Candidate Production

## Stage Intent
P4 adds a bounded internal producer for AP01 candidate input in the subject path.

## What Is Added
- `src/substrate/acp01_internal_action_candidate_production/*`
- narrow `subject_tick` integration (`acp01_result`, counters, AP01 source tagging)
- bridge internal mode (`use_internal_candidate_producer`) that projects public basis into ACP01 input
- ACP01/P4 falsifiers and tests
- ACP01 demo tool

## Runtime Shape
1. World observation is projected to public ACP01 basis.
2. `subject_tick` executes and runs ACP01 before AP01.
3. ACP01 may emit AP01 candidate set.
4. AP01 may publish bounded request.
5. Bridge/world submission behavior remains AP01-gated.

## Non-Claims
- Not autonomous planning.
- Not pathfinding.
- Not recipe/automation production.
- Not AP01 publication replacement.
- Not world execution inside ACP01.
