from substrate.dictum_candidates import build_dictum_candidates
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


def test_stage_contour_l05_exists_but_g01_still_operates_on_legacy_l04_bridge_as_debt() -> None:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l05-g01-legacy", content='he said "you are tired?"'),
        SourceMetadata(
            source_id="user-l05-g01-legacy",
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
    g01_result = build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m05:l05-g01-legacy",
        cooperation_anchor_ref="o05:l05-g01-legacy",
    )

    assert l05_result.bundle.hypothesis_records
    assert l05_result.bundle.l06_downstream_not_bound_here is True
    assert g01_result.bundle.modus_carriers
    assert g01_result.bundle.operator_carriers
    assert g01_result.bundle.source_anchors
