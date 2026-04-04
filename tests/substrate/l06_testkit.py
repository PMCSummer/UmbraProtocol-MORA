from __future__ import annotations

from dataclasses import dataclass

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
from substrate.grounded_semantic import build_grounded_semantic_substrate
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


@dataclass(frozen=True, slots=True)
class L06Context:
    surface: object
    syntax: object
    lexical: object
    dictum: object
    modus: object
    discourse_update: object
    grounded: object


def build_l06_context(text: str, case_id: str) -> L06Context:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-l06-{case_id}", content=text),
        SourceMetadata(
            source_id=f"user-l06-{case_id}",
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
    grounded = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m06:{case_id}",
        cooperation_anchor_ref=f"o06:{case_id}",
    )
    return L06Context(
        surface=surface,
        syntax=syntax,
        lexical=lexical,
        dictum=dictum,
        modus=modus,
        discourse_update=discourse_update,
        grounded=grounded,
    )
