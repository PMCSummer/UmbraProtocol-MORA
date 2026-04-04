from __future__ import annotations

from dataclasses import replace

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_update import (
    ContinuationStatus,
    build_discourse_update,
)
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import (
    build_grounded_semantic_substrate,
    derive_grounded_downstream_contract,
    evaluate_grounded_semantic_downstream_gate,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _pipeline(text: str, material_id: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    modus = build_modus_hypotheses(dictum)
    discourse_update = build_discourse_update(modus)
    return surface, dictum, modus, discourse_update


def test_g01_normative_typed_route_is_active_with_l05_and_l06_inputs() -> None:
    surface, dictum, modus, discourse_update = _pipeline(
        'he said "alpha is stable?"',
        "m-g01-rewire-normative",
    )
    result = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:g01-rewire-normative",
        cooperation_anchor_ref="o03:g01-rewire-normative",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )
    gate = evaluate_grounded_semantic_downstream_gate(result)

    assert result.bundle.normative_l05_l06_route_active is True
    assert result.bundle.legacy_surface_cue_fallback_used is False
    assert result.bundle.discourse_update_not_inferred_from_surface_when_l06_available is True
    assert "normative_l05_l06_route_active" in gate.restrictions
    assert "discourse_update_not_inferred_from_surface_when_l06_available" in gate.restrictions
    assert "legacy_surface_cue_fallback_used" not in gate.restrictions


def test_g01_legacy_l04_only_path_stays_explicit_degraded_fallback() -> None:
    surface, dictum, _, _ = _pipeline("alpha is stable?", "m-g01-rewire-legacy")
    result = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:g01-rewire-legacy",
        cooperation_anchor_ref="o03:g01-rewire-legacy",
    )
    gate = evaluate_grounded_semantic_downstream_gate(result)

    assert result.bundle.normative_l05_l06_route_active is False
    assert result.bundle.legacy_surface_cue_fallback_used is True
    assert result.bundle.legacy_surface_cue_path_not_normative is True
    assert "legacy_surface_cue_fallback_used" in gate.restrictions
    assert "legacy_surface_cue_path_not_normative" in gate.restrictions
    assert "l04_only_input_not_equivalent_to_l05_l06_route" in gate.restrictions
    assert "downstream_authority_degraded" in gate.restrictions


def test_same_dictum_different_l06_continuation_topology_changes_g01_contract_surface() -> None:
    surface, dictum, modus, discourse_update = _pipeline("alpha is stable", "m-g01-rewire-contrast")
    unblocked_states = tuple(
        replace(
            state,
            continuation_status=ContinuationStatus.PROPOSAL_ALLOWED_BUT_ACCEPTANCE_REQUIRED,
            blocked_update_ids=(),
            guarded_continue_allowed=False,
            guarded_continue_forbidden=False,
        )
        for state in discourse_update.bundle.continuation_states
    )
    unblocked_bundle = replace(
        discourse_update.bundle,
        continuation_states=unblocked_states,
        blocked_update_ids=(),
        guarded_update_ids=(),
    )
    unblocked = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:g01-rewire-contrast",
        cooperation_anchor_ref="o03:g01-rewire-contrast",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=unblocked_bundle,
    )

    blocked_states = tuple(
        replace(
            state,
            continuation_status=ContinuationStatus.BLOCKED_PENDING_REPAIR,
            blocked_update_ids=(discourse_update.bundle.update_proposals[0].proposal_id,),
            guarded_continue_allowed=False,
            guarded_continue_forbidden=True,
        )
        for state in discourse_update.bundle.continuation_states
    )
    blocked_bundle = replace(
        discourse_update.bundle,
        continuation_states=blocked_states,
        blocked_update_ids=tuple(
            proposal.proposal_id for proposal in discourse_update.bundle.update_proposals
        ),
        guarded_update_ids=(),
    )
    blocked = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:g01-rewire-contrast",
        cooperation_anchor_ref="o03:g01-rewire-contrast",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=blocked_bundle,
    )

    unblocked_contract = derive_grounded_downstream_contract(unblocked)
    blocked_contract = derive_grounded_downstream_contract(blocked)
    assert unblocked.bundle.l06_blocked_update_present is False
    assert blocked.bundle.l06_blocked_update_present is True
    assert unblocked_contract.l06_blocked_update_present is False
    assert blocked_contract.l06_blocked_update_present is True
    assert (
        "l06_blocked_update_present" not in unblocked_contract.restrictions
        and "l06_blocked_update_present" in blocked_contract.restrictions
    )


def test_normative_route_does_not_project_surface_modus_shortcuts_when_typed_l05_l06_present() -> None:
    surface, dictum, modus, discourse_update = _pipeline(
        "operator said alpha maybe moved??",
        "m-g01-rewire-nosurface",
    )
    result = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:g01-rewire-nosurface",
        cooperation_anchor_ref="o03:g01-rewire-nosurface",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )
    operator_provenance = {carrier.provenance for carrier in result.bundle.operator_carriers}
    source_anchor_provenance = {anchor.provenance for anchor in result.bundle.source_anchors}
    assert all("surface lexical cue" not in provenance for provenance in operator_provenance)
    assert all("punctuation cue" not in provenance for provenance in operator_provenance)
    assert all("surface cue" not in provenance for provenance in source_anchor_provenance)
    assert any("from l05" in provenance or "from l06" in provenance for provenance in operator_provenance)
