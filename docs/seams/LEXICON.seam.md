# LEXICON seam

phase: LEXICON  
title: Typed lexical knowledge substrate

direct_upstream:
- F01 — Causal substrate (runtime persistence seam only)
- F02 — Grounding / epistemic substrate (lineage metadata only)

direct_downstream:
- L03 — Lexical grounding and reference hypotheses (primary lexical basis when LEXICON artifact is provided)
- L04 — Dictum candidate construction (indirectly via L03 outputs)

## Canonical Seams
- `create_or_update_lexicon_state(...) -> LexiconUpdateResult`
- `query_lexical_entries(...) -> LexiconQueryResult`
- `evaluate_lexicon_downstream_gate(...) -> LexiconGateDecision`
- `persist_lexicon_result_via_f01(...) -> execute_transition(...)`
- `record_lexical_usage_episode(...) -> LexicalEpisodeRecordResult`
- `consolidate_lexical_hypotheses(...) -> LexicalHypothesisUpdateResult`
- `evaluate_lexical_learning_downstream_gate(...) -> LexicalLearningGateDecision`
- `persist_lexical_learning_result_via_f01(...) -> execute_transition(...)`

## UPSTREAM CONTRACT
- typed-only critical path:
  - `LexiconState`
  - `LexicalEntryProposal`
  - `UnknownLexicalObservation`
  - `LexiconUpdateContext`
  - `LexiconQueryRequest`
  - `LexiconQueryContext`
  - `LexicalUsageEpisode`
  - `LexicalEpisodeRecordContext`
  - `LexicalHypothesisConsolidationContext`
- raw/untyped payloads on critical path are rejected.

## DOWNSTREAM CONTRACT
- downstream receives typed lexical entries and candidate sense/reference/composition profiles.
- downstream query records expose typed lexical unknown-state taxonomy (`unknown_states`), not only free-form reason strings.
- downstream query records expose per-record unknown hardness semantics:
  - `dominant_unknown_class`
  - `hard_unknown_or_capped`
  - `strong_lexical_claim_permitted`
- lexical entry model is load-bearing and distinct from sense model:
  - entry identity (`entry_id`, canonical/lemma/aliases, entry status)
  - sense bundles (`sense_id`, sense status/confidence/evidence/conflict)
  - typed usage examples linked to entry and optionally to sense
- downstream must treat output as lexical knowledge substrate only, not final lexical grounding or semantics.
- unknown/provisional/conflict states are load-bearing and must remain inspectable.
- when L03 contour runs without a provided LEXICON artifact, this must be exposed as degraded lexical-basis mode upstream (`lexicon_handoff_missing` / `no_strong_lexical_claim_without_lexicon`), not silently normalized to normal lexical understanding.
- lexical unknown states remain distinct and inspectable:
  - `unknown_word`
  - `partial_lexical_hypothesis`
  - `known_syntax_unknown_lexeme`
  - `known_lexeme_unknown_sense_in_context`

## SEAM OBLIGATIONS
- preserve one-form-to-many-entry and one-form-to-many-sense ambiguity.
- new lexical knowledge enters through episode-backed provisional hypotheses, not single-shot stable truth.
- ordinary episode-driven promotion has a hard minimum support floor of 2; single episode must not silently stabilize lexical meaning.
- conflicting usage episodes must preserve conflict/freeze state (no silent averaging to stable).
- promotion to stable lexical entry/sense requires explicit support threshold + confidence criteria.
- episode/hypothesis payload schema/lexicon/taxonomy mismatches must be blocked/frozen/capped at runtime (not telemetry-only markers).
- ambiguous multi-match updates must use split-or-freeze discipline; no silent forced winner.
- preserve unknown/provisional/conflict as first-class state.
- unknown discipline must remain first-class across runtime/query/gate/snapshot:
  - plain no-match defaults to typed `unknown_word` unless a more specific unknown class is present
  - unknown word must not silently map to nearest known entry
  - partial hypothesis must not be treated as stable lexical knowledge
  - syntax-known lexical gap must be representable via typed query context (`syntax_known_lexical_gap_forms`)
  - unknown taxonomy class selection uses explicit precedence:
    `known_lexeme_unknown_sense_in_context` > `known_syntax_unknown_lexeme` > `partial_lexical_hypothesis` > `unknown_word`
  - known lexeme unknown-sense-in-context requires unresolved stable-sense basis (not just `len(senses) > 1`)
  - known lexeme with unresolved context-dependent sense must cap strong lexical claim
