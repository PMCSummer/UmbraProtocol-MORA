from __future__ import annotations

from dataclasses import asdict
from time import monotonic

from substrate.contact_projection_gate import ContactProjectionInput, project_contact_frame_to_subject_inputs
from substrate.subject_tick import SubjectTickInput, execute_subject_tick
from substrate.umwelt0_phenomenal_contact import (
    ActionSurfaceDeclaration,
    ContactBuildInput,
    ContactConformanceResult,
    LossinessMarker,
    SourceRef,
    UncertaintyMarker,
    ValidationStatus,
    build_phenomenal_contact_frame,
)
from substrate.umwelts_symbolic_contact import ContactSpec, UMWELTSValidationStatus, validate_contact_spec

from .models import (
    WorldAdapterRuntime,
    WorldAdapterSpec,
    WorldBackendExecutionRequest,
    WorldBackendExecutionResult,
    WorldEffectFeedback,
    WorldObservationPacket,
    WorldRunnerAuthorityFlags,
    WorldRunnerBlockReason,
    WorldRunnerConfig,
    WorldRunnerCounters,
    WorldRunnerCycleInput,
    WorldRunnerCycleResult,
    WorldRunnerCycleStatus,
    WorldRunnerCycleTrace,
    WorldRunnerExecutionStatus,
    WorldRunnerLoopInput,
    WorldRunnerLoopResult,
)

_PLAN_TOKENS: tuple[str, ...] = (
    "if_then_policy",
    "selected_action",
    "ordered_plan",
    "solution_sequence",
    "factory_steps",
    "route_plan",
    "recipe_oracle",
)
_FACTORY_TOKENS: tuple[str, ...] = (
    "build_factory",
    "automate_line",
    "complete_chain",
    "factory_solution",
    "hardcoded_sequence",
)
_SELECTION_TOKENS: tuple[str, ...] = (
    "selected_action",
    "selected_goal",
    "choose_candidate",
    "best_action",
    "cost_winner",
    "ranked_candidate",
    "selected_micro_operation",
)
_WORLDSTATE_TOKENS: tuple[str, ...] = (
    "worldstate",
    "raw_state",
    "full_map",
    "hidden_label",
    "true_recipe",
    "backend_object_id",
    "hidden_identity",
)
_SCENARIO_TOKENS: tuple[str, ...] = ("scenario_label", "eval_label", "scenario:")


def build_world_adapter_spec(
    *,
    adapter_id: str,
    backend_family: str,
    capabilities: tuple,
    public_surface_refs: tuple[str, ...],
    contact_spec_ref: str,
    source_refs: tuple[str, ...],
    allowed_action_kinds: tuple[str, ...],
    forbidden_payload_markers: tuple[str, ...] = (),
    metadata: dict[str, str] | None = None,
) -> WorldAdapterSpec:
    return WorldAdapterSpec(
        adapter_id=adapter_id,
        backend_family=backend_family,
        capabilities=capabilities,
        public_surface_refs=public_surface_refs,
        contact_spec_ref=contact_spec_ref,
        source_refs=source_refs,
        allowed_action_kinds=allowed_action_kinds,
        forbidden_payload_markers=forbidden_payload_markers,
        metadata=metadata or {},
    )


def validate_world_adapter_spec(spec: WorldAdapterSpec) -> tuple[WorldRunnerBlockReason, ...]:
    blocked: list[WorldRunnerBlockReason] = []
    if not spec.adapter_id or not spec.backend_family:
        blocked.append(WorldRunnerBlockReason.MISSING_ADAPTER_SPEC)
    joined = _joined(
        spec.adapter_id,
        spec.backend_family,
        *spec.public_surface_refs,
        *spec.allowed_action_kinds,
        *spec.forbidden_payload_markers,
        *spec.source_refs,
        *spec.metadata.keys(),
        *spec.metadata.values(),
    )
    if spec.adapter_can_select_action or spec.adapter_can_select_goal or _contains_any(joined, _SELECTION_TOKENS):
        blocked.append(WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT)
    if spec.exposes_worldstate_to_subject or _contains_any(joined, _WORLDSTATE_TOKENS):
        blocked.append(WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED)
    if spec.scenario_label_available or _contains_any(joined, _SCENARIO_TOKENS):
        blocked.append(WorldRunnerBlockReason.SCENARIO_LABEL_DECISION_DETECTED)
    if _contains_any(joined, _PLAN_TOKENS):
        blocked.append(WorldRunnerBlockReason.CONTACT_SPEC_PLAN_DETECTED)
    if _contains_any(joined, _FACTORY_TOKENS):
        blocked.append(WorldRunnerBlockReason.FACTORY_SOLUTION_DETECTED)
    return tuple(dict.fromkeys(blocked))


