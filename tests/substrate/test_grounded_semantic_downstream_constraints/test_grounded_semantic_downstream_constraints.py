from __future__ import annotations

from dataclasses import replace

from substrate.dictum_candidates import build_dictum_candidates
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import (
    OperatorKind,
    SourceAnchorKind,
    UncertaintyKind,
    build_grounded_semantic_substrate_legacy_compatibility,
    evaluate_grounded_semantic_downstream_gate,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _build_result(text: str, material_id: str):
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
    return build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )


def test_source_assertion_quote_and_report_paths_do_not_collapse() -> None:
    direct = _build_result("alpha is stable", "m-g01-src-direct")
    quoted = _build_result('"alpha is stable"', "m-g01-src-quote")
    reported = _build_result("operator said alpha is stable", "m-g01-src-report")

    direct_ops = {carrier.operator_kind for carrier in direct.bundle.operator_carriers}
    quote_ops = {carrier.operator_kind for carrier in quoted.bundle.operator_carriers}
    report_ops = {carrier.operator_kind for carrier in reported.bundle.operator_carriers}

    direct_anchor_kinds = {anchor.anchor_kind for anchor in direct.bundle.source_anchors}
    quote_anchor_kinds = {anchor.anchor_kind for anchor in quoted.bundle.source_anchors}
    report_anchor_kinds = {anchor.anchor_kind for anchor in reported.bundle.source_anchors}
    report_uncertainty = {marker.uncertainty_kind for marker in reported.bundle.uncertainty_markers}

    assert OperatorKind.QUOTATION not in direct_ops
    assert SourceAnchorKind.QUOTE_BOUNDARY not in direct_anchor_kinds
    assert OperatorKind.QUOTATION in quote_ops
    assert SourceAnchorKind.QUOTE_BOUNDARY in quote_anchor_kinds
    assert SourceAnchorKind.REPORTED_SPEECH in report_anchor_kinds
    assert UncertaintyKind.SOURCE_SCOPE_UNCERTAIN in report_uncertainty
    assert quote_ops != direct_ops


def test_dictum_and_modus_carriers_are_separated_not_collapsed_into_content() -> None:
    result = _build_result("maybe alpha can move now?", "m-g01-modus")
    dictum_ids = {carrier.carrier_id for carrier in result.bundle.dictum_carriers}
    modus_ids = {carrier.carrier_id for carrier in result.bundle.modus_carriers}
    assert result.bundle.dictum_carriers
    assert result.bundle.modus_carriers
    assert dictum_ids.isdisjoint(modus_ids)
    assert any("modus_stance" in carrier.stance_kind for carrier in result.bundle.modus_carriers)


def test_without_g01_carriers_downstream_gate_degrades_for_same_raw_text() -> None:
    full = _build_result("we do not track alpha here", "m-g01-bypass-full")
    degraded_bundle = replace(
        full.bundle,
        phrase_scaffolds=(),
        dictum_carriers=(),
        operator_carriers=(),
    )

    full_gate = evaluate_grounded_semantic_downstream_gate(full)
    degraded_gate = evaluate_grounded_semantic_downstream_gate(degraded_bundle)

    assert full_gate.accepted is True
    assert degraded_gate.accepted is False
    assert "no_usable_scaffold" in degraded_gate.restrictions
