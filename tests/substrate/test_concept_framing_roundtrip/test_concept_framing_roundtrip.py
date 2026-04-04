from __future__ import annotations

from substrate.concept_framing import (
    build_concept_framing,
    concept_framing_result_to_payload,
)
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
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
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import build_semantic_acquisition


def _g06(text: str, material_id: str):
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
        memory_anchor_ref=f"m06:{material_id}",
        cooperation_anchor_ref=f"o06:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    perspective = build_discourse_provenance_chain(applicability)
    acquisition = build_semantic_acquisition(perspective)
    return build_concept_framing(acquisition)


def test_snapshot_roundtrip_contains_load_bearing_framing_fields() -> None:
    result = _g06('he said "you are tired?"', "m-g06-roundtrip")
    payload = concept_framing_result_to_payload(result)
    assert payload["bundle"]["framing_records"]
    assert payload["bundle"]["competition_links"]
    first = payload["bundle"]["framing_records"][0]
    assert "frame_family" in first
    assert "framing_status" in first
    assert "framing_basis" in first
    assert "alternative_framings" in first
    assert "vulnerability_profile" in first
    assert "downstream_cautions" in first
    assert payload["bundle"]["l06_update_proposal_not_bound_here"] is True
    assert payload["telemetry"]["downstream_gate"]["restrictions"]