def build_world_observation_packet(
    *,
    observation_id: str,
    adapter_id: str,
    cycle_id: str,
    source_refs: tuple[str, ...],
    contact_spec_ref: str,
    public_observation_refs: tuple[str, ...] = (),
    public_effect_refs: tuple[str, ...] = (),
    passive_public_event_refs: tuple[str, ...] = (),
    action_surface_refs: tuple[str, ...] = (),
    effect_surface_refs: tuple[str, ...] = (),
    residue_refs: tuple[str, ...] = (),
    uncertainty_refs: tuple[str, ...] = (),
    lossiness_refs: tuple[str, ...] = (),
    conflict_refs: tuple[str, ...] = (),
    metadata: dict[str, str] | None = None,
    no_backend_worldstate: bool = True,
) -> WorldObservationPacket:
    return WorldObservationPacket(
        observation_id=observation_id,
        adapter_id=adapter_id,
        cycle_id=cycle_id,
        public_observation_refs=public_observation_refs,
        public_effect_refs=public_effect_refs,
        passive_public_event_refs=passive_public_event_refs,
        action_surface_refs=action_surface_refs,
        effect_surface_refs=effect_surface_refs,
        residue_refs=residue_refs,
        uncertainty_refs=uncertainty_refs,
        lossiness_refs=lossiness_refs,
        conflict_refs=conflict_refs,
        source_refs=source_refs,
        contact_spec_ref=contact_spec_ref,
        metadata=metadata or {},
        no_backend_worldstate=no_backend_worldstate,
    )


def validate_world_observation_packet(
    packet: WorldObservationPacket,
    config: WorldRunnerConfig,
) -> tuple[WorldRunnerBlockReason, ...]:
    blocked: list[WorldRunnerBlockReason] = []
    joined = _joined(*packet.metadata.keys(), *packet.metadata.values(), *packet.source_refs)
    if not packet.source_refs:
        blocked.append(WorldRunnerBlockReason.CONTACT_BLOCKED)
    if (not packet.no_backend_worldstate or _contains_any(joined, _WORLDSTATE_TOKENS)) and config.fail_on_backend_worldstate:
        blocked.append(WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED)
    if _contains_any(joined, _SCENARIO_TOKENS) and config.fail_on_scenario_label:
        blocked.append(WorldRunnerBlockReason.SCENARIO_LABEL_DECISION_DETECTED)
    if _contains_any(joined, _PLAN_TOKENS):
        blocked.append(WorldRunnerBlockReason.CONTACT_SPEC_PLAN_DETECTED)
    if _contains_any(joined, _FACTORY_TOKENS):
        blocked.append(WorldRunnerBlockReason.FACTORY_SOLUTION_DETECTED)
    return tuple(dict.fromkeys(blocked))


