from __future__ import annotations

from substrate.concept_framing import build_concept_framing
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
from substrate.discourse_update import build_discourse_update
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import build_semantic_acquisition
from substrate.state import create_empty_state
from substrate.targeted_clarification import (
    build_targeted_clarification,
    evaluate_targeted_clarification_downstream_gate,
)
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_l05_l06_g07_normative_runtime_path() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g07-l06-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-05T00:00:00+00:00",
            event_id="ev-g07-l06-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g07-l06-stage", content='he said "you should stop?"'),
        SourceMetadata(
            source_id="user-g07-l06-stage",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    lexical_result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g07-l06-stage"),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g07-l06-stage"),
    )
    modus_result = build_modus_hypotheses(dictum_result)
    discourse_update_result = build_discourse_update(modus_result)
    grounded_result = build_grounded_semantic_substrate_normative(
        dictum_result,
        utterance_surface=surface_result,
        memory_anchor_ref="m07:g07-l06-stage",
        cooperation_anchor_ref="o07:g07-l06-stage",
    )
    runtime_graph_result = build_runtime_semantic_graph(grounded_result)
    applicability_result = build_scope_attribution(runtime_graph_result)
    perspective_result = build_discourse_provenance_chain(applicability_result)
    acquisition_result = build_semantic_acquisition(perspective_result)
    framing_result = build_concept_framing(acquisition_result)
    intervention_result = build_targeted_clarification(
        acquisition_result,
        framing_result,
        discourse_update_result,
    )

    gate = evaluate_targeted_clarification_downstream_gate(intervention_result)
    assert intervention_result.bundle.intervention_records
    assert intervention_result.bundle.l06_upstream_bound_here is True
    assert intervention_result.bundle.l06_continuation_topology_present is True
    assert intervention_result.bundle.source_acquisition_ref_kind == "phase_native_derived_ref"
    assert intervention_result.bundle.source_framing_ref_kind == "phase_native_derived_ref"
    assert intervention_result.bundle.source_discourse_update_ref_kind == "phase_native_derived_ref"
    assert (
        intervention_result.bundle.source_discourse_update_ref
        != intervention_result.bundle.source_discourse_update_lineage_ref
    )
    assert "l06_proposal_requires_acceptance_read" in gate.restrictions
    assert "intervention_not_discourse_acceptance" in gate.restrictions
