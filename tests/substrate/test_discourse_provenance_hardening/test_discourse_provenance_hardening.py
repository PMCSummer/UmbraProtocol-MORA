from __future__ import annotations

from dataclasses import replace

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import (
    PerspectiveSourceClass,
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
from substrate.grounded_semantic import build_grounded_semantic_substrate_legacy_compatibility
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.scope_attribution import (
    CommitmentLevel,
    SourceScopeClass,
    build_scope_attribution,
)
from substrate.runtime_semantic_graph import build_runtime_semantic_graph


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
    grounded = build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m04:{material_id}",
        cooperation_anchor_ref=f"o04:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    return build_scope_attribution(graph)


def _g04(text: str, material_id: str):
    return build_discourse_provenance_chain(_g03(text, material_id))


def test_role_distinction_reporter_vs_believer_vs_quoted_speaker() -> None:
    base = _g03("he said that you are tired", "m-g04-hard-role-base")
    quoted_bundle = replace(
        base.bundle,
        records=tuple(
            replace(record, source_scope_class=SourceScopeClass.QUOTED)
            for record in base.bundle.records
        ),
    )
    reported_bundle = replace(
        base.bundle,
        records=tuple(
            replace(
                record,
                source_scope_class=SourceScopeClass.REPORTED,
                commitment_level=CommitmentLevel.EXTERNAL_REPORTED,
            )
            for record in base.bundle.records
        ),
    )
    believer_bundle = replace(
        base.bundle,
        records=tuple(
            replace(
                record,
                source_scope_class=SourceScopeClass.REPORTED,
                commitment_level=CommitmentLevel.ASSERTIVE_BOUNDED,
            )
            for record in base.bundle.records
        ),
    )

    quoted = build_discourse_provenance_chain(quoted_bundle)
    reported = build_discourse_provenance_chain(reported_bundle)
    believer = build_discourse_provenance_chain(believer_bundle)

    quoted_sources = {record.source_class for record in quoted.bundle.chain_records}
    reported_sources = {record.source_class for record in reported.bundle.chain_records}
    believer_sources = {record.source_class for record in believer.bundle.chain_records}

    assert PerspectiveSourceClass.QUOTED_SPEAKER in quoted_sources
    assert PerspectiveSourceClass.REPORTED_SOURCE in reported_sources
    assert PerspectiveSourceClass.BELIEVER in believer_sources
    assert quoted_sources != reported_sources
    assert believer_sources != reported_sources


def test_metamorphic_same_content_different_provenance_rewires_constraints() -> None:
    direct = _g04("you are tired", "m-g04-hard-meta-direct")
    quote = _g04('"you are tired"', "m-g04-hard-meta-quote")
    report = _g04("he said that you are tired", "m-g04-hard-meta-report")

    direct_view = derive_perspective_chain_contract_view(direct)
    quote_view = derive_perspective_chain_contract_view(quote)
    report_view = derive_perspective_chain_contract_view(report)

    direct_strength = (
        int(direct_view.response_should_not_echo_as_direct_user_belief)
        + int(direct_view.owner_flattening_risk_detected)
    )
    quote_strength = (
        int(quote_view.response_should_not_echo_as_direct_user_belief)
        + int(quote_view.owner_flattening_risk_detected)
    )
    report_strength = (
        int(report_view.response_should_not_echo_as_direct_user_belief)
        + int(report_view.owner_flattening_risk_detected)
    )

    assert quote_strength >= direct_strength
    assert report_strength >= direct_strength
    assert quote_view.response_should_not_flatten_owner or quote_view.owner_flattening_risk_detected
    assert report_view.response_should_not_flatten_owner or report_view.owner_flattening_risk_detected


def test_metamorphic_nesting_order_changes_chain_or_forces_ambiguity() -> None:
    a = _g04("petya said masha thinks i am afraid", "m-g04-hard-nesting-a")
    b = _g04("petya thinks masha said i am afraid", "m-g04-hard-nesting-b")
    sig_a = {(r.discourse_level, r.assertion_mode.value, r.source_class.value) for r in a.bundle.chain_records}
    sig_b = {(r.discourse_level, r.assertion_mode.value, r.source_class.value) for r in b.bundle.chain_records}
    if sig_a == sig_b:
        assert a.bundle.ambiguity_reasons or b.bundle.ambiguity_reasons
    else:
        assert sig_a != sig_b


def test_cross_turn_denial_marks_repair_pending_instead_of_silent_append() -> None:
    base = _g03("no, i did not say that", "m-g04-hard-repair")
    with_prior = replace(
        base,
        telemetry=replace(
            base.telemetry,
            source_lineage=("anchor:turn-1", "report:external", "anchor:turn-2"),
        ),
    )
    result = build_discourse_provenance_chain(with_prior)
    gate = evaluate_perspective_chain_downstream_gate(result)
    assert any(link.attachment_state.value == "repair_pending" for link in result.bundle.cross_turn_links)
    assert "cross_turn_repair_pending" in gate.restrictions
    assert "downstream_authority_degraded" in gate.restrictions


def test_shallow_chain_risk_is_not_treated_as_clean_owner_truth() -> None:
    result = _g04("you are tired?", "m-g04-hard-shallow")
    gate = evaluate_perspective_chain_downstream_gate(result)
    view = derive_perspective_chain_contract_view(result)
    assert "accepted_chain_not_owner_truth" in gate.restrictions
    assert "usability_must_be_read" in gate.restrictions
    assert view.accepted_chain_not_owner_truth is True
    assert view.requires_usability_read is True
