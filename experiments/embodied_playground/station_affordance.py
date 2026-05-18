from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys

try:
    from substrate.ap01_subject_action_publication import (
        AP01ActionPublicationCandidate,
        AP01ActionPublicationCandidateSet,
        AP01CandidateOrigin,
        build_ap01_subject_action_publication,
    )
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from substrate.ap01_subject_action_publication import (
        AP01ActionPublicationCandidate,
        AP01ActionPublicationCandidateSet,
        AP01CandidateOrigin,
        build_ap01_subject_action_publication,
    )

from .grid_world import GridWorldBackend
from .models import (
    AP01RequestRef,
    ActionEffectFrame,
    CorrelationStatus,
    EffectStatus,
    PublishedActionEnvelope,
)
from .scenarios import GridWorldScenarioConfig
from .station_scenarios import StationScenarioSpec, list_station_scenarios, station_scenario_for_id


@dataclass(frozen=True, slots=True)
class StationAffordanceRecord:
    station_ref: str | None
    visible: bool
    reachable: bool
    proximate: bool
    required_input_refs: tuple[str, ...]
    available_input_refs: tuple[str, ...]
    missing_input_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    usable_status: str
    affordance_basis_refs: tuple[str, ...]
    action_surface_supports_use_station: bool
    hidden_recipe_used: bool = False
    scenario_label_used: bool = False


@dataclass(frozen=True, slots=True)
class StationUseAttemptRecord:
    attempt_id: str
    ap01_request_ref: str | None
    station_ref: str | None
    input_refs: tuple[str, ...]
    effect_ref: str | None
    correlation_status: str
    outcome: str
    inventory_delta: dict[str, object]
    world_delta: dict[str, object]
    recipe_claimed: bool = False
    mature_schema_created: bool = False
    hidden_recipe_used: bool = False


@dataclass(frozen=True, slots=True)
class StationAblationCheck:
    ablation_id: str
    scenario_id: str
    expected_degradation: tuple[str, ...]
    observed_behavior: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StationAffordanceProofRun:
    run_id: str
    scenario_id: str
    station_ref: str | None
    public_station_basis: StationAffordanceRecord
    proximity_status: str
    input_status: str
    blocked_status: str
    affordance_status: str
    station_use_candidate_status: str
    ap01_publication_status: str
    world_submission_status: str
    effect_status: str
    effect_refs: tuple[str, ...]
    inventory_delta_refs: tuple[str, ...]
    world_delta_refs: tuple[str, ...]
    missing_input_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    falsifier_results: dict[str, bool]
    ablation_results: tuple[StationAblationCheck, ...]
    claim_safe_verdict: str
    protected_evaluator_only_rule_present: bool
    mature_schema_created: bool = False
    hidden_recipe_used: bool = False
    action_request_emitted: bool = False
    cause_confirmed: bool = False
    fact_claimed: bool = False
    acp01_involved: bool = False
    acp01_candidate_status: str = "not_involved"
    attempt_record: StationUseAttemptRecord | None = None


_CLAIM_BOUNDARY = (
    "P14 station affordance proof only: not recipe learning, no automation, no mature schema, "
    "and no general tool-use or consciousness claim."
)


def list_station_affordance_cases() -> tuple[StationScenarioSpec, ...]:
    return list_station_scenarios()


