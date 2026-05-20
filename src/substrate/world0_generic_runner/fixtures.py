from __future__ import annotations

from dataclasses import dataclass, replace

from substrate.ap01_subject_action_publication import (
    AP01ActionPublicationCandidate,
    AP01ActionPublicationCandidateSet,
    AP01CandidateOrigin,
    AP01ExecutionBoundary,
    AP01SubjectActionPublicationResult,
    AP01SubjectActionRequestPacket,
    AP01WorldExecutionStatus,
    build_ap01_subject_action_publication,
)
from substrate.umwelts_symbolic_contact import ContactSpec, generic_grid_fixture, symbolic_factory_fixture

from .models import (
    WorldAdapterCapability,
    WorldAdapterRuntime,
    WorldAdapterSpec,
    WorldBackendExecutionRequest,
    WorldBackendExecutionResult,
    WorldObservationPacket,
    WorldRunnerCycleInput,
    WorldRunnerConfig,
    WorldRunnerLoopInput,
)
from .policy import build_world_adapter_spec, build_world_observation_packet


@dataclass(slots=True)
class InMemoryWorldAdapter(WorldAdapterRuntime):
    adapter_id: str
    observation_by_cycle: dict[str, WorldObservationPacket]
    execution_by_request: dict[str, WorldBackendExecutionResult]
    default_execution: WorldBackendExecutionResult | None = None

    def observe(self, cycle_id: str) -> WorldObservationPacket:
        if cycle_id in self.observation_by_cycle:
            return self.observation_by_cycle[cycle_id]
        if self.observation_by_cycle:
            return next(iter(self.observation_by_cycle.values()))
        raise KeyError(f"missing observation for cycle {cycle_id}")

    def execute_ap01_envelope(self, request: WorldBackendExecutionRequest) -> WorldBackendExecutionResult:
        base = self.execution_by_request.get(request.ap01_request_ref, self.default_execution)
        if base is None:
            return _execution_result(
                execution_ref=f"exec:{request.execution_request_id}",
                request_ref=request.execution_request_id,
                ap01_request_ref=request.ap01_request_ref,
                adapter_id=self.adapter_id,
                effects=(),
                failed=True,
                blocked=True,
                residue=("residue:missing_execution_stub",),
            )
        next_ap01_ref = (
            base.ap01_request_ref
            if base.metadata.get("preserve_ap01_ref") == "true"
            else request.ap01_request_ref
        )
        return replace(
            base,
            execution_request_ref=request.execution_request_id,
            ap01_request_ref=next_ap01_ref,
            adapter_ref=self.adapter_id,
        )


@dataclass(frozen=True, slots=True)
class World0FixtureBundle:
    loop_input: WorldRunnerLoopInput
    adapter: InMemoryWorldAdapter
    description: str


def noop_world_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:noop", "symbolic_grid")
    obs = _base_observation("cycle:noop", spec.adapter_id, spec.contact_spec_ref)
    cycle = WorldRunnerCycleInput(cycle_id="cycle:noop", adapter_spec=spec, observation_packet=obs)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:noop": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:noop", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="public observation only, no AP01, execution skipped",
    )


def ap01_execution_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:ap01", "symbolic_grid")
    obs = _base_observation("cycle:ap01", spec.adapter_id, spec.contact_spec_ref, action_surfaces=("surface:inspect",))
    ap01_result = _ap01_result("cycle:ap01", request_id="ap01:req:cycle:ap01", action_kind="inspect")
    exec_result = _execution_result(
        execution_ref="backend_exec:ap01",
        request_ref="pending",
        ap01_request_ref="ap01:req:cycle:ap01",
        adapter_id=spec.adapter_id,
        effects=("effect:inspect:observed",),
    )
    cycle = WorldRunnerCycleInput(
        cycle_id="cycle:ap01",
        adapter_spec=spec,
        observation_packet=obs,
        external_ap01_result=ap01_result,
    )
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:ap01": obs}, {"ap01:req:cycle:ap01": exec_result})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:ap01", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="execution path uses only AP01-published request",
    )


def blocked_contact_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:blocked_contact", "symbolic_grid")
    obs = _base_observation(
        "cycle:blocked_contact",
        spec.adapter_id,
        spec.contact_spec_ref,
        source_refs=(),
    )
    cycle = WorldRunnerCycleInput(cycle_id="cycle:blocked_contact", adapter_spec=spec, observation_packet=obs)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:blocked_contact": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:blocked_contact", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="contact cannot be constructed, runner blocks execution",
    )


