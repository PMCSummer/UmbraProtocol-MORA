from __future__ import annotations

from dataclasses import dataclass

from substrate.world0_generic_runner import (
    WorldRunnerCycleResult,
    ap01_execution_fixture,
    blocked_contact_fixture,
    failed_backend_execution_fixture,
    no_ap01_no_execution_fixture,
    run_world_cycle,
)

from .models import P17BFactoryNeed, P17BRunStatus, P17BStepInput, P17BStepKind
from .policy import build_p17b_factory_need, build_p17b_live_run, build_p17b_step_spec


@dataclass(frozen=True, slots=True)
class P17BFixtureBundle:
    case_id: str
    expected_status: P17BRunStatus
    run: object
    description: str


def successful_bounded_chain_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    steps = (
        _step_input(
            step_id="step:1:gather",
            step_kind=P17BStepKind.GATHER_RESOURCE,
            required_inputs=("resource:ore",),
            required_stations=(),
            expected_outputs=("intermediate:ore_chunk",),
            cycle=cycle,
            observed=("intermediate:ore_chunk",),
        ),
        _step_input(
            step_id="step:2:transform",
            step_kind=P17BStepKind.TRANSFORM_RESOURCE,
            required_inputs=("intermediate:ore_chunk",),
            required_stations=("station:smelter",),
            expected_outputs=("intermediate:heated_ingot",),
            cycle=cycle,
            observed=("intermediate:heated_ingot",),
        ),
        _step_input(
            step_id="step:3:assemble",
            step_kind=P17BStepKind.USE_STATION,
            required_inputs=("intermediate:heated_ingot",),
            required_stations=("station:assembler",),
            expected_outputs=("target:widget",),
            cycle=cycle,
            observed=("target:widget",),
        ),
    )
    run = build_p17b_live_run(
        run_id="p17b:run:success",
        need=need,
        step_inputs=steps,
        final_target_refs=("target:widget",),
        world0_run_refs=("run:ap01",),
        source_refs=("source:p17b:fixture",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter", "station:assembler"),
    )
    return P17BFixtureBundle("successful_bounded_chain", P17BRunStatus.COMPLETED_BOUNDED_FIXTURE, run, "bounded 3-step chain")


def missing_ap01_blocks_step_fixture() -> P17BFixtureBundle:
    cycle = _world0_noap01_cycle()
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:missing_ap01",
        step_kind=P17BStepKind.GATHER_RESOURCE,
        required_inputs=("resource:ore",),
        required_stations=(),
        expected_outputs=("intermediate:ore_chunk",),
        cycle=cycle,
        observed=("intermediate:ore_chunk",),
        force_no_ap01=True,
    )
    run = _run_single("p17b:run:missing_ap01", need, step, available=("resource:ore",), stations=())
    return P17BFixtureBundle("missing_ap01_blocks_step", P17BRunStatus.BLOCKED, run, "missing AP01 blocks execution")


def failed_intermediate_stops_chain_fixture() -> P17BFixtureBundle:
    failed = _world0_failed_cycle()
    need = _need("need:target_widget")
    step1 = _step_input(
        step_id="step:failed_transform",
        step_kind=P17BStepKind.TRANSFORM_RESOURCE,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=failed,
        observed=(),
    )
    step2 = _step_input(
        step_id="step:downstream",
        step_kind=P17BStepKind.USE_STATION,
        required_inputs=("intermediate:heated_ingot",),
        required_stations=("station:assembler",),
        expected_outputs=("target:widget",),
        cycle=failed,
        observed=("target:widget",),
    )
    run = build_p17b_live_run(
        run_id="p17b:run:failed_stop",
        need=need,
        step_inputs=(step1, step2),
        final_target_refs=("target:widget",),
        world0_run_refs=("run:failed_exec",),
        source_refs=("source:p17b:fixture",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter", "station:assembler"),
        allow_safe_partial_continuation=False,
    )
    return P17BFixtureBundle("failed_intermediate_stops_chain", P17BRunStatus.BLOCKED, run, "failed step preserves residue and stops chain")


def unverified_intermediate_blocks_downstream_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    step1 = _step_input(
        step_id="step:unverified",
        step_kind=P17BStepKind.TRANSFORM_RESOURCE,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=cycle,
        observed=("effect:inspect:observed",),
    )
    step2 = _step_input(
        step_id="step:downstream",
        step_kind=P17BStepKind.USE_STATION,
        required_inputs=("intermediate:heated_ingot",),
        required_stations=("station:assembler",),
        expected_outputs=("target:widget",),
        cycle=cycle,
        observed=("target:widget",),
    )
    run = build_p17b_live_run(
        run_id="p17b:run:unverified_blocks",
        need=need,
        step_inputs=(step1, step2),
        final_target_refs=("target:widget",),
        world0_run_refs=("run:ap01",),
        source_refs=("source:p17b:fixture",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter", "station:assembler"),
    )
    return P17BFixtureBundle("unverified_intermediate_blocks_downstream", P17BRunStatus.BLOCKED, run, "expected effect is not verified")


def missing_resource_blocks_chain_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:missing_resource",
        step_kind=P17BStepKind.GATHER_RESOURCE,
        required_inputs=("resource:ore",),
        required_stations=(),
        expected_outputs=("intermediate:ore_chunk",),
        cycle=cycle,
        observed=("intermediate:ore_chunk",),
    )
    run = _run_single("p17b:run:missing_resource", need, step, available=(), stations=())
    return P17BFixtureBundle("missing_resource_blocks_chain", P17BRunStatus.BLOCKED, run, "required public resource absent")


def blocked_station_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:blocked_station",
        step_kind=P17BStepKind.USE_STATION,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=cycle,
        observed=("intermediate:heated_ingot",),
    )
    run = _run_single("p17b:run:blocked_station", need, step, available=("resource:ore",), stations=())
    return P17BFixtureBundle("blocked_station", P17BRunStatus.BLOCKED, run, "station affordance missing")