def run_station_affordance_case(scenario_id: str) -> StationAffordanceProofRun:
    spec = station_scenario_for_id(scenario_id)
    backend = _build_backend(spec)
    observation = backend.observe("subject_a")
    affordance = _derive_station_affordance(spec=spec, observation=observation)

    attempt_status = "not_attempted"
    ap01_status = "not_attempted"
    world_submission_status = "not_submitted"
    effect: ActionEffectFrame | None = None
    attempt_record: StationUseAttemptRecord | None = None

    if spec.use_passive_effect_fixture:
        effect = _passive_station_effect_fixture(scenario_id=spec.scenario_id)
        world_submission_status = "passive_world_event"
    elif spec.attempt_station_use:
        if affordance.station_ref and affordance.action_surface_supports_use_station:
            attempt_status = "proposed"
            ap01_result = _publish_use_station_request(
                scenario_id=spec.scenario_id,
                observation_id=observation.observation_id,
                station_ref=affordance.station_ref,
                input_refs=affordance.available_input_refs,
            )
            if ap01_result.published_requests:
                request = ap01_result.published_requests[0]
                ap01_status = "published"
                envelope = _request_to_envelope(request=request, scenario_id=spec.scenario_id)
                effect = backend.submit_action(envelope)
                world_submission_status = "submitted"
                attempt_status = "published"
                attempt_record = _attempt_from_effect(
                    scenario_id=spec.scenario_id,
                    station_ref=affordance.station_ref,
                    input_refs=affordance.available_input_refs,
                    request_ref=request.request_id,
                    effect=effect,
                )
            else:
                ap01_status = "blocked"
                world_submission_status = "not_submitted"
        else:
            attempt_status = "invalid_no_basis"
            ap01_status = "not_attempted"
    else:
        attempt_status = "not_attempted"
        ap01_status = "not_attempted"

    effect_status = str(getattr(effect.effect_status, "value", effect.effect_status)) if effect is not None else "not_attempted"
    effect_refs = (effect.effect_id,) if effect is not None else ()
    inventory_delta_refs = _delta_refs(effect.effect_id, effect.inventory_delta) if effect is not None else ()
    world_delta_refs = _delta_refs(effect.effect_id, effect.world_delta_public) if effect is not None else ()

    if attempt_record is None:
        default_outcome = "not_attempted"
        if ap01_status == "published" and world_submission_status == "submitted":
            if effect_status == EffectStatus.SUCCEEDED.value:
                default_outcome = "succeeded"
            elif effect_status == EffectStatus.BLOCKED.value:
                default_outcome = "blocked"
            elif effect_status == EffectStatus.PARTIAL.value:
                default_outcome = "succeeded"
            else:
                default_outcome = "invalid"
        attempt_record = StationUseAttemptRecord(
            attempt_id=f"p14:{spec.scenario_id}:attempt:none",
            ap01_request_ref=None,
            station_ref=affordance.station_ref,
            input_refs=affordance.available_input_refs,
            effect_ref=effect.effect_id if effect is not None else None,
            correlation_status=(
                str(getattr(effect.correlation_status, "value", effect.correlation_status))
                if effect is not None
                else CorrelationStatus.AMBIGUOUS.value
            ),
            outcome=default_outcome,
            inventory_delta=dict(effect.inventory_delta if effect is not None else {}),
            world_delta=dict(effect.world_delta_public if effect is not None else {}),
            recipe_claimed=False,
            mature_schema_created=False,
            hidden_recipe_used=False,
        )

    blocked_status = "blocked" if affordance.blocked_reasons else "not_blocked"
    if effect_status == EffectStatus.BLOCKED.value and blocked_status == "not_blocked":
        blocked_status = "blocked"

    from .station_falsifiers import evaluate_station_falsifiers

    draft = StationAffordanceProofRun(
        run_id=f"p14:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        station_ref=affordance.station_ref,
        public_station_basis=affordance,
        proximity_status=("proximate" if affordance.proximate else "not_proximate"),
        input_status=(
            "input_not_required"
            if not affordance.required_input_refs
            else "input_available"
            if not affordance.missing_input_refs
            else "missing_input"
        ),
        blocked_status=blocked_status,
        affordance_status=affordance.usable_status,
        station_use_candidate_status=attempt_status,
        ap01_publication_status=ap01_status,
        world_submission_status=world_submission_status,
        effect_status=effect_status,
        effect_refs=effect_refs,
        inventory_delta_refs=inventory_delta_refs,
        world_delta_refs=world_delta_refs,
        missing_input_refs=affordance.missing_input_refs,
        blocked_reasons=affordance.blocked_reasons,
        falsifier_results={},
        ablation_results=(),
        claim_safe_verdict="no_clear_advantage",
        protected_evaluator_only_rule_present=spec.evaluator_only_rule_present,
        mature_schema_created=False,
        hidden_recipe_used=False,
        action_request_emitted=False,
        cause_confirmed=False,
        fact_claimed=False,
        acp01_involved=False,
        acp01_candidate_status="not_involved",
        attempt_record=attempt_record,
    )
    falsifiers = evaluate_station_falsifiers(run=draft, claim_boundary=_CLAIM_BOUNDARY)
    run = StationAffordanceProofRun(
        run_id=draft.run_id,
        scenario_id=draft.scenario_id,
        station_ref=draft.station_ref,
        public_station_basis=draft.public_station_basis,
        proximity_status=draft.proximity_status,
        input_status=draft.input_status,
        blocked_status=draft.blocked_status,
        affordance_status=draft.affordance_status,
        station_use_candidate_status=draft.station_use_candidate_status,
        ap01_publication_status=draft.ap01_publication_status,
        world_submission_status=draft.world_submission_status,
        effect_status=draft.effect_status,
        effect_refs=draft.effect_refs,
        inventory_delta_refs=draft.inventory_delta_refs,
        world_delta_refs=draft.world_delta_refs,
        missing_input_refs=draft.missing_input_refs,
        blocked_reasons=draft.blocked_reasons,
        falsifier_results=falsifiers,
        ablation_results=(),
        claim_safe_verdict=("mora_station_affordance_advantage" if not any(falsifiers.values()) else "insufficient_evidence"),
        protected_evaluator_only_rule_present=draft.protected_evaluator_only_rule_present,
        mature_schema_created=draft.mature_schema_created,
        hidden_recipe_used=draft.hidden_recipe_used,
        action_request_emitted=draft.action_request_emitted,
        cause_confirmed=draft.cause_confirmed,
        fact_claimed=draft.fact_claimed,
        acp01_involved=draft.acp01_involved,
        acp01_candidate_status=draft.acp01_candidate_status,
        attempt_record=draft.attempt_record,
    )
    return run


