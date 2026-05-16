from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ApertureState,
    CounterpartEmission,
    CounterpartSignalKind,
    ResourceInventoryTruth,
    ResourceKind,
    ResourceLevel,
    SignalAuthority,
    TransferOutcome,
)


@dataclass(frozen=True, slots=True)
class ScriptedScenario:
    scenario_id: str
    a_truth: ResourceInventoryTruth
    b_truth: ResourceInventoryTruth
    emissions: tuple[CounterpartEmission, ...]
    eval_only_labels: tuple[str, ...]


def _inventory(actor_id: str, *, food: ResourceLevel, water: ResourceLevel) -> ResourceInventoryTruth:
    return ResourceInventoryTruth(
        actor_id=actor_id,
        resource_levels={
            ResourceKind.FOOD: food,
            ResourceKind.WATER: water,
        },
        hidden_from_subject=True,
    )


def _emission(
    scenario_id: str,
    step: int,
    signal: CounterpartSignalKind,
    *,
    resource: ResourceKind | None = None,
    reported_level: ResourceLevel | None = None,
    item_kind: ResourceKind | None = None,
    aperture: ApertureState = ApertureState.OPEN,
    authority: SignalAuthority = SignalAuthority.COUNTERPART_CLAIM,
    transfer_outcome: TransferOutcome = TransferOutcome.NOT_ATTEMPTED,
    notes: str = "",
) -> CounterpartEmission:
    return CounterpartEmission(
        emission_id=f"{scenario_id}:emission:{step}",
        source_actor_id="counterpart_b",
        signal_kind=signal,
        resource_kind=resource,
        reported_level=reported_level,
        item_kind=item_kind,
        aperture_state=aperture,
        source_authority=authority,
        emitted_at_step=step,
        provenance_ref=("experiments.symbolic_trade", scenario_id),
        visible_to_subject=True,
        eval_truth_ref=f"{scenario_id}:truth:b",
        transfer_outcome=transfer_outcome,
        notes=notes,
    )