def construct_world_contact(
    cycle_input: WorldRunnerCycleInput,
    observation: WorldObservationPacket,
) -> tuple[ContactConformanceResult | None, tuple[WorldRunnerBlockReason, ...], tuple[str, ...]]:
    blocked: list[WorldRunnerBlockReason] = []
    trace: list[str] = ["world0:construct_contact:start"]

    if cycle_input.contact_spec is not None:
        spec_result = validate_contact_spec(cycle_input.contact_spec)
        trace.append(f"world0:contact_spec:{spec_result.status.value}")
        if spec_result.status in {UMWELTSValidationStatus.BLOCKED, UMWELTSValidationStatus.REJECTED}:
            blocked.append(WorldRunnerBlockReason.INVALID_CONTACT_SPEC)
        if not validate_no_contactspec_plan_execution(cycle_input.contact_spec):
            blocked.append(WorldRunnerBlockReason.CONTACT_SPEC_PLAN_DETECTED)

    if blocked:
        return None, tuple(dict.fromkeys(blocked)), tuple(trace)

    source_objs = tuple(
        SourceRef(
            source_id=ref,
            source_kind="world0_adapter_public",
            public=True,
            protected_eval=("eval" in ref.lower()),
            scenario_label=("scenario" in ref.lower()),
            provider_ref=observation.adapter_id,
        )
        for ref in observation.source_refs
    )
    action_surfaces = tuple(
        ActionSurfaceDeclaration(
            surface_ref=ref,
            action_kind=_action_kind_from_ref(ref),
            source_refs=tuple(item.source_id for item in source_objs),
        )
        for ref in observation.action_surface_refs
    )

    contact_input = ContactBuildInput(
        frame_id=f"world0:{cycle_input.cycle_id}:contact",
        tick_id=cycle_input.cycle_id,
        provider_refs=(observation.adapter_id,),
        public_observation_refs=observation.public_observation_refs,
        public_effect_refs=observation.public_effect_refs,
        passive_event_refs=observation.passive_public_event_refs,
        action_surfaces=action_surfaces,
        effect_frames=(),
        residue_refs=observation.residue_refs,
        uncertainty_refs=observation.uncertainty_refs,
        conflict_refs=observation.conflict_refs,
        source_refs=source_objs,
        lossiness_markers=tuple(
            LossinessMarker(marker_id=item, kind="lossy_public", description="world0_observation_lossy")
            for item in observation.lossiness_refs
        ),
        uncertainty_markers=tuple(
            UncertaintyMarker(marker_id=item, kind="uncertain_public", description="world0_observation_uncertain")
            for item in observation.uncertainty_refs
        ),
        worldstate_payload_present=(not observation.no_backend_worldstate)
        or _contains_any(_joined(*observation.metadata.values()), _WORLDSTATE_TOKENS),
        scenario_label_present=_contains_any(_joined(*observation.metadata.values(), *observation.source_refs), _SCENARIO_TOKENS),
        protected_eval_present=_contains_any(_joined(*observation.metadata.values()), ("eval", "protected_eval")),
        backend_specific_fields=tuple(
            value for value in (*observation.metadata.keys(), *observation.metadata.values()) if "backend_object_id" in value.lower()
        ),
    )
    result = build_phenomenal_contact_frame(contact_input)
    trace.append(f"world0:contact_status:{result.phenomenal_contact_frame.validation_status.value}")
    if result.phenomenal_contact_frame.validation_status in {ValidationStatus.BLOCKED, ValidationStatus.REJECTED}:
        blocked.append(WorldRunnerBlockReason.CONTACT_BLOCKED)
    return result, tuple(dict.fromkeys(blocked)), tuple(trace)


def project_world_contact(cycle_id: str, contact_result: ContactConformanceResult):
    return project_contact_frame_to_subject_inputs(
        ContactProjectionInput(
            projection_id=f"world0:{cycle_id}:projection",
            contact_result=contact_result,
        )
    )


def collect_ap01_requests_from_tick_result(
    tick_result,
    external_ap01_result=None,
    external_requests: tuple = (),
) -> tuple:
    requests: list = []
    if tick_result is not None:
        requests.extend(tick_result.ap01_result.published_requests)
    if external_ap01_result is not None:
        requests.extend(external_ap01_result.published_requests)
    requests.extend(external_requests)
    by_id = {}
    for item in requests:
        by_id[item.request_id] = item
    return tuple(by_id.values())


def build_backend_execution_request(
    *,
    cycle_id: str,
    adapter_spec: WorldAdapterSpec,
    ap01_request,
) -> WorldBackendExecutionRequest:
    return WorldBackendExecutionRequest(
        execution_request_id=f"world0:{cycle_id}:exec_req:{ap01_request.request_id}",
        cycle_id=cycle_id,
        ap01_request_ref=ap01_request.request_id,
        adapter_ref=adapter_spec.adapter_id,
        action_kind_ref=ap01_request.action_kind,
        source_refs=tuple(ap01_request.source_phase_refs),
        provenance_refs=tuple(dict.fromkeys((*ap01_request.source_phase_refs, ap01_request.source_tick_ref))),
        created_by_runner=False,
        created_from_ap01=True,
        runner_selected_action=False,
        metadata={"source": "ap01_published_request"},
    )


def execute_backend_from_ap01(
    *,
    adapter: WorldAdapterRuntime,
    request: WorldBackendExecutionRequest,
) -> WorldBackendExecutionResult:
    return adapter.execute_ap01_envelope(request)