- preserve entry != sense separation across update/query/snapshot/roundtrip.
- no hidden top-1 lexical meaning collapse.
- no referent resolution claim.
- no dictum/proposition/illocution/discourse-acceptance claim.
- direct lexical curation path and episode-backed promotion path must remain distinguishable via typed acquisition origin markers.
- runtime mutation only via F01 persistence seam.
- enforce schema/lexicon/taxonomy compatibility on update/query seams.
- query gate must not accept when remaining matches are only conflicted/frozen/context-blocked.
- query gate and canonical gate must share one decision semantics path (no drift between local/canonical gate logic).
- if a query leaves only non-stable senses, strong lexical claim is capped (`only_unstable_senses`).
- non-stable entries without example support must be capped (`non_stable_entry_without_example_support`).
- `reference_profile.requires_context` must be runtime load-bearing on query/gate claim strength.
- operator-like composition hints may cap strong lexical claim when scope context is absent (`operator_scope_context_required`).
- typed lexical examples must remain linked to entry/sense and survive roundtrip.
- per-entry schema/lexicon/taxonomy mismatch at reconstruct/continue boundary must be frozen/capped, not silently reused.

## FORBIDDEN OVERREACH
- no full language learning engine.
- no semantic parser or proposition builder.
- no final lexical grounding.
- no implicit world-object binding from lexical entry.

## LOAD-BEARING SEAM TELEMETRY
- source lineage
- processed entry ids
- processed episode ids
- processed hypothesis ids
- new/updated/provisional/stable counts
- recorded/promoted/conflicted/frozen/insufficient episode-learning counts
- unknown/conflict/blocked counts
- ambiguity reasons
- queried forms and matched entry ids
- no-match count
- compatibility markers
- downstream gate outcome
- unknown state classes emitted for the query path
- attempted update/query paths
- causal basis

## REQUIRED SEAM TESTS
- typed-only seam validation and raw bypass rejection.
- ambiguity preservation (multiple senses and multiple entries).
- entry != sense preservation under query/persistence.
- ambiguous update-target handling (split-or-freeze).
- unknown/conflict/provisional preservation.
- context-required reference profile restriction in query/gate.
- role-hint load-bearing restriction (operator scope context requirement).
- lexical example integrity (entry/sense link + roundtrip survival).
- compatibility mismatch -> honest blocked/abstain path.
- unknown taxonomy tests:
  - unknown-word / partial-hypothesis / syntax-known-lexeme-gap / known-lexeme-unknown-sense are distinct runtime states
  - unknown classes affect gate restrictions and accepted/rejected semantics
  - query record per-item hardness is visible even when global batched gate is accepted
  - query embedded gate and canonical gate remain semantically identical on unknown-taxonomy cases
- unknown roundtrip tests:
  - persist -> reconstruct -> continue preserves unknown/provisional/context-sensitive unknown behavior
- F01-only persistence and roundtrip integrity, including persist -> reconstruct -> continue equivalence.
- episode-learning tests:
  - single-episode provisional discipline
  - repeated support -> promotion eligibility/promotion
  - conflict episode -> conflicted/frozen path
  - roundtrip preservation of episodes/hypotheses/support/conflict state
- boundary tests: no lexical substrate claim stronger than authority.

## SEAM FALSIFIERS
- surface form silently collapsed to one final sense.
- multi-match update silently collapsed to one update target.
- unknown lexical item forced into fabricated stable meaning.
- single observed usage silently promoted to stable lexical truth.
- conflict evidence averaged away without explicit conflict state.
- episode ledger exists but has no effect on promotion/conflict outcomes.
- compatibility mismatch silently reused as compatible state.
- context-dependent lexical reference treated as strong match without context.
- unknown classes collapsed into generic ambiguity/no-match with no typed distinction.
- downstream can treat lexical output as final grounding/proposition.
- query/canonical gate divergence on accept/reject semantics.