def run_station_affordance_matrix() -> tuple[StationAffordanceProofRun, ...]:
    return tuple(run_station_affordance_case(item.scenario_id) for item in list_station_scenarios())


def run_station_affordance_ablations() -> tuple[StationAblationCheck, ...]:
    runs = {item.scenario_id: item for item in run_station_affordance_matrix()}
    checks: list[StationAblationCheck] = []

    checks.append(
        StationAblationCheck(
            ablation_id="remove_station_ref",
            scenario_id="station_missing_station_ref",
            expected_degradation=("no_station_use_attempt",),
            observed_behavior=(
                "no_station_use_attempt" if runs["station_missing_station_ref"].station_use_candidate_status != "published" else "published_without_station_ref",
            ),
        )
    )
    checks.append(
        StationAblationCheck(
            ablation_id="remove_proximity",
            scenario_id="station_far_with_input",
            expected_degradation=("blocked_or_not_proximate",),
            observed_behavior=(
                "blocked_or_not_proximate"
                if runs["station_far_with_input"].effect_status != "succeeded"
                else "unexpected_success",
            ),
        )
    )
    checks.append(
        StationAblationCheck(
            ablation_id="remove_input_refs",
            scenario_id="station_proximate_no_input",
            expected_degradation=("missing_input_preserved",),
            observed_behavior=(
                "missing_input_preserved"
                if runs["station_proximate_no_input"].input_status == "missing_input"
                else "missing_input_not_preserved",
            ),
        )
    )
    checks.append(
        StationAblationCheck(
            ablation_id="remove_action_surface",
            scenario_id="station_action_surface_only",
            expected_degradation=("no_valid_station_attempt",),
            observed_behavior=(
                "no_valid_station_attempt"
                if runs["station_action_surface_only"].station_use_candidate_status != "published"
                else "unexpected_published_attempt",
            ),
        )
    )
    checks.append(
        StationAblationCheck(
            ablation_id="hidden_eval_only_recipe",
            scenario_id="station_protected_eval_only_rule",
            expected_degradation=("no_subject_station_success",),
            observed_behavior=(
                "no_subject_station_success"
                if runs["station_protected_eval_only_rule"].effect_status != "succeeded"
                else "subject_station_success_from_eval_only",
            ),
        )
    )
    checks.append(
        StationAblationCheck(
            ablation_id="remove_ap01_ref",
            scenario_id="station_effect_without_ap01_attempt",
            expected_degradation=("not_subject_owned_success",),
            observed_behavior=(
                "not_subject_owned_success"
                if runs["station_effect_without_ap01_attempt"].ap01_publication_status != "published"
                else "subject_owned_success_claimed",
            ),
        )
    )
    checks.append(
        StationAblationCheck(
            ablation_id="remove_effect_ref",
            scenario_id="station_visible_not_usable",
            expected_degradation=("no_station_success_claim",),
            observed_behavior=(
                "no_station_success_claim"
                if not runs["station_visible_not_usable"].effect_refs
                else "effect_ref_present",
            ),
        )
    )
    checks.append(
        StationAblationCheck(
            ablation_id="blocked_station",
            scenario_id="station_blocked",
            expected_degradation=("blocked_outcome_preserved",),
            observed_behavior=(
                "blocked_outcome_preserved"
                if runs["station_blocked"].effect_status == "blocked"
                else "blocked_outcome_not_preserved",
            ),
        )
    )
    checks.append(
        StationAblationCheck(
            ablation_id="one_shot_success",
            scenario_id="station_use_effect_feedback",
            expected_degradation=("no_mature_schema",),
            observed_behavior=(
                "no_mature_schema"
                if not runs["station_use_effect_feedback"].mature_schema_created
                else "mature_schema_created",
            ),
        )
    )
    return tuple(checks)


