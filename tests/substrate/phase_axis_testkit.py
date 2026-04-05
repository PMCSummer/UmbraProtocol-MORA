from __future__ import annotations

from dataclasses import dataclass

from substrate.concept_framing import build_concept_framing
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
from substrate.grounded_semantic import (
    build_grounded_semantic_substrate,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import build_semantic_acquisition
from substrate.targeted_clarification import build_targeted_clarification


@dataclass(frozen=True, slots=True)
class PhaseAxisContext:
    surface: object
    syntax: object
    lexical: object
    dictum: object
    modus: object
    discourse_update: object
    grounded_normative: object
    runtime_graph: object
    applicability: object
    perspective: object
    acquisition: object
    framing: object
    intervention: object


def build_phase_axis_context(
    text: str,
    case_id: str,
) -> PhaseAxisContext:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-axis-{case_id}", content=text),
        SourceMetadata(
            source_id=f"user-axis-{case_id}",
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
    grounded_normative = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m-axis:{case_id}",
        cooperation_anchor_ref=f"o-axis:{case_id}",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )
    runtime_graph = build_runtime_semantic_graph(grounded_normative)
    applicability = build_scope_attribution(runtime_graph)
    perspective = build_discourse_provenance_chain(applicability)
    acquisition = build_semantic_acquisition(perspective)
    framing = build_concept_framing(acquisition)
    intervention = build_targeted_clarification(acquisition, framing, discourse_update)
    return PhaseAxisContext(
        surface=surface,
        syntax=syntax,
        lexical=lexical,
        dictum=dictum,
        modus=modus,
        discourse_update=discourse_update,
        grounded_normative=grounded_normative,
        runtime_graph=runtime_graph,
        applicability=applicability,
        perspective=perspective,
        acquisition=acquisition,
        framing=framing,
        intervention=intervention,
    )