def passive_event_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:passive", "symbolic_grid")
    obs = _base_observation(
        "cycle:passive",
        spec.adapter_id,
        spec.contact_spec_ref,
        passive_events=("event:ambient_wind",),
    )
    cycle = WorldRunnerCycleInput(cycle_id="cycle:passive", adapter_spec=spec, observation_packet=obs)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:passive": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:passive", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="passive public event path with no cause proof",
    )


def failed_backend_execution_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:failed_exec", "symbolic_grid")
    obs = _base_observation("cycle:failed_exec", spec.adapter_id, spec.contact_spec_ref, action_surfaces=("surface:inspect",))
    ap01_result = _ap01_result("cycle:failed_exec", request_id="ap01:req:failed", action_kind="inspect")
    exec_result = _execution_result(
        execution_ref="backend_exec:failed",
        request_ref="pending",
        ap01_request_ref="ap01:req:failed",
        adapter_id=spec.adapter_id,
        effects=(),
        failed=True,
        blocked=False,
        residue=("residue:backend_failure",),
        uncertainty=("uncertain:backend_timeout",),
    )
    cycle = WorldRunnerCycleInput(
        cycle_id="cycle:failed_exec",
        adapter_spec=spec,
        observation_packet=obs,
        external_ap01_result=ap01_result,
    )
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:failed_exec": obs}, {"ap01:req:failed": exec_result})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:failed_exec", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="backend execution failure preserves residue",
    )


def adapter_action_selection_blocked_fixture() -> World0FixtureBundle:
    spec = replace(_base_spec("adapter:selected_action", "symbolic_grid"), adapter_can_select_action=True)
    obs = _base_observation("cycle:selected_action", spec.adapter_id, spec.contact_spec_ref)
    cycle = WorldRunnerCycleInput(cycle_id="cycle:selected_action", adapter_spec=spec, observation_packet=obs)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:selected_action": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:selected_action", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="adapter attempts selection and must be blocked",
    )


def contactspec_plan_blocked_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:contactspec_plan", "symbolic_factory")
    contact_spec = replace(symbolic_factory_fixture(), metadata={"ordered_plan": "factory_steps"})
    obs = _base_observation("cycle:contactspec_plan", spec.adapter_id, contact_spec.spec_id)
    cycle = WorldRunnerCycleInput(
        cycle_id="cycle:contactspec_plan",
        adapter_spec=spec,
        observation_packet=obs,
        contact_spec=contact_spec,
    )
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:contactspec_plan": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:contactspec_plan", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="contact spec plan payload must not drive runner",
    )


def backend_worldstate_blocked_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:worldstate", "symbolic_grid")
    obs = _base_observation(
        "cycle:worldstate",
        spec.adapter_id,
        spec.contact_spec_ref,
        metadata={"backend_worldstate": "raw_state:full_map"},
        no_backend_worldstate=False,
    )
    cycle = WorldRunnerCycleInput(cycle_id="cycle:worldstate", adapter_spec=spec, observation_packet=obs)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:worldstate": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:worldstate", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="backend worldstate payload is blocked on subject path",
    )


def scenario_label_blocked_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:scenario", "symbolic_grid")
    obs = _base_observation(
        "cycle:scenario",
        spec.adapter_id,
        spec.contact_spec_ref,
        metadata={"scenario_label": "eval:golden_path"},
    )
    cycle = WorldRunnerCycleInput(cycle_id="cycle:scenario", adapter_spec=spec, observation_packet=obs)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:scenario": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:scenario", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="scenario label cannot drive world cycle",
    )


def two_backend_grid_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:grid", "symbolic_grid")
    obs = _base_observation("cycle:grid", spec.adapter_id, spec.contact_spec_ref, observations=("obs:grid:cell_1_1",))
    cycle = WorldRunnerCycleInput(cycle_id="cycle:grid", adapter_spec=spec, observation_packet=obs)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:grid": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:grid", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="first backend family through generic runner",
    )


def two_backend_inventory_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:inventory", "symbolic_inventory")
    obs = _base_observation(
        "cycle:inventory",
        spec.adapter_id,
        spec.contact_spec_ref,
        observations=("obs:inventory:slot_full",),
        action_surfaces=("surface:store",),
    )
    cycle = WorldRunnerCycleInput(cycle_id="cycle:inventory", adapter_spec=spec, observation_packet=obs)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:inventory": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:inventory", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="second backend family through same runner contract",
    )