def _build_backend(spec: StationScenarioSpec) -> GridWorldBackend:
    if spec.world_scenario_id in {"station_visible_no_input", "station_input_available_no_recipe_execution", "water_source_visible", "empty_room_presence"}:
        return GridWorldBackend(spec.world_scenario_id)

    config = _custom_scenario_config(spec.world_scenario_id)
    backend = GridWorldBackend("empty_room_presence")
    backend.reset(seed=None, scenario_config=config)
    return backend


def _custom_scenario_config(scenario_id: str) -> GridWorldScenarioConfig:
    if scenario_id == "p14_station_visible_far_no_input":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=8,
            height=8,
            subject_start=(1, 1),
            subject_orientation="east",
            stations=(("station:alpha", (6, 6), ("item:ore",), None),),
            visibility_range=20,
        )
    if scenario_id == "p14_station_far_with_input":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=8,
            height=8,
            subject_start=(1, 1),
            subject_orientation="east",
            stations=(("station:alpha", (6, 6), ("item:ore",), None),),
            initial_inventory=(("item:ore", 1),),
            visibility_range=20,
        )
    if scenario_id == "p14_station_blocked_with_input":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="east",
            stations=(("station:alpha", (3, 2), ("item:ore",), "station_temporarily_blocked"),),
            initial_inventory=(("item:ore", 1),),
        )
    if scenario_id == "p14_action_surface_and_input_no_station":
        return GridWorldScenarioConfig(
            scenario_id=scenario_id,
            width=5,
            height=5,
            subject_start=(2, 2),
            subject_orientation="south",
            water_sources=(("water:source:1", (2, 3)),),
            initial_inventory=(("item:ore", 1),),
        )
    raise ValueError(f"Unknown custom station scenario: {scenario_id}")


