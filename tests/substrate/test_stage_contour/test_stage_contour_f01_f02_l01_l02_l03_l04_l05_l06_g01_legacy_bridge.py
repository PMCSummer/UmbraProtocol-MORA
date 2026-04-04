from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_update import build_discourse_update
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
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def test_stage_contour_l06_exists_but_g01_legacy_bridge_remains_operational_debt() -> None:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l06-g01-legacy", content='he said "you are tired?"'),
        SourceMetadata(
            source_id="user-l06-g01-legacy",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    l05_result = build_modus_hypotheses(dictum)
    l06_result = build_discourse_update(l05_result)
    g01_result = build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m06:l06-g01-legacy",
        cooperation_anchor_ref="o06:l06-g01-legacy",
    )

    assert l06_result.bundle.update_proposals
    assert l06_result.bundle.legacy_g01_bypass_risk_present is True
    assert g01_result.bundle.normative_l05_l06_route_active is False
    assert g01_result.bundle.legacy_surface_cue_fallback_used is True
    assert g01_result.bundle.legacy_surface_cue_path_not_normative is True
    assert "legacy_surface_cue_fallback_used" in g01_result.telemetry.downstream_gate.restrictions
    assert g01_result.bundle.modus_carriers
    assert g01_result.bundle.source_anchors
