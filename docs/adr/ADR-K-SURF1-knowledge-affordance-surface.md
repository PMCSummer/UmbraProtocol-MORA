# ADR K-SURF1 Knowledge Affordance Surface

## Status
Accepted (build scope, non-authoritative provider surface only).

## Why K-SURF1 exists after UMWELT-S
UMWELT-S defines symbolic contact declarations and provider surfaces. K-SURF1 defines how provider-origin data is interpreted operationally: as source-bound hints/testimony/status candidates with uncertainty, never as truth, authority, or execution permission.

## Relation to adjacent layers
- UMWELT0: runtime public-contact membrane and authority boundary.
- UMWELT-S: symbolic ContactSpec/IR declarations, including `knowledge_affordance` channels.
- CONTACT-PROJECTION-GATE: projects runtime public contact to subject-side AB/ACP/AP-lineage surfaces.
- K1 (future): progression/slot-opening discipline over provider/affordance traces.
- EXP1 (future): unknown-resource inquiry using non-oracle hints.
- COST1 (future): comparison over candidate options, not provider truth.
- P15/P16/AB7: recipe/value/automation maturity gates that K-SURF1 cannot bypass.

## Provider authority classes
K-SURF1 normalizes providers into explicit authority classes:
- `hint`, `testimony`, `index`, `ui_status`, `quest_objective`, `machine_status`, `scanner_candidate`, `manual_claim`, `conflict_source`, `unknown_source`

All classes are non-authoritative by contract.

## Locked/partial slot discipline
- Locked slots stay locked unless explicit public discovery/contact/inspection/scan/quest-state/machine-status basis exists.
- Unlock in K-SURF1 yields partial/visible hint state only.
- No mature recipe is produced.

## Source/provenance requirements
- Every provider ref and provider claim must carry source refs.
- Hidden/eval/scenario-label payloads are blocked.
- Stale/lossy provider surfaces require uncertainty/lossiness markers.

## Conflict handling
- Contradicting provider claims create `ProviderConflictFrame`.
- No silent merge and no winner selection.
- Resolution status remains `unresolved` in this phase.

## No-oracle / no-action / no-value boundaries
K-SURF1 must never:
- emit AP01 request
- select action or goal
- execute world action
- claim fact/cause
- assign value
- mature recipe/transformation/skill
- claim automation or lived evidence
- expose hidden truth

## Falsifiers and ablations
Primary falsifiers:
- `knowledge_hint_as_action`
- `encyclopedia_as_oracle`
- `hint_as_lived_evidence`
- `locked_recipe_used`
- `slot_unlock_without_public_discovery`
- `provider_text_as_truth`
- `knowledge_hint_assigns_value`
- `provider_conflict_erased`

Ablations include:
- no source refs
- hidden/eval/scenario provider
- locked slot without discovery
- provider truth authority
- selected action in provider payload
- value assignment by provider payload
- mature recipe claim
- scanner identity truth
- machine UI cause truth
- stale/lossy without markers

## Allowed claim after build
"MORA provides a source-bound, multi-provider knowledge affordance surface that outputs hint/slot/conflict artifacts without action, truth, value, or maturity authority."

## Forbidden claims
- K-SURF1 runs provider backends
- K-SURF1 performs K1 progression
- K-SURF1 validates final recipes
- K-SURF1 selects actions/goals or emits AP01
- K-SURF1 proves live symbolic progression