def _derive_station_affordance(*, spec: StationScenarioSpec, observation) -> StationAffordanceRecord:
    station_obj = None
    if spec.station_ref:
        station_obj = next((obj for obj in observation.visible_objects if obj.object_ref == spec.station_ref), None)
    else:
        station_obj = next((obj for obj in observation.visible_objects if str(getattr(obj.object_kind, "value", obj.object_kind)) == "station"), None)

    station_ref = station_obj.object_ref if station_obj is not None else None
    visible = station_obj is not None
    relation = str(station_obj.relation_to_subject) if station_obj is not None and station_obj.relation_to_subject else ""
    proximate = relation in {"same_cell", "adjacent"}
    reachable = proximate
    required_input_refs: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    if station_obj is not None:
        required_input_refs = tuple(station_obj.observable_properties.get("required_input_refs", ()))
        blocked_reason = station_obj.observable_properties.get("blocked_reason")
        if blocked_reason:
            blocked_reasons = (str(blocked_reason),)

    available_input_refs = tuple(
        item_ref
        for item_ref in required_input_refs
        if observation.inventory_state.item_counts.get(item_ref, 0) > 0
    )
    missing_input_refs = tuple(item_ref for item_ref in required_input_refs if item_ref not in available_input_refs)

    action_surface = next(
        (
            surface
            for surface in observation.action_space.available_surfaces
            if "use_station" in surface.action_kinds
        ),
        None,
    )
    action_surface_supports_use_station = action_surface is not None

    basis_refs = [f"observation:{observation.observation_id}"]
    if station_ref:
        basis_refs.append(f"station:{station_ref}")
    if action_surface is not None:
        basis_refs.append(f"surface:{action_surface.surface_ref}")
    if proximate and station_ref:
        basis_refs.append(f"capability:proximity:{station_ref}")
    if required_input_refs:
        basis_refs.extend(f"input_required:{item}" for item in required_input_refs)
    if available_input_refs:
        basis_refs.extend(f"input_available:{item}" for item in available_input_refs)

    if not visible:
        status = "not_visible"
    elif not action_surface_supports_use_station:
        status = "insufficient_public_basis"
    elif not proximate:
        status = "not_proximate"
    elif blocked_reasons:
        status = "blocked"
    elif missing_input_refs:
        status = "missing_input"
    else:
        status = "usable"

    return StationAffordanceRecord(
        station_ref=station_ref,
        visible=visible,
        reachable=reachable,
        proximate=proximate,
        required_input_refs=required_input_refs,
        available_input_refs=available_input_refs,
        missing_input_refs=missing_input_refs,
        blocked_reasons=blocked_reasons,
        usable_status=status,
        affordance_basis_refs=tuple(dict.fromkeys(basis_refs)),
        action_surface_supports_use_station=action_surface_supports_use_station,
        hidden_recipe_used=False,
        scenario_label_used=False,
    )


def _publish_use_station_request(*, scenario_id: str, observation_id: str, station_ref: str, input_refs: tuple[str, ...]):
    candidate = AP01ActionPublicationCandidate(
        candidate_id=f"p14:{scenario_id}:candidate:use_station",
        action_kind="use_station",
        target_ref=station_ref,
        args={"mode": "station_affordance_proof"},
        intended_effect=f"use_station:{station_ref}",
        source_tick_ref=f"subject_tick:{scenario_id}",
        source_cycle_ref=f"cycle:{scenario_id}",
        source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
        affordance_binding_refs=(f"A04:binding:{station_ref}",),
        permission_refs=("W04:permit",),
        evidence_refs=(
            f"observation:{observation_id}",
            f"station:{station_ref}",
            *tuple(f"input_available:{item}" for item in input_refs),
        ),
        episode_refs=(f"P02:episode:{scenario_id}",),
        residue_refs=(),
        revalidation_refs=(),
        blocked_claim_refs=(),
        desired_refs=(),
        predicted_refs=(),
        observed_refs=(f"station:{station_ref}",),
        permitted_refs=("W05:permitted",),
        candidate_origin=AP01CandidateOrigin.TEST_FIXTURE_CANDIDATE,
        forbidden_basis_markers=(),
        no_hidden_truth_used=True,
        no_eval_only_used=True,
        no_scenario_label_used=True,
    )
    return build_ap01_subject_action_publication(
        tick_id=f"p14:{scenario_id}",
        tick_index=1,
        candidate_set=AP01ActionPublicationCandidateSet(
            candidate_set_id=f"p14:{scenario_id}:set",
            candidates=(candidate,),
            source_lineage=("experiments.embodied_playground.station_affordance",),
        ),
        allow_test_fixture_candidates=True,
    )