def build_world_effect_feedback(
    *,
    cycle_id: str,
    result: WorldBackendExecutionResult,
) -> WorldEffectFeedback:
    passive_marker = f"passive:{result.backend_execution_ref}" if result.passive_event else None
    request_ref = None if result.passive_event else result.ap01_request_ref
    if request_ref is not None:
        correlation_status = "request_correlated"
    elif passive_marker is not None:
        correlation_status = "passive_event"
    else:
        correlation_status = "uncorrelated"
    return WorldEffectFeedback(
        feedback_id=f"world0:{cycle_id}:feedback:{result.backend_execution_ref}",
        cycle_id=cycle_id,
        request_ref=request_ref,
        passive_event_ref=passive_marker,
        backend_execution_ref=result.backend_execution_ref,
        public_effect_refs=result.public_effect_refs,
        residue_refs=result.residue_refs,
        uncertainty_refs=result.uncertainty_refs,
        lossiness_refs=result.lossiness_refs,
        conflict_refs=result.conflict_refs,
        correlation_status=correlation_status,
        effect_frame_ref=f"world_effect:{result.backend_execution_ref}",
        no_fact_claim=True,
        no_cause_confirmed=True,
    )


def validate_effect_correlation(feedback: WorldEffectFeedback) -> bool:
    return bool(feedback.request_ref or feedback.passive_event_ref)


def validate_runner_does_not_select_action(cycle_input: WorldRunnerCycleInput) -> bool:
    return not _contains_any(_joined(*cycle_input.metadata_refs), _SELECTION_TOKENS)


def validate_runner_does_not_create_ap01(cycle_input: WorldRunnerCycleInput) -> bool:
    return not cycle_input.runner_created_ap01_refs


def validate_no_execution_without_ap01(
    *,
    ap01_requests: tuple,
    execution_attempt: bool,
) -> bool:
    return bool(ap01_requests) or not execution_attempt


def validate_no_backend_worldstate_to_subject(observation: WorldObservationPacket) -> bool:
    joined = _joined(*observation.metadata.keys(), *observation.metadata.values())
    return observation.no_backend_worldstate and not _contains_any(joined, _WORLDSTATE_TOKENS)


def validate_no_scenario_label_decision(observation: WorldObservationPacket) -> bool:
    return not _contains_any(_joined(*observation.metadata.keys(), *observation.metadata.values(), *observation.source_refs), _SCENARIO_TOKENS)


def validate_no_contactspec_plan_execution(spec: ContactSpec) -> bool:
    joined = _joined(
        spec.spec_id,
        spec.backend_family,
        *spec.metadata.keys(),
        *spec.metadata.values(),
        *(item.action_kind for item in spec.action_surface_declarations),
        *(item.effect_kind for item in spec.effect_surface_declarations),
    )
    return not _contains_any(joined, _PLAN_TOKENS)


def validate_no_factory_solution(values: tuple[str, ...]) -> bool:
    return not _contains_any(_joined(*values), _FACTORY_TOKENS)


def validate_failure_preserves_residue(result: WorldBackendExecutionResult) -> bool:
    if result.failed or result.blocked:
        return bool(result.residue_refs)
    return True


def validate_blocked_cycle_visible(trace: WorldRunnerCycleTrace) -> bool:
    if trace.cycle_status is WorldRunnerCycleStatus.BLOCKED:
        return bool(trace.blocked_reasons)
    return True


def validate_cycle_trace(trace: WorldRunnerCycleTrace) -> bool:
    if trace.cycle_status is WorldRunnerCycleStatus.COMPLETED:
        return bool(trace.subject_tick_ref)
    return True


def build_cycle_trace(
    *,
    cycle_id: str,
    adapter_spec: WorldAdapterSpec,
    contact_spec_ref: str,
    observation_packet_ref: str | None,
    contact_frame_refs: tuple[str, ...],
    projection_refs: tuple[str, ...],
    subject_tick_ref: str | None,
    ap01_request_refs: tuple[str, ...],
    backend_execution_refs: tuple[str, ...],
    world_effect_frame_refs: tuple[str, ...],
    residue_refs: tuple[str, ...],
    uncertainty_refs: tuple[str, ...],
    blocked_reasons: tuple[WorldRunnerBlockReason, ...],
    cycle_status: WorldRunnerCycleStatus,
    execution_status: WorldRunnerExecutionStatus,
) -> WorldRunnerCycleTrace:
    return WorldRunnerCycleTrace(
        cycle_id=cycle_id,
        adapter_ref=adapter_spec.adapter_id,
        contact_spec_ref=contact_spec_ref,
        observation_packet_ref=observation_packet_ref,
        contact_frame_refs=contact_frame_refs,
        projection_refs=projection_refs,
        subject_tick_ref=subject_tick_ref,
        ap01_request_refs=ap01_request_refs,
        backend_execution_refs=backend_execution_refs,
        world_effect_frame_refs=world_effect_frame_refs,
        residue_refs=residue_refs,
        uncertainty_refs=uncertainty_refs,
        blocked_reasons=blocked_reasons,
        cycle_status=cycle_status,
        execution_status=execution_status,
        no_runner_action_selection=True,
        no_runner_ap01_creation=True,
        no_backend_worldstate_to_subject=True,
        no_factory_solution=True,
    )


