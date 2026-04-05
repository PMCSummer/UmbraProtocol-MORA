from __future__ import annotations

from substrate.dictum_candidates import DictumEvidenceKind, build_dictum_candidates
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
    G01EvidenceKind,
    build_grounded_semantic_substrate,
    build_grounded_semantic_substrate_legacy_compatibility,
    derive_grounded_downstream_contract,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    LexicalEvidenceKind,
    build_lexical_grounding_hypotheses,
)
from substrate.modus_hypotheses import ModusEvidenceKind, build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _pipeline(text: str, material_id: str):
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
    return surface, lexical, dictum, modus, discourse_update


def test_l03_emits_factorized_lexical_evidence_records() -> None:
    _, lexical, _, _, _ = _pipeline(
        'he said "alpha moved here now"',
        "m-factor-l03",
    )
    kinds = {record.evidence_kind for record in lexical.bundle.evidence_records}
    assert lexical.bundle.evidence_records
    assert LexicalEvidenceKind.MENTION_ANCHOR in kinds
    assert LexicalEvidenceKind.BASIS_CLASS in kinds
    assert LexicalEvidenceKind.SENSE_CUE in kinds
    assert LexicalEvidenceKind.REFERENCE_CUE in kinds or LexicalEvidenceKind.DEIXIS_CUE in kinds


def test_l04_dictum_evidence_keeps_quote_axis_separate_from_structural_basis() -> None:
    _, _, plain_dictum, _, _ = _pipeline("alpha moved", "m-factor-l04-plain")
    _, _, quoted_dictum, _, _ = _pipeline('"alpha moved"', "m-factor-l04-quoted")
    plain_candidate = plain_dictum.bundle.dictum_candidates[0]
    quoted_candidate = quoted_dictum.bundle.dictum_candidates[0]
    plain_kinds = {record.evidence_kind for record in plain_candidate.evidence_records}
    quoted_kinds = {record.evidence_kind for record in quoted_candidate.evidence_records}
    assert DictumEvidenceKind.PREDICATE_SHELL in plain_kinds
    assert DictumEvidenceKind.ARGUMENT_SLOT in plain_kinds
    assert DictumEvidenceKind.QUOTATION_CUE not in plain_kinds
    assert DictumEvidenceKind.QUOTATION_CUE in quoted_kinds


def test_l05_evidence_records_prevent_single_cue_force_addressivity_collapse() -> None:
    _, _, _, modus, _ = _pipeline(
        'he said "you should leave now"',
        "m-factor-l05",
    )
    assert all(record.evidence_records for record in modus.bundle.hypothesis_records)
    kinds = {
        evidence.evidence_kind
        for record in modus.bundle.hypothesis_records
        for evidence in record.evidence_records
    }
    assert ModusEvidenceKind.FORCE_CUE in kinds
    assert ModusEvidenceKind.ADDRESSIVITY_CUE in kinds or ModusEvidenceKind.QUOTATION_CUE in kinds
    assert ModusEvidenceKind.MODALITY_CUE in kinds


def test_g01_normative_and_compatibility_routes_expose_non_equivalent_evidence_basis() -> None:
    surface, _, dictum, modus, discourse_update = _pipeline(
        'he said "alpha moved?"',
        "m-factor-g01-route",
    )
    normative = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:m-factor-g01-route",
        cooperation_anchor_ref="o03:m-factor-g01-route",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )
    compatibility = build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:m-factor-g01-route",
        cooperation_anchor_ref="o03:m-factor-g01-route",
    )
    normative_kinds = {record.evidence_kind for record in normative.bundle.evidence_records}
    compatibility_kinds = {record.evidence_kind for record in compatibility.bundle.evidence_records}
    assert G01EvidenceKind.NORMATIVE_L05_CUE in normative_kinds
    assert G01EvidenceKind.NORMATIVE_L06_CUE in normative_kinds
    assert G01EvidenceKind.LEGACY_SURFACE_CUE in compatibility_kinds
    assert G01EvidenceKind.NORMATIVE_L05_CUE not in compatibility_kinds
    assert G01EvidenceKind.NORMATIVE_L06_CUE not in compatibility_kinds


def test_g01_contract_requires_reading_factorized_route_specific_evidence() -> None:
    surface, _, dictum, modus, discourse_update = _pipeline(
        "alpha maybe moved?",
        "m-factor-g01-contract",
    )
    normative = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:m-factor-g01-contract",
        cooperation_anchor_ref="o03:m-factor-g01-contract",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )
    compatibility = build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:m-factor-g01-contract",
        cooperation_anchor_ref="o03:m-factor-g01-contract",
    )
    normative_contract = derive_grounded_downstream_contract(normative)
    compatibility_contract = derive_grounded_downstream_contract(compatibility)
    assert normative_contract.factorized_evidence_present is True
    assert normative_contract.normative_factorized_evidence_present is True
    assert normative_contract.compatibility_factorized_evidence_present is False
    assert compatibility_contract.factorized_evidence_present is True
    assert compatibility_contract.normative_factorized_evidence_present is False
    assert compatibility_contract.compatibility_factorized_evidence_present is True