def _request_to_envelope(*, request, scenario_id: str) -> PublishedActionEnvelope:
    return PublishedActionEnvelope(
        envelope_id=f"p14:{scenario_id}:envelope:{request.request_id}",
        subject_id="subject_a",
        ap01_request_ref=AP01RequestRef(request_ref=f"ap01_request:{request.request_id}"),
        action_kind=request.action_kind,
        target_ref=request.target_ref,
        args=dict(request.args),
        intended_effect=request.intended_effect,
        source_tick_ref=request.source_tick_ref,
        source_phase_refs=request.source_phase_refs,
        permission_refs=request.permission_refs,
        evidence_refs=request.evidence_refs,
        affordance_binding_refs=request.affordance_binding_refs,
    )


def _attempt_from_effect(
    *,
    scenario_id: str,
    station_ref: str,
    input_refs: tuple[str, ...],
    request_ref: str,
    effect: ActionEffectFrame,
) -> StationUseAttemptRecord:
    status = str(getattr(effect.effect_status, "value", effect.effect_status))
    if status == EffectStatus.SUCCEEDED.value:
        outcome = "succeeded"
    elif status == EffectStatus.BLOCKED.value:
        outcome = "blocked"
    elif status == EffectStatus.PARTIAL.value:
        outcome = "succeeded"
    else:
        outcome = "invalid"

    return StationUseAttemptRecord(
        attempt_id=f"p14:{scenario_id}:attempt:1",
        ap01_request_ref=request_ref,
        station_ref=station_ref,
        input_refs=input_refs,
        effect_ref=effect.effect_id,
        correlation_status=str(getattr(effect.correlation_status, "value", effect.correlation_status)),
        outcome=outcome,
        inventory_delta=dict(effect.inventory_delta),
        world_delta=dict(effect.world_delta_public),
        recipe_claimed=False,
        mature_schema_created=False,
        hidden_recipe_used=False,
    )


def _passive_station_effect_fixture(*, scenario_id: str) -> ActionEffectFrame:
    return ActionEffectFrame(
        effect_id=f"p14:{scenario_id}:passive_effect",
        subject_id="subject_a",
        tick_index=1,
        request_ref=None,
        envelope_ref=None,
        action_kind="use_station",
        target_ref="station:alpha",
        effect_status=EffectStatus.SUCCEEDED,
        body_delta={},
        inventory_delta={},
        world_delta_public={},
        observed_result_refs=("grid:external_station_effect",),
        correlation_status=CorrelationStatus.PASSIVE_WORLD_EVENT,
    )


def _delta_refs(effect_id: str, delta: dict[str, object]) -> tuple[str, ...]:
    refs: list[str] = []
    for key, value in delta.items():
        if isinstance(value, dict):
            for inner_key in value.keys():
                refs.append(f"{effect_id}:{key}:{inner_key}")
        elif isinstance(value, list):
            for inner_value in value:
                refs.append(f"{effect_id}:{key}:{inner_value}")
        else:
            refs.append(f"{effect_id}:{key}")
    return tuple(refs)
