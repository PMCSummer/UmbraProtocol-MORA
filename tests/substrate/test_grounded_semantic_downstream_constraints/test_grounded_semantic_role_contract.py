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
    GroundedAuthorityLevel,
    GroundedSourceMode,
    build_grounded_semantic_substrate,
    derive_grounded_downstream_contract,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _dictum_and_surface(text: str, material_id: str):
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
    return dictum, surface


def _build_result(text: str, material_id: str, *, with_surface: bool = True):
    dictum, surface = _dictum_and_surface(text, material_id)
    return build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface if with_surface else None,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )


def test_role_contract_distinguishes_source_modes_without_raw_text_access() -> None:
    direct = derive_grounded_downstream_contract(_build_result("i track alpha", "m-g01-role-direct"))
    quoted = derive_grounded_downstream_contract(_build_result('"alpha moved"', "m-g01-role-quote"))
    reported = derive_grounded_downstream_contract(
        _build_result("operator said alpha moved", "m-g01-role-report")
    )

    assert direct.source_mode is GroundedSourceMode.DIRECT_ASSERTION
    assert quoted.source_mode in {GroundedSourceMode.QUOTED_CONTENT, GroundedSourceMode.MIXED}
    assert reported.source_mode is GroundedSourceMode.REPORTED_CONTENT


def test_role_contract_distinguishes_negation_and_modality() -> None:
    negated = derive_grounded_downstream_contract(_build_result("we do not track alpha", "m-g01-role-neg"))
    plain = derive_grounded_downstream_contract(_build_result("we track alpha", "m-g01-role-plain"))
    modal = derive_grounded_downstream_contract(_build_result("maybe alpha can move?", "m-g01-role-modal"))

    assert negated.negation_present is True
    assert plain.negation_present is False
    assert modal.interrogation_or_modality_present is True


def test_role_contract_marks_noisy_uncertainty_as_elevated() -> None:
    noisy = derive_grounded_downstream_contract(_build_result("i i alpha ???", "m-g01-role-noisy"))
    calm = derive_grounded_downstream_contract(_build_result("i track alpha", "m-g01-role-calm"))
    assert noisy.uncertainty_elevated is True
    assert calm.uncertainty_elevated in {False, True}
    assert noisy.low_coverage_mode or noisy.uncertainty_elevated


def test_ablation_remove_source_anchors_breaks_source_distinction() -> None:
    result = _build_result("operator said alpha moved", "m-g01-ablate-source")
    base = derive_grounded_downstream_contract(result)
    ablated = derive_grounded_downstream_contract(
        replace(result.bundle, source_anchors=())
    )
    assert base.can_distinguish_source_handling is True
    assert ablated.can_distinguish_source_handling is False
    assert ablated.authority_level is GroundedAuthorityLevel.DEGRADED_SCAFFOLD_ONLY


def test_ablation_remove_operator_carriers_breaks_scope_distinction() -> None:
    result = _build_result("we do not track alpha?", "m-g01-ablate-op")
    base = derive_grounded_downstream_contract(result)
    ablated = derive_grounded_downstream_contract(
        replace(result.bundle, operator_carriers=())
    )
    assert base.can_distinguish_operator_handling is True
    assert ablated.can_distinguish_operator_handling is False
    assert ablated.negation_present is False
    assert ablated.interrogation_or_modality_present is False


def test_ablation_remove_modus_carriers_breaks_dictum_modus_split_signal() -> None:
    result = _build_result("maybe alpha can move?", "m-g01-ablate-modus")
    base = derive_grounded_downstream_contract(result)
    ablated = derive_grounded_downstream_contract(
        replace(result.bundle, modus_carriers=())
    )
    assert base.dictum_modus_split_present in {True, False}
    assert ablated.dictum_modus_split_present is False


def test_ablation_remove_uncertainty_markers_hides_noisy_stance() -> None:
    result = _build_result("i i alpha ???", "m-g01-ablate-unc")
    base = derive_grounded_downstream_contract(result)
    ablated = derive_grounded_downstream_contract(
        replace(result.bundle, uncertainty_markers=())
    )
    assert base.uncertainty_elevated is True
    assert ablated.uncertainty_elevated is False


def test_ablation_without_surface_forces_degraded_mode() -> None:
    with_surface = derive_grounded_downstream_contract(
        _build_result("operator said alpha moved", "m-g01-ablate-nosurface-a", with_surface=True)
    )
    no_surface = derive_grounded_downstream_contract(
        _build_result("operator said alpha moved", "m-g01-ablate-nosurface-b", with_surface=False)
    )
    assert with_surface.authority_level in {
        GroundedAuthorityLevel.SCAFFOLD_ONLY,
        GroundedAuthorityLevel.DEGRADED_SCAFFOLD_ONLY,
    }
    assert no_surface.authority_level is GroundedAuthorityLevel.DEGRADED_SCAFFOLD_ONLY
    assert no_surface.low_coverage_mode is True


def test_ablation_phrase_scaffold_plus_dictum_only_stays_accepted_but_degraded() -> None:
    result = _build_result("i track alpha", "m-g01-ablate-minimal")
    minimal_bundle = replace(
        result.bundle,
        operator_carriers=(),
        modus_carriers=(),
        source_anchors=(),
        uncertainty_markers=(),
        low_coverage_mode=False,
        low_coverage_reasons=(),
    )
    view = derive_grounded_downstream_contract(minimal_bundle)
    assert view.authority_level is GroundedAuthorityLevel.DEGRADED_SCAFFOLD_ONLY
    assert view.usable_for_distinction is False