def run_world_cycle(
    cycle_input: WorldRunnerCycleInput,
    *,
    adapter: WorldAdapterRuntime,
    config: WorldRunnerConfig,
) -> WorldRunnerCycleResult:
    blocked: list[WorldRunnerBlockReason] = []
    counters = WorldRunnerCounters(cycle_count=1)
    contact_result = None
    projection_result = None
    tick_result = None
    backend_requests: list[WorldBackendExecutionRequest] = []
    backend_results: list[WorldBackendExecutionResult] = []
    feedback_refs: list[WorldEffectFeedback] = []

    adapter_issues = validate_world_adapter_spec(cycle_input.adapter_spec)
    blocked.extend(adapter_issues)
    if WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT in adapter_issues:
        counters = _with_count(counters, "adapter_action_selection_block_count", 1)
    if WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED in adapter_issues:
        counters = _with_count(counters, "backend_worldstate_block_count", 1)
    if WorldRunnerBlockReason.SCENARIO_LABEL_DECISION_DETECTED in adapter_issues:
        counters = _with_count(counters, "scenario_label_block_count", 1)
    if WorldRunnerBlockReason.CONTACT_SPEC_PLAN_DETECTED in adapter_issues:
        counters = _with_count(counters, "contact_spec_plan_block_count", 1)
    if WorldRunnerBlockReason.FACTORY_SOLUTION_DETECTED in adapter_issues:
        counters = _with_count(counters, "factory_solution_block_count", 1)

    if not validate_runner_does_not_select_action(cycle_input):
        blocked.append(WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT)
        counters = _with_count(counters, "adapter_action_selection_block_count", 1)
    if not validate_runner_does_not_create_ap01(cycle_input):
        blocked.append(WorldRunnerBlockReason.RUNNER_AP01_CREATION_ATTEMPT)
        counters = _with_count(counters, "runner_ap01_creation_block_count", 1)
    if not validate_no_factory_solution(cycle_input.metadata_refs):
        blocked.append(WorldRunnerBlockReason.FACTORY_SOLUTION_DETECTED)
        counters = _with_count(counters, "factory_solution_block_count", 1)

    observation = cycle_input.observation_packet or adapter.observe(cycle_input.cycle_id)
    packet_issues = validate_world_observation_packet(observation, config)
    blocked.extend(packet_issues)
    if WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED in packet_issues:
        counters = _with_count(counters, "backend_worldstate_block_count", 1)
    if WorldRunnerBlockReason.SCENARIO_LABEL_DECISION_DETECTED in packet_issues:
        counters = _with_count(counters, "scenario_label_block_count", 1)
    if WorldRunnerBlockReason.CONTACT_SPEC_PLAN_DETECTED in packet_issues:
        counters = _with_count(counters, "contact_spec_plan_block_count", 1)
    if WorldRunnerBlockReason.FACTORY_SOLUTION_DETECTED in packet_issues:
        counters = _with_count(counters, "factory_solution_block_count", 1)

    if validate_no_backend_worldstate_to_subject(observation) is False:
        blocked.append(WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED)
        counters = _with_count(counters, "backend_worldstate_block_count", 1)
    if validate_no_scenario_label_decision(observation) is False and config.fail_on_scenario_label:
        blocked.append(WorldRunnerBlockReason.SCENARIO_LABEL_DECISION_DETECTED)
        counters = _with_count(counters, "scenario_label_block_count", 1)

    if not blocked:
        contact_result, contact_blocked, _ = construct_world_contact(cycle_input, observation)
        blocked.extend(contact_blocked)
        if contact_blocked:
            counters = _with_count(counters, "contact_blocked_count", 1)

    if not blocked and contact_result is not None:
        projection_result = project_world_contact(cycle_input.cycle_id, contact_result)
        if projection_result.projection_status == "blocked":
            blocked.append(WorldRunnerBlockReason.PROJECTION_BLOCKED)
            counters = _with_count(counters, "projection_blocked_count", 1)

    if not blocked and projection_result is not None and not cycle_input.skip_subject_tick:
        tick_input = cycle_input.subject_tick_input or SubjectTickInput(
            case_id=f"world0:{cycle_input.cycle_id}",
            energy=0.5,
            cognitive=0.5,
            safety=0.6,
        )
        try:
            tick_result = execute_subject_tick(tick_input)
        except Exception:
            blocked.append(WorldRunnerBlockReason.SUBJECT_TICK_FAILED)
            counters = _with_count(counters, "subject_tick_failed_count", 1)
    elif not blocked and cycle_input.skip_subject_tick:
        blocked.append(WorldRunnerBlockReason.SUBJECT_TICK_FAILED)
        counters = _with_count(counters, "subject_tick_failed_count", 1)

    if cycle_input.external_ap01_requests:
        blocked.append(WorldRunnerBlockReason.RUNNER_AP01_CREATION_ATTEMPT)
        counters = _with_count(counters, "runner_ap01_creation_block_count", 1)

    ap01_requests = collect_ap01_requests_from_tick_result(
        tick_result,
        external_ap01_result=cycle_input.external_ap01_result,
        external_requests=(),
    )
    counters = _with_count(counters, "ap01_request_count", len(ap01_requests))

    if cycle_input.execution_without_ap01_attempt and not validate_no_execution_without_ap01(ap01_requests=ap01_requests, execution_attempt=True):
        blocked.append(WorldRunnerBlockReason.EXECUTION_WITHOUT_AP01)
        counters = _with_count(counters, "execution_without_ap01_block_count", 1)

    execution_status = WorldRunnerExecutionStatus.NOT_REQUESTED
    if ap01_requests and not blocked:
        for req in ap01_requests:
            backend_req = build_backend_execution_request(cycle_id=cycle_input.cycle_id, adapter_spec=cycle_input.adapter_spec, ap01_request=req)
            backend_requests.append(backend_req)
            backend_res = execute_backend_from_ap01(adapter=adapter, request=backend_req)
            backend_results.append(backend_res)
            feedback = build_world_effect_feedback(cycle_id=cycle_input.cycle_id, result=backend_res)
            feedback_refs.append(feedback)
            if not validate_effect_correlation(feedback):
                blocked.append(WorldRunnerBlockReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER)
            if not validate_failure_preserves_residue(backend_res):
                blocked.append(WorldRunnerBlockReason.RESIDUE_MISSING_AFTER_FAILURE)
            if backend_res.passive_event:
                counters = _with_count(counters, "passive_event_count", 1)
        counters = _with_count(counters, "backend_execution_count", len(backend_results))
        counters = _with_count(counters, "effect_frame_count", len(feedback_refs))
        execution_status = WorldRunnerExecutionStatus.EXECUTED_FROM_AP01
    elif ap01_requests and blocked:
        execution_status = WorldRunnerExecutionStatus.BLOCKED
    else:
        counters = _with_count(counters, "skipped_no_ap01_count", 1)
        execution_status = (
            WorldRunnerExecutionStatus.PASSIVE_EVENT_ONLY
            if observation.passive_public_event_refs and config.allow_passive_events
            else WorldRunnerExecutionStatus.SKIPPED_NO_AP01
        )
        blocked.append(WorldRunnerBlockReason.NO_AP01_REQUEST)

    residue_refs = tuple(
        dict.fromkeys(
            (
                *observation.residue_refs,
                *(contact_result.phenomenal_contact_frame.residue_refs if contact_result else ()),
                *(projection_result.projected_ab_input.residue_refs if projection_result else ()),
                *(ref for item in backend_results for ref in item.residue_refs),
                *(ref for item in feedback_refs for ref in item.residue_refs),
            )
        )
    )
    uncertainty_refs = tuple(
        dict.fromkeys(
            (
                *observation.uncertainty_refs,
                *(contact_result.phenomenal_contact_frame.uncertainty_refs if contact_result else ()),
                *(projection_result.projected_ab_input.uncertainty_refs if projection_result else ()),
                *(ref for item in backend_results for ref in item.uncertainty_refs),
            )
        )
    )
    counters = _with_count(counters, "residue_count", len(residue_refs))
    counters = _with_count(counters, "uncertainty_count", len(uncertainty_refs))

    blocked = list(dict.fromkeys(blocked))
    if blocked and any(item in blocked for item in (WorldRunnerBlockReason.SUBJECT_TICK_FAILED, WorldRunnerBlockReason.RESIDUE_MISSING_AFTER_FAILURE)):
        cycle_status = WorldRunnerCycleStatus.FAILED
    elif blocked and WorldRunnerBlockReason.NO_AP01_REQUEST in blocked and len(blocked) == 1 and config.allow_noop_cycles:
        cycle_status = WorldRunnerCycleStatus.NOOP
    elif blocked:
        cycle_status = WorldRunnerCycleStatus.BLOCKED
    elif execution_status in {WorldRunnerExecutionStatus.SKIPPED_NO_AP01, WorldRunnerExecutionStatus.PASSIVE_EVENT_ONLY}:
        cycle_status = WorldRunnerCycleStatus.NOOP
    elif any(item.failed for item in backend_results):
        cycle_status = WorldRunnerCycleStatus.FAILED
    elif any(item.blocked for item in backend_results):
        cycle_status = WorldRunnerCycleStatus.PARTIAL
    else:
        cycle_status = WorldRunnerCycleStatus.COMPLETED

    if cycle_status is WorldRunnerCycleStatus.COMPLETED:
        counters = _with_count(counters, "completed_count", 1)
    elif cycle_status is WorldRunnerCycleStatus.NOOP:
        counters = _with_count(counters, "noop_count", 1)
    elif cycle_status is WorldRunnerCycleStatus.BLOCKED:
        counters = _with_count(counters, "blocked_count", 1)
    elif cycle_status is WorldRunnerCycleStatus.FAILED:
        counters = _with_count(counters, "failed_count", 1)

    trace = build_cycle_trace(
        cycle_id=cycle_input.cycle_id,
        adapter_spec=cycle_input.adapter_spec,
        contact_spec_ref=observation.contact_spec_ref,
        observation_packet_ref=observation.observation_id,
        contact_frame_refs=(contact_result.phenomenal_contact_frame.frame_id, contact_result.world_contact_frame.frame_id) if contact_result else (),
        projection_refs=(projection_result.projection_id,) if projection_result else (),
        subject_tick_ref=(tick_result.state.tick_id if tick_result is not None else None),
        ap01_request_refs=tuple(item.request_id for item in ap01_requests),
        backend_execution_refs=tuple(item.backend_execution_ref for item in backend_results),
        world_effect_frame_refs=tuple(item.effect_frame_ref for item in feedback_refs if item.effect_frame_ref),
        residue_refs=residue_refs,
        uncertainty_refs=uncertainty_refs,
        blocked_reasons=tuple(blocked),
        cycle_status=cycle_status,
        execution_status=execution_status,
    )
    if not validate_cycle_trace(trace):
        blocked.append(WorldRunnerBlockReason.SUBJECT_TICK_FAILED)
    if not validate_blocked_cycle_visible(trace):
        blocked.append(WorldRunnerBlockReason.CONTACT_BLOCKED)

    return WorldRunnerCycleResult(
        cycle_trace=trace,
        cycle_status=cycle_status,
        execution_status=execution_status,
        contact_result=contact_result,
        projection_result=projection_result,
        subject_tick_result=tick_result,
        ap01_requests=ap01_requests,
        backend_requests=tuple(backend_requests),
        backend_results=tuple(backend_results),
        effect_feedback=tuple(feedback_refs),
        blocked_reasons=tuple(dict.fromkeys(blocked)),
        residue_refs=residue_refs,
        uncertainty_refs=uncertainty_refs,
        counters=counters,
        authority_flags=WorldRunnerAuthorityFlags(),
    )