def factory_solution_blocked_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:factory_solution", "symbolic_factory")
    obs = _base_observation("cycle:factory_solution", spec.adapter_id, spec.contact_spec_ref)
    cycle = WorldRunnerCycleInput(
        cycle_id="cycle:factory_solution",
        adapter_spec=spec,
        observation_packet=obs,
        metadata_refs=("hardcoded_sequence:build_factory", "factory_steps:1,2,3"),
    )
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:factory_solution": obs}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:factory_solution", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="hardcoded factory solution sequence is rejected",
    )


def timeout_max_tick_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:timeout", "symbolic_grid")
    obs1 = _base_observation("cycle:timeout:1", spec.adapter_id, spec.contact_spec_ref)
    obs2 = _base_observation("cycle:timeout:2", spec.adapter_id, spec.contact_spec_ref)
    cycle1 = WorldRunnerCycleInput(cycle_id="cycle:timeout:1", adapter_spec=spec, observation_packet=obs1)
    cycle2 = WorldRunnerCycleInput(cycle_id="cycle:timeout:2", adapter_spec=spec, observation_packet=obs2)
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:timeout:1": obs1, "cycle:timeout:2": obs2}, {})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(
            run_id="run:timeout",
            adapter_spec=spec,
            cycle_inputs=(cycle1, cycle2),
            config=replace(_default_loop_config(), max_ticks=1),
        ),
        adapter=adapter,
        description="loop stop is explicit when max tick bound is reached",
    )


def replay_trace_fixture() -> World0FixtureBundle:
    return ap01_execution_fixture()


def no_ap01_no_execution_fixture() -> World0FixtureBundle:
    return noop_world_fixture()


def effect_without_correlation_blocked_fixture() -> World0FixtureBundle:
    spec = _base_spec("adapter:uncorrelated_effect", "symbolic_grid")
    obs = _base_observation("cycle:uncorrelated", spec.adapter_id, spec.contact_spec_ref, action_surfaces=("surface:inspect",))
    ap01_result = _ap01_result("cycle:uncorrelated", request_id="ap01:req:uncorrelated", action_kind="inspect")
    exec_result = _execution_result(
        execution_ref="backend_exec:uncorrelated",
        request_ref="pending",
        ap01_request_ref="ap01:req:uncorrelated",
        adapter_id=spec.adapter_id,
        effects=("effect:orphan",),
    )
    exec_result = replace(exec_result, ap01_request_ref="", passive_event=False, metadata={"preserve_ap01_ref": "true"})
    cycle = WorldRunnerCycleInput(
        cycle_id="cycle:uncorrelated",
        adapter_spec=spec,
        observation_packet=obs,
        external_ap01_result=ap01_result,
    )
    adapter = InMemoryWorldAdapter(spec.adapter_id, {"cycle:uncorrelated": obs}, {"ap01:req:uncorrelated": exec_result})
    return World0FixtureBundle(
        loop_input=WorldRunnerLoopInput(run_id="run:uncorrelated", adapter_spec=spec, cycle_inputs=(cycle,)),
        adapter=adapter,
        description="effect without request/passive marker must be blocked",
    )


def _base_spec(adapter_id: str, backend_family: str) -> WorldAdapterSpec:
    return build_world_adapter_spec(
        adapter_id=adapter_id,
        backend_family=backend_family,
        capabilities=(
            WorldAdapterCapability.OBSERVE,
            WorldAdapterCapability.EXECUTE_AP01_ENVELOPE,
            WorldAdapterCapability.PRODUCE_EFFECT_DELTA,
            WorldAdapterCapability.PUBLIC_STATUS,
        ),
        public_surface_refs=("surface:inspect", "surface:store", "surface:move_toward"),
        contact_spec_ref=f"spec:{backend_family}",
        source_refs=(f"source:{backend_family}:public",),
        allowed_action_kinds=("inspect", "store", "move_toward", "wait"),
    )


def _base_observation(
    cycle_id: str,
    adapter_id: str,
    contact_spec_ref: str,
    *,
    source_refs: tuple[str, ...] | None = None,
    observations: tuple[str, ...] = ("obs:entity:ore_node",),
    action_surfaces: tuple[str, ...] = (),
    public_effects: tuple[str, ...] = (),
    passive_events: tuple[str, ...] = (),
    metadata: dict[str, str] | None = None,
    no_backend_worldstate: bool = True,
) -> WorldObservationPacket:
    return build_world_observation_packet(
        observation_id=f"obs_packet:{cycle_id}",
        adapter_id=adapter_id,
        cycle_id=cycle_id,
        source_refs=source_refs if source_refs is not None else (f"source:{adapter_id}:public",),
        contact_spec_ref=contact_spec_ref,
        public_observation_refs=observations,
        public_effect_refs=public_effects,
        passive_public_event_refs=passive_events,
        action_surface_refs=action_surfaces,
        effect_surface_refs=(),
        residue_refs=("residue:observation",),
        uncertainty_refs=("uncertain:surface_partial",),
        lossiness_refs=("loss:sampled",),
        conflict_refs=(),
        metadata=metadata or {},
        no_backend_worldstate=no_backend_worldstate,
    )


