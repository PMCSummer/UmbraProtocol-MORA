from dataclasses import replace

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import (
    ViabilityCalibrationSpec,
    ViabilityContext,
    compute_viability_control_state,
    create_default_viability_calibration_spec,
)


def _regulation(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-cal-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-cal-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-cal-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-calibration",)),
    ).state


def _stage_rank(value: str) -> int:
    if value == "critical":
        return 4
    if value == "threat":
        return 3
    if value == "elevated":
        return 2
    return 1


def test_shorter_time_to_boundary_does_not_reduce_escalation() -> None:
    current = _regulation(energy=19.0, cognitive=91.0, safety=38.0)
    prior_slow = _regulation(energy=20.0, cognitive=90.0, safety=40.0)
    prior_fast = _regulation(energy=45.0, cognitive=64.0, safety=72.0)
    affordances = generate_regulation_affordances(
        regulation_state=current,
        capability_state=create_default_capability_state(),
    )
    preferences = create_empty_preference_state()
    slow = compute_viability_control_state(
        current,
        affordances,
        preferences,
        context=ViabilityContext(prior_regulation_state=prior_slow),
    )
    fast = compute_viability_control_state(
        current,
        affordances,
        preferences,
        context=ViabilityContext(prior_regulation_state=prior_fast),
    )
    assert fast.state.predicted_time_to_boundary is not None
    if slow.state.predicted_time_to_boundary is not None:
        assert fast.state.predicted_time_to_boundary <= slow.state.predicted_time_to_boundary
    assert _stage_rank(fast.state.escalation_stage.value) >= _stage_rank(
        slow.state.escalation_stage.value
    )


def test_recovery_means_evidence_does_not_inflate_stage_under_same_threat() -> None:
    state = _regulation(energy=17.0, cognitive=92.0, safety=37.0)
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    preferences = create_empty_preference_state()
    default_result = compute_viability_control_state(state, affordances, preferences)
    strict_calibration = replace(
        create_default_viability_calibration_spec(),
        min_recoverability_evidence_quality=0.95,
    )
    strict_result = compute_viability_control_state(
        state,
        affordances,
        preferences,
        calibration_spec=strict_calibration,
    )
    assert strict_result.state.recoverability_estimate is None
    assert _stage_rank(strict_result.state.escalation_stage.value) <= _stage_rank(
        default_result.state.escalation_stage.value
    )


def test_invalid_calibration_threshold_order_fails_honestly() -> None:
    state = _regulation(energy=20.0, cognitive=88.0, safety=42.0)
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    invalid = ViabilityCalibrationSpec(
        calibration_id="bad-calibration",
        pressure_elevated_threshold=0.7,
        pressure_threat_threshold=0.5,
        pressure_critical_threshold=0.9,
    )
    result = compute_viability_control_state(
        state,
        affordances,
        create_empty_preference_state(),
        calibration_spec=invalid,
    )
    assert result.abstain is True
    assert "invalid calibration pressure thresholds" in (result.abstain_reason or "")


def test_calibration_schema_mismatch_surfaces_and_caps_strong_override_claim() -> None:
    state = _regulation(energy=16.0, cognitive=93.0, safety=36.0)
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    mismatched = replace(
        create_default_viability_calibration_spec(),
        schema_version="r04.calibration.v0",
    )
    result = compute_viability_control_state(
        state,
        affordances,
        create_empty_preference_state(),
        calibration_spec=mismatched,
        context=ViabilityContext(
            expected_calibration_schema_version="r04.calibration.v1",
        ),
    )
    assert "calibration_schema_incompatible" in result.telemetry.boundary_compatibility
    assert result.state.no_strong_override_claim is True


def test_expected_calibration_id_mismatch_is_explicit_and_non_silent() -> None:
    state = _regulation(energy=18.0, cognitive=88.0, safety=44.0)
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    result = compute_viability_control_state(
        state,
        affordances,
        create_empty_preference_state(),
        context=ViabilityContext(expected_calibration_id="r04-nonexistent-calibration"),
    )
    assert "calibration_id_incompatible" in result.telemetry.boundary_compatibility
    assert result.state.no_strong_override_claim is True