def run_world_loop(
    loop_input: WorldRunnerLoopInput,
    *,
    adapter: WorldAdapterRuntime,
) -> WorldRunnerLoopResult:
    started = monotonic()
    traces: list[WorldRunnerCycleTrace] = []
    blocked: list[WorldRunnerBlockReason] = []
    residue: list[str] = []
    uncertainty: list[str] = []
    counter_dict = asdict(WorldRunnerCounters())
    final_status = WorldRunnerCycleStatus.NOOP

    limit = min(len(loop_input.cycle_inputs), loop_input.config.max_ticks)
    if len(loop_input.cycle_inputs) > loop_input.config.max_ticks:
        blocked.append(WorldRunnerBlockReason.MAX_TICKS_REACHED)
        counter_dict["max_tick_stop_count"] += 1

    for cycle in loop_input.cycle_inputs[:limit]:
        if loop_input.config.timeout_seconds is not None and (monotonic() - started) > loop_input.config.timeout_seconds:
            blocked.append(WorldRunnerBlockReason.TIMEOUT_REACHED)
            counter_dict["timeout_count"] += 1
            final_status = WorldRunnerCycleStatus.TIMEOUT
            break
        cycle_result = run_world_cycle(cycle, adapter=adapter, config=loop_input.config)
        traces.append(cycle_result.cycle_trace)
        residue.extend(cycle_result.residue_refs)
        uncertainty.extend(cycle_result.uncertainty_refs)
        final_status = cycle_result.cycle_status
        _merge_counter_dict(counter_dict, asdict(cycle_result.counters))
        blocked.extend(cycle_result.blocked_reasons)

    blocked = list(dict.fromkeys(blocked))
    if WorldRunnerBlockReason.TIMEOUT_REACHED in blocked:
        final_status = WorldRunnerCycleStatus.TIMEOUT
    elif WorldRunnerBlockReason.MAX_TICKS_REACHED in blocked and final_status is WorldRunnerCycleStatus.NOOP:
        final_status = WorldRunnerCycleStatus.HALTED

    replay_ref = f"world0:replay:{loop_input.run_id}" if loop_input.config.replay_enabled else None
    return WorldRunnerLoopResult(
        run_id=loop_input.run_id,
        cycle_traces=tuple(traces),
        final_status=final_status,
        counters=WorldRunnerCounters(**counter_dict),
        replay_trace_ref=replay_ref,
        residue_refs=tuple(dict.fromkeys(residue)),
        uncertainty_refs=tuple(dict.fromkeys(uncertainty)),
        blocked_reasons=tuple(blocked),
        no_action_selected_by_runner=True,
        no_ap01_created_by_runner=True,
        no_world_submission_without_ap01=True,
        fact_claimed=False,
        cause_confirmed=False,
        value_assigned=False,
        recipe_matured=False,
        skill_matured=False,
        automation_claimed=False,
        factory_solution_hardcoded=False,
    )