def hidden_recipe_blocked_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:hidden_recipe",
        step_kind=P17BStepKind.TRANSFORM_RESOURCE,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=cycle,
        observed=("intermediate:heated_ingot",),
        metadata={"hidden_recipe": "true_recipe_table"},
    )
    run = _run_single("p17b:run:hidden_recipe", need, step, available=("resource:ore",), stations=("station:smelter",))
    return P17BFixtureBundle("hidden_recipe_blocked", P17BRunStatus.BLOCKED, run, "hidden recipe payload blocked")


def adapter_solution_sequence_blocked_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:adapter_solution",
        step_kind=P17BStepKind.USE_STATION,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=cycle,
        observed=("intermediate:heated_ingot",),
        metadata_refs=("solution_sequence:1>2>3",),
    )
    run = _run_single("p17b:run:adapter_solution", need, step, available=("resource:ore",), stations=("station:smelter",))
    return P17BFixtureBundle("adapter_solution_sequence_blocked", P17BRunStatus.BLOCKED, run, "adapter sequence script blocked")


def contactspec_factory_script_blocked_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:contactspec_script",
        step_kind=P17BStepKind.USE_STATION,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=cycle,
        observed=("intermediate:heated_ingot",),
        metadata={"ordered_plan": "factory_steps"},
    )
    run = _run_single("p17b:run:contactspec_script", need, step, available=("resource:ore",), stations=("station:smelter",))
    return P17BFixtureBundle("contactspec_factory_script_blocked", P17BRunStatus.BLOCKED, run, "contact declaration script blocked")


def cost_winner_permission_blocked_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:cost_permission",
        step_kind=P17BStepKind.USE_STATION,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=cycle,
        observed=("intermediate:heated_ingot",),
        metadata_refs=("cost_winner:candidate_a",),
    )
    run = _run_single("p17b:run:cost_permission", need, step, available=("resource:ore",), stations=("station:smelter",))
    return P17BFixtureBundle("cost_winner_permission_blocked", P17BRunStatus.BLOCKED, run, "cost winner cannot authorize step")


def provider_hint_truth_blocked_fixture() -> P17BFixtureBundle:
    cycle = _world0_success_cycle("step")
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:provider_truth",
        step_kind=P17BStepKind.TRANSFORM_RESOURCE,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=cycle,
        observed=("intermediate:heated_ingot",),
        provider_hint_refs=("provider_truth:asserted",),
    )
    run = _run_single("p17b:run:provider_truth", need, step, available=("resource:ore",), stations=("station:smelter",))
    return P17BFixtureBundle("provider_hint_truth_blocked", P17BRunStatus.BLOCKED, run, "provider hint cannot be truth")