def build_scripted_stage1_scenario(scenario_id: str) -> ScriptedScenario:
    a_default = _inventory("subject_a", food=ResourceLevel.SURPLUS, water=ResourceLevel.DEFICIT)

    if scenario_id == "presence_only":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.UNKNOWN, water=ResourceLevel.UNKNOWN),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.PRESENCE_PING, authority=SignalAuthority.OBSERVED_EVENT),
            ),
            eval_only_labels=("presence_detectable",),
        )

    if scenario_id == "resource_claim_contact":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.DEFICIT, water=ResourceLevel.SURPLUS),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS),
                _emission(scenario_id, 2, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.FOOD, reported_level=ResourceLevel.DEFICIT),
            ),
            eval_only_labels=("counterpart_claim_contact_established",),
        )

    if scenario_id == "mirrored_resource_asymmetry":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.DEFICIT, water=ResourceLevel.SURPLUS),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.PRESENCE_PING, authority=SignalAuthority.OBSERVED_EVENT),
                _emission(scenario_id, 2, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS),
                _emission(scenario_id, 3, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.FOOD, reported_level=ResourceLevel.DEFICIT),
            ),
            eval_only_labels=("potential_reciprocity_eval_only",),
        )

    if scenario_id == "false_counterpart_claim":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.SUFFICIENT, water=ResourceLevel.DEFICIT),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS, notes="intentionally false claim"),
            ),
            eval_only_labels=("false_claim_expected",),
        )

    if scenario_id == "blocked_aperture":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.DEFICIT, water=ResourceLevel.SURPLUS),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS),
                _emission(scenario_id, 2, CounterpartSignalKind.BLOCKED, aperture=ApertureState.BLOCKED, authority=SignalAuthority.OBSERVED_EVENT, notes="aperture blocked"),
                _emission(
                    scenario_id,
                    3,
                    CounterpartSignalKind.TRANSFER_RESULT,
                    resource=ResourceKind.WATER,
                    reported_level=ResourceLevel.UNKNOWN,
                    aperture=ApertureState.BLOCKED,
                    authority=SignalAuthority.OBSERVED_EVENT,
                    transfer_outcome=TransferOutcome.FAILED_BLOCKED,
                ),
            ),
            eval_only_labels=("transfer_not_feasible_under_blocked_aperture",),
        )

    if scenario_id == "noisy_signal":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.DEFICIT, water=ResourceLevel.SUFFICIENT),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS),
                _emission(scenario_id, 2, CounterpartSignalKind.CONTRADICTION, resource=ResourceKind.WATER, reported_level=ResourceLevel.DEFICIT, aperture=ApertureState.NOISY, authority=SignalAuthority.OBSERVED_EVENT),
            ),
            eval_only_labels=("signal_ambiguity_present",),
        )

    if scenario_id == "transfer_seen_without_trade_token":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.DEFICIT, water=ResourceLevel.SURPLUS),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.ITEM_SEEN_AT_APERTURE, item_kind=ResourceKind.WATER, authority=SignalAuthority.OBSERVED_EVENT),
                _emission(scenario_id, 2, CounterpartSignalKind.TRANSFER_ATTEMPT, item_kind=ResourceKind.WATER, authority=SignalAuthority.OBSERVED_EVENT),
                _emission(scenario_id, 3, CounterpartSignalKind.TRANSFER_RESULT, item_kind=ResourceKind.WATER, authority=SignalAuthority.OBSERVED_EVENT, transfer_outcome=TransferOutcome.SUCCEEDED),
            ),
            eval_only_labels=("object_transfer_event_only",),
        )

    if scenario_id == "eval_label_leak_attack":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.DEFICIT, water=ResourceLevel.SURPLUS),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.PRESENCE_PING, authority=SignalAuthority.OBSERVED_EVENT),
                _emission(scenario_id, 2, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS),
            ),
            eval_only_labels=("mutually_beneficial_trade_possible_eval_only",),
        )

    if scenario_id == "a_deficit_only":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=_inventory("subject_a", food=ResourceLevel.SUFFICIENT, water=ResourceLevel.DEFICIT),
            b_truth=_inventory("counterpart_b", food=ResourceLevel.UNKNOWN, water=ResourceLevel.UNKNOWN),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.PRESENCE_PING, authority=SignalAuthority.OBSERVED_EVENT),
            ),
            eval_only_labels=("a_deficit_without_counterpart_resource_claim",),
        )

    if scenario_id == "b_surplus_claim_only":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=_inventory("subject_a", food=ResourceLevel.SUFFICIENT, water=ResourceLevel.SUFFICIENT),
            b_truth=_inventory("counterpart_b", food=ResourceLevel.SUFFICIENT, water=ResourceLevel.SURPLUS),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS),
            ),
            eval_only_labels=("counterpart_surplus_claim_without_a_matching_deficit",),
        )

    if scenario_id == "claim_then_confirmed_transfer":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.DEFICIT, water=ResourceLevel.SURPLUS),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS),
                _emission(scenario_id, 2, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.FOOD, reported_level=ResourceLevel.DEFICIT),
                _emission(scenario_id, 3, CounterpartSignalKind.TRANSFER_ATTEMPT, item_kind=ResourceKind.WATER, authority=SignalAuthority.OBSERVED_EVENT),
                _emission(
                    scenario_id,
                    4,
                    CounterpartSignalKind.TRANSFER_RESULT,
                    item_kind=ResourceKind.WATER,
                    authority=SignalAuthority.OBSERVED_EVENT,
                    transfer_outcome=TransferOutcome.SUCCEEDED,
                ),
            ),
            eval_only_labels=("claim_then_transfer_confirmation_visible",),
        )

    if scenario_id == "claim_then_failed_transfer":
        return ScriptedScenario(
            scenario_id=scenario_id,
            a_truth=a_default,
            b_truth=_inventory("counterpart_b", food=ResourceLevel.DEFICIT, water=ResourceLevel.SURPLUS),
            emissions=(
                _emission(scenario_id, 1, CounterpartSignalKind.RESOURCE_STATUS_CLAIM, resource=ResourceKind.WATER, reported_level=ResourceLevel.SURPLUS),
                _emission(scenario_id, 2, CounterpartSignalKind.TRANSFER_ATTEMPT, item_kind=ResourceKind.WATER, authority=SignalAuthority.OBSERVED_EVENT),
                _emission(
                    scenario_id,
                    3,
                    CounterpartSignalKind.TRANSFER_RESULT,
                    item_kind=ResourceKind.WATER,
                    aperture=ApertureState.BLOCKED,
                    authority=SignalAuthority.OBSERVED_EVENT,
                    transfer_outcome=TransferOutcome.FAILED_BLOCKED,
                ),
            ),
            eval_only_labels=("claim_then_transfer_failed",),
        )

    raise ValueError(f"Unsupported symbolic trade scenario: {scenario_id}")


def stage1_scenarios() -> tuple[str, ...]:
    return (
        "presence_only",
        "resource_claim_contact",
        "mirrored_resource_asymmetry",
        "false_counterpart_claim",
        "blocked_aperture",
        "noisy_signal",
        "transfer_seen_without_trade_token",
        "eval_label_leak_attack",
        "a_deficit_only",
        "b_surplus_claim_only",
        "claim_then_confirmed_transfer",
        "claim_then_failed_transfer",
    )
