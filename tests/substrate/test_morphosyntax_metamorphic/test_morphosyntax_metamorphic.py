from dataclasses import fields

from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.morphosyntax import SyntaxHypothesis, build_morphosyntax_candidate_space


def _surface_result(text: str, material_id: str | None = None):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id or f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return build_utterance_surface(epistemic.unit)


def _unresolved_count(result) -> int:
    return sum(len(h.unresolved_attachments) for h in result.hypothesis_set.hypotheses)


def test_punctuation_perturbation_changes_clause_graph_predictably() -> None:
    plain = build_morphosyntax_candidate_space(_surface_result("alpha beta gamma delta"))
    punct = build_morphosyntax_candidate_space(_surface_result("alpha beta; gamma delta."))

    assert punct.telemetry.clause_count >= plain.telemetry.clause_count
    punct_kinds = {
        clause.boundary_kind.value
        for clause in punct.hypothesis_set.hypotheses[0].clause_graph.clauses
    }
    assert "clause" in punct_kinds or "sentence" in punct_kinds


def test_agreement_perturbation_changes_agreement_cues_predictably() -> None:
    matched = build_morphosyntax_candidate_space(_surface_result("we are blarf."))
    mismatched = build_morphosyntax_candidate_space(_surface_result("we is blarf."))

    matched_statuses = {cue.status.value for cue in matched.hypothesis_set.hypotheses[0].agreement_cues}
    mismatched_statuses = {
        cue.status.value for cue in mismatched.hypothesis_set.hypotheses[0].agreement_cues
    }
    assert "conflict" not in matched_statuses
    assert "conflict" in mismatched_statuses


def test_ambiguous_attachment_variants_do_not_collapse_to_same_settled_state() -> None:
    ambiguous = build_morphosyntax_candidate_space(_surface_result("alpha beta ... gamma delta"))
    settled = build_morphosyntax_candidate_space(_surface_result("alpha beta gamma delta."))

    assert ambiguous.hypothesis_set.no_selected_winner is True
    assert ambiguous.hypothesis_set.ambiguity_present is True
    assert (
        len(ambiguous.hypothesis_set.hypotheses) > len(settled.hypothesis_set.hypotheses)
        or _unresolved_count(ambiguous) > _unresolved_count(settled)
    )


def test_harmless_whitespace_changes_preserve_typed_structure_and_lineage() -> None:
    compact = build_morphosyntax_candidate_space(_surface_result("blarf zint.", material_id="m-ws"))
    spaced = build_morphosyntax_candidate_space(
        _surface_result("  blarf\tzint.  ", material_id="m-ws")
    )

    assert compact.abstain is False
    assert spaced.abstain is False
    assert compact.telemetry.morphology_feature_count == spaced.telemetry.morphology_feature_count
    assert compact.telemetry.input_surface_ref == compact.hypothesis_set.source_surface_ref
    assert spaced.telemetry.input_surface_ref == spaced.hypothesis_set.source_surface_ref


def test_quote_or_parenthetical_presence_changes_structure_without_semantic_fields() -> None:
    plain = build_morphosyntax_candidate_space(_surface_result("alpha beta."))
    marked = build_morphosyntax_candidate_space(_surface_result('("alpha beta") gamma.'))

    signature_plain = (
        plain.telemetry.morphology_feature_count,
        plain.telemetry.clause_count,
        plain.telemetry.unresolved_edge_count,
    )
    signature_marked = (
        marked.telemetry.morphology_feature_count,
        marked.telemetry.clause_count,
        marked.telemetry.unresolved_edge_count,
    )
    assert signature_marked != signature_plain

    forbidden = {"dictum", "meaning", "truth", "illocution", "intent", "commitment"}
    assert forbidden.isdisjoint({f.name for f in fields(SyntaxHypothesis)})
