from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import (
    CrossTurnAttachmentState,
    ProvenanceUsabilityClass,
    build_discourse_provenance_chain,
    derive_perspective_chain_contract_view,
    evaluate_perspective_chain_downstream_gate,
)
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import build_grounded_semantic_substrate
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import (
    CommitmentLevel,
    SourceScopeClass,
    build_scope_attribution,
)


def _g03(text: str, material_id: str):
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
    grounded = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m04:{material_id}",
        cooperation_anchor_ref=f"o04:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    return build_scope_attribution(graph)


def _g04(text: str, material_id: str):
    return build_discourse_provenance_chain(_g03(text, material_id))


def test_quote_report_direct_do_not_flatten_commitment_owner() -> None:
    direct = _g04("you are tired", "m-g04-direct")
    quoted = _g04('"you are tired"', "m-g04-quoted")
    reported = _g04("he said that you are tired", "m-g04-reported")

    direct_owners = {record.commitment_owner.value for record in direct.bundle.chain_records}
    quoted_owners = {record.commitment_owner.value for record in quoted.bundle.chain_records}
    reported_owners = {record.commitment_owner.value for record in reported.bundle.chain_records}

    assert direct_owners != quoted_owners or direct_owners != reported_owners
    assert any(
        "response_should_not_echo_as_direct_user_belief" in wrapped.downstream_constraints
        for wrapped in quoted.bundle.wrapped_propositions
    )
    assert any(
        "response_should_not_echo_as_direct_user_belief" in wrapped.downstream_constraints
        for wrapped in reported.bundle.wrapped_propositions
    )


def test_cross_turn_repair_cases_signal_reattachment_or_repair_pending() -> None:
    repaired = _g04("i was quoting him", "m-g04-repair")
    denied = _g04("no, i did not say that", "m-g04-denied")

    states = {link.attachment_state for link in repaired.bundle.cross_turn_links + denied.bundle.cross_turn_links}
    assert states & {CrossTurnAttachmentState.REATTACHED, CrossTurnAttachmentState.REPAIR_PENDING, CrossTurnAttachmentState.STABLE}


def test_downstream_contract_obedience_uses_only_g04_output() -> None:
    result = _g04('he said "you are tired"', "m-g04-contract")
    view = derive_perspective_chain_contract_view(result)
    assert view.requires_chain_read is True
    assert view.requires_usability_read is True
    assert view.closure_requires_chain_consistency_check is True
    assert view.response_should_not_echo_as_direct_user_belief is True
    assert view.accepted_chain_not_owner_truth is True
    assert view.strong_owner_commitment_permitted is False


@pytest.mark.parametrize(
    ("ablation_id", "ablate"),
    (
        (
            "weaken_source_markers",
            lambda bundle: replace(
                bundle,
                records=tuple(
                    replace(record, source_scope_class=SourceScopeClass.DIRECT_ASSERTION)
                    for record in bundle.records
                ),
            ),
        ),
        (
            "weaken_commitment_markers",
            lambda bundle: replace(
                bundle,
                records=tuple(
                    replace(record, commitment_level=CommitmentLevel.ASSERTIVE_BOUNDED)
                    for record in bundle.records
                ),
            ),
        ),
        (
            "weaken_turn_link_metadata",
            lambda bundle: replace(bundle, source_surface_ref=None),
        ),
        (
            "weaken_repair_metadata",
            lambda bundle: replace(bundle, ambiguity_reasons=()),
        ),
        (
            "weaken_modality_hint",
            lambda bundle: replace(
                bundle,
                records=tuple(
                    replace(record, source_scope_class=SourceScopeClass.DIRECT_ASSERTION)
                    for record in bundle.records
                ),
                low_coverage_mode=True,
                low_coverage_reasons=tuple(dict.fromkeys((*bundle.low_coverage_reasons, "ablation_modality_removed"))),
            ),
        ),
    ),
)
def test_ablation_matrix_for_targeted_degradation(ablation_id: str, ablate) -> None:
    base = _g03('he said "you are not tired?"', f"m-g04-ablate-{ablation_id}")
    baseline = build_discourse_provenance_chain(base)
    degraded = build_discourse_provenance_chain(ablate(base.bundle))
    gate = evaluate_perspective_chain_downstream_gate(degraded)
    view = derive_perspective_chain_contract_view(degraded)

    baseline_sig = {
        (record.assertion_mode.value, record.source_class.value, record.commitment_owner.value)
        for record in baseline.bundle.chain_records
    }
    degraded_sig = {
        (record.assertion_mode.value, record.source_class.value, record.commitment_owner.value)
        for record in degraded.bundle.chain_records
    }
    assert baseline_sig != degraded_sig or baseline.bundle.ambiguity_reasons != degraded.bundle.ambiguity_reasons

    assert "perspective_chain_must_be_read" in gate.restrictions
    assert view.requires_chain_read is True
    if ablation_id in {"weaken_turn_link_metadata", "weaken_modality_hint"}:
        assert gate.usability_class in {
            ProvenanceUsabilityClass.DEGRADED_BOUNDED,
            ProvenanceUsabilityClass.BLOCKED,
        } or "downstream_authority_degraded" in gate.restrictions
    if ablation_id == "weaken_source_markers":
        assert any(
            wrapped.source_class.value in {"current_utterer", "unknown", "mixed"}
            for wrapped in degraded.bundle.wrapped_propositions
        )
    if ablation_id == "weaken_turn_link_metadata":
        assert "discourse_anchor_missing" in degraded.bundle.ambiguity_reasons


def test_depth_stress_up_to_three_levels_or_explicit_degraded_mode() -> None:
    base = _g03("petya said that masha thinks that i am tired", "m-g04-depth")
    stressed = replace(
        base,
        telemetry=replace(
            base.telemetry,
            source_lineage=(
                "anchor:turn-1",
                "report:petya",
                "belief:masha",
                "quote:inner",
                "anchor:turn-2",
            ),
        ),
    )
    rebuilt = build_discourse_provenance_chain(stressed)
    gate = evaluate_perspective_chain_downstream_gate(rebuilt)
    max_depth = max(record.discourse_level for record in rebuilt.bundle.chain_records)
    if max_depth < 3:
        assert "downstream_authority_degraded" in gate.restrictions or rebuilt.bundle.ambiguity_reasons
    else:
        assert max_depth >= 3
