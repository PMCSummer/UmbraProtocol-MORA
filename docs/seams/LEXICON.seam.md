# LEXICON seam

phase: LEXICON  
title: Typed lexical knowledge substrate

direct_upstream:
- F01 — Causal substrate (runtime persistence seam only)
- F02 — Grounding / epistemic substrate (lineage metadata only)

direct_downstream:
- L03 — Lexical grounding and reference hypotheses (optional lexical knowledge source)
- L04 — Dictum candidate construction (indirectly via L03 outputs)

## Canonical Seams
- `create_or_update_lexicon_state(...) -> LexiconUpdateResult`
- `query_lexical_entries(...) -> LexiconQueryResult`
- `evaluate_lexicon_downstream_gate(...) -> LexiconGateDecision`
- `persist_lexicon_result_via_f01(...) -> execute_transition(...)`

## UPSTREAM CONTRACT
- typed-only critical path:
  - `LexiconState`
  - `LexicalEntryProposal`
  - `UnknownLexicalObservation`
  - `LexiconUpdateContext`
  - `LexiconQueryRequest`
  - `LexiconQueryContext`
- raw/untyped payloads on critical path are rejected.

## DOWNSTREAM CONTRACT
- downstream receives typed lexical entries and candidate sense/reference/composition profiles.
- downstream must treat output as lexical knowledge substrate only, not final lexical grounding or semantics.
- unknown/provisional/conflict states are load-bearing and must remain inspectable.

## SEAM OBLIGATIONS
- preserve one-form-to-many-entry and one-form-to-many-sense ambiguity.
- ambiguous multi-match updates must use split-or-freeze discipline; no silent forced winner.
- preserve unknown/provisional/conflict as first-class state.
- no hidden top-1 lexical meaning collapse.
- no referent resolution claim.
- no dictum/proposition/illocution/discourse-acceptance claim.
- runtime mutation only via F01 persistence seam.
- enforce schema/lexicon/taxonomy compatibility on update/query seams.
- query gate must not accept when remaining matches are only conflicted/frozen/context-blocked.
- `reference_profile.requires_context` must be runtime load-bearing on query/gate claim strength.

## FORBIDDEN OVERREACH
- no full language learning engine.
- no semantic parser or proposition builder.
- no final lexical grounding.
- no implicit world-object binding from lexical entry.

## LOAD-BEARING SEAM TELEMETRY
- source lineage
- processed entry ids
- new/updated/provisional/stable counts
- unknown/conflict/blocked counts
- ambiguity reasons
- queried forms and matched entry ids
- no-match count
- compatibility markers
- downstream gate outcome
- attempted update/query paths
- causal basis

## REQUIRED SEAM TESTS
- typed-only seam validation and raw bypass rejection.
- ambiguity preservation (multiple senses and multiple entries).
- ambiguous update-target handling (split-or-freeze).
- unknown/conflict/provisional preservation.
- context-required reference profile restriction in query/gate.
- compatibility mismatch -> honest blocked/abstain path.
- F01-only persistence and roundtrip integrity, including persist -> reconstruct -> continue equivalence.
- boundary tests: no lexical substrate claim stronger than authority.

## SEAM FALSIFIERS
- surface form silently collapsed to one final sense.
- multi-match update silently collapsed to one update target.
- unknown lexical item forced into fabricated stable meaning.
- conflict evidence averaged away without explicit conflict state.
- compatibility mismatch silently reused as compatible state.
- context-dependent lexical reference treated as strong match without context.
- downstream can treat lexical output as final grounding/proposition.
