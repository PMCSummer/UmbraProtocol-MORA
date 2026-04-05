from __future__ import annotations

from dataclasses import dataclass

import pytest

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
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import build_semantic_acquisition
from substrate.targeted_clarification import build_targeted_clarification


@dataclass(frozen=True, slots=True)
class G07Context:
    acquisition: object
    framing: object
    discourse_update: object
    intervention: object


@pytest.fixture
def g07_factory():
    def _factory(text: str, material_id: str) -> G07Context:
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
        grounded = build_grounded_semantic_substrate_normative(
            dictum,
            utterance_surface=surface,
            memory_anchor_ref=f"m07:{material_id}",
            cooperation_anchor_ref=f"o07:{material_id}",
        )
        graph = build_runtime_semantic_graph(grounded)
        applicability = build_scope_attribution(graph)
        perspective = build_discourse_provenance_chain(applicability)
        acquisition = build_semantic_acquisition(perspective)
        framing = build_concept_framing(acquisition)
        intervention = build_targeted_clarification(acquisition, framing, discourse_update)
        return G07Context(
            acquisition=acquisition,
            framing=framing,
            discourse_update=discourse_update,
            intervention=intervention,
        )

    return _factory