def summarize_runner_conformance(result: WorldRunnerLoopResult) -> dict[str, object]:
    return {
        "run_id": result.run_id,
        "final_status": result.final_status.value,
        "cycle_count": len(result.cycle_traces),
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "counters": asdict(result.counters),
        "authority_flags": asdict(WorldRunnerAuthorityFlags()),
        "no_action_selected_by_runner": result.no_action_selected_by_runner,
        "no_ap01_created_by_runner": result.no_ap01_created_by_runner,
        "no_world_submission_without_ap01": result.no_world_submission_without_ap01,
        "fact_claimed": result.fact_claimed,
        "cause_confirmed": result.cause_confirmed,
        "value_assigned": result.value_assigned,
        "recipe_matured": result.recipe_matured,
        "skill_matured": result.skill_matured,
        "automation_claimed": result.automation_claimed,
    }


def _action_kind_from_ref(surface_ref: str) -> str:
    if ":" in surface_ref:
        return surface_ref.split(":")[-1]
    return surface_ref


def _joined(*values: object) -> str:
    parts: list[str] = []
    for value in values:
        parts.extend(_flatten_text_tokens(value))
    return " ".join(parts).lower()


def _contains_any(haystack: str, tokens: tuple[str, ...]) -> bool:
    return any(token in haystack for token in tokens)


def _flatten_text_tokens(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        parts: list[str] = []
        for key, nested in value.items():
            parts.extend(_flatten_text_tokens(key))
            parts.extend(_flatten_text_tokens(nested))
        return tuple(parts)
    if isinstance(value, (tuple, list, set, frozenset)):
        parts: list[str] = []
        for item in value:
            parts.extend(_flatten_text_tokens(item))
        return tuple(parts)
    return (str(value),)


def _with_count(counters: WorldRunnerCounters, key: str, amount: int) -> WorldRunnerCounters:
    payload = asdict(counters)
    payload[key] += amount
    return WorldRunnerCounters(**payload)


def _merge_counter_dict(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        if key in target:
            target[key] += value