def p17_proof_not_live_execution_fixture() -> P17BFixtureBundle:
    need = _need("need:target_widget")
    spec = build_p17b_step_spec(
        step_id="step:proof_only",
        step_kind=P17BStepKind.TRANSFORM_RESOURCE,
        required_input_refs=("resource:ore",),
        required_station_refs=("station:smelter",),
        expected_output_refs=("target:widget",),
        required_micro_operation_kinds=("transform_resource",),
        allowed_action_surface_refs=("surface:use_station",),
        source_refs=("source:p17b:proof",),
        metadata={"proof_trace_only": True},
    )
    step = P17BStepInput(step_spec=spec, metadata_refs=("p17_proof_only",), micro_operation_refs=("micro:proof:1",))
    run = build_p17b_live_run(
        run_id="p17b:run:proof_only",
        need=need,
        step_inputs=(step,),
        final_target_refs=("target:widget",),
        world0_run_refs=(),
        source_refs=("source:p17b:proof",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter",),
        metadata={"proof_trace_only": True},
    )
    return P17BFixtureBundle("p17_proof_not_live_execution", P17BRunStatus.BLOCKED, run, "proof chain must not count as live")


def noop_not_completion_fixture() -> P17BFixtureBundle:
    cycle = _world0_noap01_cycle()
    need = _need("need:target_widget")
    step = _step_input(
        step_id="step:noop",
        step_kind=P17BStepKind.WAIT,
        required_inputs=(),
        required_stations=(),
        expected_outputs=("target:widget",),
        cycle=cycle,
        observed=(),
        force_no_ap01=True,
    )
    run = _run_single("p17b:run:noop", need, step, available=(), stations=())
    return P17BFixtureBundle("noop_not_completion", P17BRunStatus.BLOCKED, run, "noop path cannot claim completion")


def residue_recovery_partial_fixture() -> P17BFixtureBundle:
    failed = _world0_failed_cycle()
    ok = _world0_success_cycle("recover")
    need = _need("need:target_widget")
    step1 = _step_input(
        step_id="step:fail_then_recover",
        step_kind=P17BStepKind.REPAIR_CHECK,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=failed,
        observed=(),
    )
    step2 = _step_input(
        step_id="step:recover",
        step_kind=P17BStepKind.TRANSFORM_RESOURCE,
        required_inputs=("resource:ore",),
        required_stations=("station:smelter",),
        expected_outputs=("intermediate:heated_ingot",),
        cycle=ok,
        observed=("intermediate:heated_ingot",),
    )
    run = build_p17b_live_run(
        run_id="p17b:run:recovery_partial",
        need=need,
        step_inputs=(step1, step2),
        final_target_refs=("target:widget",),
        world0_run_refs=("run:failed_exec", "run:ap01"),
        source_refs=("source:p17b:fixture",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter",),
        allow_safe_partial_continuation=True,
    )
    return P17BFixtureBundle("residue_recovery_partial", P17BRunStatus.PARTIAL, run, "safe continuation preserves failure residue")


def replay_trace_fixture() -> P17BFixtureBundle:
    return successful_bounded_chain_fixture()


def _world0_success_cycle(seed: str) -> WorldRunnerCycleResult:
    bundle = ap01_execution_fixture()
    return run_world_cycle(bundle.loop_input.cycle_inputs[0], adapter=bundle.adapter, config=bundle.loop_input.config)


def _world0_noap01_cycle() -> WorldRunnerCycleResult:
    bundle = no_ap01_no_execution_fixture()
    return run_world_cycle(bundle.loop_input.cycle_inputs[0], adapter=bundle.adapter, config=bundle.loop_input.config)


def _world0_failed_cycle() -> WorldRunnerCycleResult:
    bundle = failed_backend_execution_fixture()
    return run_world_cycle(bundle.loop_input.cycle_inputs[0], adapter=bundle.adapter, config=bundle.loop_input.config)


def _need(target_ref: str) -> P17BFactoryNeed:
    return build_p17b_factory_need(
        need_id=f"need:{target_ref}",
        target_ref=target_ref,
        pressure_refs=("pressure:factory_target",),
        source_refs=("source:p17b:need",),
        public_basis_refs=("basis:public:need", "resource:ore"),
    )


def _step_input(
    *,
    step_id: str,
    step_kind: P17BStepKind,
    required_inputs: tuple[str, ...],
    required_stations: tuple[str, ...],
    expected_outputs: tuple[str, ...],
    cycle: WorldRunnerCycleResult,
    observed: tuple[str, ...],
    metadata: dict[str, object] | None = None,
    provider_hint_refs: tuple[str, ...] = (),
    metadata_refs: tuple[str, ...] = (),
    force_no_ap01: bool = False,
) -> P17BStepInput:
    spec = build_p17b_step_spec(
        step_id=step_id,
        step_kind=step_kind,
        required_input_refs=required_inputs,
        required_station_refs=required_stations,
        expected_output_refs=expected_outputs,
        required_micro_operation_kinds=(step_kind.value,),
        allowed_action_surface_refs=("surface:inspect", "surface:use_station", "surface:gather"),
        source_refs=("source:p17b:step",),
        metadata=metadata or {},
    )
    ap01_refs = () if force_no_ap01 else tuple(req.request_id for req in cycle.ap01_requests)
    return P17BStepInput(
        step_spec=spec,
        cycle_refs=(cycle.cycle_trace.cycle_id,),
        world0_run_ref=f"run:{cycle.cycle_trace.cycle_id}",
        micro_operation_refs=(f"micro:{step_id}",),
        cost_comparison_refs=(f"cost:{step_id}",),
        ap01_request_refs=ap01_refs,
        backend_execution_refs=tuple(item.backend_execution_ref for item in cycle.backend_results) if not force_no_ap01 else (),
        world_effect_feedback_refs=tuple(item.effect_frame_ref for item in cycle.effect_feedback if item.effect_frame_ref) if not force_no_ap01 else (),
        observed_effect_refs=observed,
        residue_refs=cycle.residue_refs,
        uncertainty_refs=cycle.uncertainty_refs,
        provider_hint_refs=provider_hint_refs,
        metadata_refs=metadata_refs,
    )


def _run_single(
    run_id: str,
    need: P17BFactoryNeed,
    step: P17BStepInput,
    *,
    available: tuple[str, ...],
    stations: tuple[str, ...],
) -> object:
    return build_p17b_live_run(
        run_id=run_id,
        need=need,
        step_inputs=(step,),
        final_target_refs=("target:widget",),
        world0_run_refs=(step.world0_run_ref,) if step.world0_run_ref else (),
        source_refs=("source:p17b:fixture",),
        available_resources=available,
        station_affordances=stations,
    )