def _candidate(cycle_id: str, action_kind: str) -> AP01ActionPublicationCandidate:
    return AP01ActionPublicationCandidate(
        candidate_id=f"candidate:{cycle_id}:{action_kind}",
        action_kind=action_kind,
        target_ref="target:public",
        args={"mode": "world0_test"},
        intended_effect="public_effect_expected",
        source_tick_ref=f"subject-tick:{cycle_id}",
        source_cycle_ref=cycle_id,
        source_phase_refs=("W04:permission:public", "W05:routing:public", "W06:revision:public"),
        affordance_binding_refs=("A04:binding:public",),
        permission_refs=("W04:permit:public",),
        evidence_refs=("W01:contact:public",),
        episode_refs=("P02:episode:public",),
        residue_refs=(),
        revalidation_refs=(),
        blocked_claim_refs=(),
        desired_refs=(),
        predicted_refs=(),
        observed_refs=(),
        permitted_refs=("W05:permitted:public",),
        candidate_origin=AP01CandidateOrigin.TEST_FIXTURE_CANDIDATE,
        forbidden_basis_markers=(),
        no_hidden_truth_used=True,
        no_eval_only_used=True,
        no_scenario_label_used=True,
    )


def _ap01_result(cycle_id: str, *, request_id: str, action_kind: str) -> AP01SubjectActionPublicationResult:
    result = build_ap01_subject_action_publication(
        tick_id=f"subject-tick:{cycle_id}",
        tick_index=1,
        candidate_set=AP01ActionPublicationCandidateSet(
            candidate_set_id=f"candidate_set:{cycle_id}",
            candidates=(_candidate(cycle_id, action_kind),),
            source_lineage=("world0.fixture.ap01",),
        ),
        allow_test_fixture_candidates=True,
    )
    req = result.published_requests[0]
    forced = AP01SubjectActionRequestPacket(
        request_id=request_id,
        source_candidate_id=req.source_candidate_id,
        action_kind=req.action_kind,
        target_ref=req.target_ref,
        args=req.args,
        intended_effect=req.intended_effect,
        source_tick_ref=req.source_tick_ref,
        source_phase_refs=req.source_phase_refs,
        affordance_binding_refs=req.affordance_binding_refs,
        permission_refs=req.permission_refs,
        evidence_refs=req.evidence_refs,
        episode_refs=req.episode_refs,
        execution_boundary=AP01ExecutionBoundary.EXTERNAL_WORLD_ONLY,
        executed_by_subject=False,
        world_execution_status=AP01WorldExecutionStatus.NOT_EXECUTED_BY_SUBJECT,
        must_wait_for_world_effect=True,
        effect_feedback_required=True,
        no_hidden_truth_used=req.no_hidden_truth_used,
        no_eval_only_used=req.no_eval_only_used,
        no_scenario_label_used=req.no_scenario_label_used,
        publication_confidence=req.publication_confidence,
        uncertainty_markers=req.uncertainty_markers,
        claim_boundary=req.claim_boundary,
    )
    return replace(result, published_requests=(forced,))


def _execution_result(
    *,
    execution_ref: str,
    request_ref: str,
    ap01_request_ref: str,
    adapter_id: str,
    effects: tuple[str, ...],
    failed: bool = False,
    blocked: bool = False,
    passive: bool = False,
    residue: tuple[str, ...] = ("residue:execution",),
    uncertainty: tuple[str, ...] = ("uncertain:execution",),
    lossiness: tuple[str, ...] = (),
    conflict: tuple[str, ...] = (),
) -> WorldBackendExecutionResult:
    return WorldBackendExecutionResult(
        backend_execution_ref=execution_ref,
        execution_request_ref=request_ref,
        ap01_request_ref=ap01_request_ref,
        adapter_ref=adapter_id,
        public_effect_refs=effects,
        residue_refs=residue,
        uncertainty_refs=uncertainty,
        lossiness_refs=lossiness,
        conflict_refs=conflict,
        failed=failed,
        blocked=blocked,
        passive_event=passive,
        source_refs=(f"source:{adapter_id}:execution",),
        metadata={},
        no_truth_claim=True,
        no_cause_claim=True,
    )


def _default_loop_config():
    return WorldRunnerConfig()
