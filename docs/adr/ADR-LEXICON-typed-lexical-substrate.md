# ADR-LEXICON: Typed Lexical Substrate

## Status
Accepted as a narrow build-mode substrate increment.

## Canonical Seams
- `create_or_update_lexicon_state(...) -> LexiconUpdateResult`
- `query_lexical_entries(...) -> LexiconQueryResult`
- `evaluate_lexicon_downstream_gate(...) -> LexiconGateDecision`
- `persist_lexicon_result_via_f01(...) -> execute_transition(...)`
- `record_lexical_usage_episode(...) -> LexicalEpisodeRecordResult`
- `consolidate_lexical_hypotheses(...) -> LexicalHypothesisUpdateResult`
- `evaluate_lexical_learning_downstream_gate(...) -> LexicalLearningGateDecision`
- `persist_lexical_learning_result_via_f01(...) -> execute_transition(...)`

## What This Substrate Claims
- Provides a typed storage and update/query surface for lexical knowledge.
- Stores lexical entries as bundles, not string-to-single-meaning maps.
- Entry model is explicit and distinct from sense model (entry identity + sense bundles).
- Preserves lexical ambiguity:
  - one form may map to multiple entries
  - one entry may carry multiple senses
- Enforces split-or-freeze behavior on ambiguous multi-target updates (no silent winner-take-all collapse).
- Preserves provisional/conflict/unknown lexical states as first-class outputs.
- Preserves a first-class typed lexical unknown taxonomy on query path:
  - `unknown_word`
  - `partial_lexical_hypothesis`
  - `known_syntax_unknown_lexeme`
  - `known_lexeme_unknown_sense_in_context`
- Plain query no-match defaults to typed `unknown_word` unless a more specific unknown class is derivable.
- Unknown taxonomy derivation uses explicit dominance precedence:
  - `known_lexeme_unknown_sense_in_context` > `known_syntax_unknown_lexeme` > `partial_lexical_hypothesis` > `unknown_word`
- Known-lexeme-unknown-sense-in-context is triggered only by unresolved stable-sense basis under available lexical/context cues, not by a raw multi-sense count alone.
- Query records carry per-record unknown hardness semantics (`dominant_unknown_class`, `hard_unknown_or_capped`, `strong_lexical_claim_permitted`) so batched global acceptance cannot hide per-item lexical caps.
- Stores composition and reference behavior hints for later phases.
- Stores typed lexical examples linked to entries/senses as inspectable usage evidence.
- Applies `reference_profile.requires_context` as a runtime query/gate restriction (`context_required_for_reference_profile`).
- Applies operator scope-context restriction for underspecified operator-like entries (`operator_scope_context_required`).
- Uses a single gate semantics path for query and canonical downstream gate decisions.
- Enforces query/canonical gate parity for unknown-taxonomy cases (same accepted/restricted semantics).
- Caps strong lexical claims when only non-stable senses remain (`only_unstable_senses`).
- Uses example support as a minimal runtime evidence-quality cap for non-stable entries (`non_stable_entry_without_example_support`).
- Supports episode-driven lexical acquisition:
  - usage episode -> provisional hypothesis
  - repeated compatible support -> promotion-eligible
  - conflict episodes -> conflicted/frozen hypothesis
  - consolidation promotes to lexical entries only after evidence threshold.
- Ordinary episode-driven acquisition uses a hard support floor of 2 (single-shot promotion is blocked by runtime guard).
- Episode/hypothesis schema/lexicon/taxonomy mismatch is runtime load-bearing (block/freeze/cap), not telemetry-only.
- Lexical entry acquisition origin is explicit (`seed` / `direct_curation` / `episode_promotion`) so direct curation is not misclaimed as learned-from-episodes.
- Enforces schema/lexicon/taxonomy compatibility checks on update/query seams.
- Freezes/caps per-entry version-incompatible records on reconstruct/continue boundary (no silent incompatible carry-forward).
- Persists load-bearing lexical state through F01 seam only.

## What This Substrate Does Not Claim
- No full language learning.
- No final lexical grounding.
- No final referent resolution.
- No word-sense disambiguation engine.
- No dictum/proposition construction.
- No semantic completion.
- No illocution/discourse acceptance/commitment updates.

## Load-Bearing Telemetry
- source lineage
- processed entry ids
- new/updated/provisional/stable counts
- unknown/conflict/blocked counts
- ambiguity reasons
- queried forms
- matched entry ids
- no-match count
- compatibility markers
- downstream gate decision
- attempted update/query paths
- causal basis

## Explicit Bounds
- Mechanism is intentionally minimal and rule-based.
- Seed lexicon is intentionally small and typed (not language mastery).
- Unknown lexical items remain unknown unless explicit typed evidence is added.
- Episode-driven learning is minimal and rule-based (no parser, no WSD, no phrase semantics).
- Optional lexical substrate usage by L03 is allowed but not required in this increment.
- L03 integration treats lexicon query artifacts as primary lexical basis when provided; heuristic lexical guesses remain explicit fallback with capped claim strength.
- When L03 contour runs without lexicon handoff, runtime emits explicit degraded bounded mode (`lexicon_handoff_missing`, `lexical_basis_degraded`, `no_strong_lexical_claim_without_lexicon`) instead of silently normal lexical mode.
- Syntax-known lexical gaps can be represented via typed lexical query context only; no parser/semantic integration is introduced here.
- Contour-level proof that lexicon ablation degrades full L03 behavior is not closed here to avoid L03 phase creep.
- Hostile/raw bypass outside typed seams is out of scope.
