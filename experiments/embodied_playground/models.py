from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Orientation(str, Enum):
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"
    UNKNOWN = "unknown"


class BodyPostureStatus(str, Enum):
    READY = "ready"
    IMPAIRED = "impaired"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class ActuatorStatus(str, Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class InventoryKnowledgeStatus(str, Enum):
    VISIBLE = "visible"
    EMPTY = "empty"
    FULL = "full"
    UNKNOWN = "unknown"


class WorldObjectKind(str, Enum):
    ITEM = "item"
    RESOURCE_NODE = "resource_node"
    STATION = "station"
    OBSTACLE = "obstacle"
    APERTURE = "aperture"
    CONTAINER = "container"
    FLUID_SOURCE = "fluid_source"
    ENTITY = "entity"
    UNKNOWN = "unknown"


class InteractionSurfaceKind(str, Enum):
    MOVEMENT = "movement"
    PICKUP = "pickup"
    DROP = "drop"
    INSPECT = "inspect"
    INTERACT = "interact"
    USE_STATION = "use_station"
    COMMUNICATE = "communicate"
    WAIT = "wait"
    UNKNOWN = "unknown"


class EffectStatus(str, Enum):
    NOT_ATTEMPTED = "not_attempted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    PARTIAL = "partial"
    NO_EFFECT = "no_effect"
    UNKNOWN = "unknown"


class CorrelationStatus(str, Enum):
    CORRELATED_TO_REQUEST = "correlated_to_request"
    MISSING_REQUEST = "missing_request"
    PASSIVE_WORLD_EVENT = "passive_world_event"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


_FORBIDDEN_AP01_REF_MARKERS: tuple[str, ...] = (
    "scenario_id",
    "test_name",
    "expected_outcome",
    "gui_label",
    "eval_only",
    "hidden_truth",
    "external_stub_target",
)
_AP01_REF_ALLOWED_PREFIXES: tuple[str, ...] = ("ap01_request:", "ap01:req:")


@dataclass(frozen=True, slots=True)
class AP01RequestRef:
    request_ref: str
    source: str = "ap01"
    boundary_preserved: bool = True
    must_wait_for_effect: bool = True

    def __post_init__(self) -> None:
        if not self.request_ref:
            raise ValueError("AP01RequestRef.request_ref is required")
        lowered = self.request_ref.lower()
        if not lowered.startswith(_AP01_REF_ALLOWED_PREFIXES):
            raise ValueError("AP01RequestRef.request_ref must use ap01_request: or ap01:req: prefix")
        if lowered in {"request", "ap01_request", "ap01:req"}:
            raise ValueError("AP01RequestRef.request_ref is too generic")
        if any(marker in lowered for marker in _FORBIDDEN_AP01_REF_MARKERS):
            raise ValueError("AP01RequestRef.request_ref cannot contain scenario/eval/hidden/test markers")
        if self.source != "ap01":
            raise ValueError("AP01RequestRef.source must be 'ap01'")
        if not self.boundary_preserved:
            raise ValueError("AP01RequestRef.boundary_preserved must remain True")
        if not self.must_wait_for_effect:
            raise ValueError("AP01RequestRef.must_wait_for_effect must remain True")


@dataclass(frozen=True, slots=True)
class BodyState:
    subject_id: str
    body_ref: str
    location_ref: str
    orientation: Orientation | str
    posture_status: BodyPostureStatus | str
    hand_slot: str | None
    held_item_ref: str | None
    actuator_status: ActuatorStatus | str
    movement_blocked_reason: str | None = None
    visible_range: float | None = None
    sensor_profile: tuple[str, ...] = ()
    hidden_truth_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.subject_id or not self.body_ref or not self.location_ref:
            raise ValueError("BodyState requires subject_id/body_ref/location_ref")
        if not self.hidden_truth_excluded:
            raise ValueError("BodyState must exclude hidden truth")


@dataclass(frozen=True, slots=True)
class InventoryState:
    inventory_ref: str
    owner_subject_id: str
    capacity_slots: int
    used_slots: int
    item_refs: tuple[str, ...]
    item_counts: dict[str, int]
    knowledge_status: InventoryKnowledgeStatus | str
    blocked_reason: str | None = None
    hidden_truth_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.inventory_ref or not self.owner_subject_id:
            raise ValueError("InventoryState requires inventory_ref/owner_subject_id")
        if self.capacity_slots < 0 or self.used_slots < 0:
            raise ValueError("InventoryState slot counts must be non-negative")
        if self.used_slots > self.capacity_slots:
            raise ValueError("InventoryState used_slots cannot exceed capacity_slots")
        if not self.hidden_truth_excluded:
            raise ValueError("InventoryState must exclude hidden truth")


@dataclass(frozen=True, slots=True)
class WorldObjectObservation:
    object_ref: str
    object_kind: WorldObjectKind | str
    display_label: str | None
    location_ref: str
    relation_to_subject: str | None
    observable_properties: dict[str, object]
    source_authority: str
    claim_not_fact_marker: bool
    hidden_truth_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.object_ref or not self.location_ref:
            raise ValueError("WorldObjectObservation requires object_ref/location_ref")
        if not self.source_authority:
            raise ValueError("WorldObjectObservation requires source_authority")
        if not self.hidden_truth_excluded:
            raise ValueError("WorldObjectObservation must exclude hidden truth")


@dataclass(frozen=True, slots=True)
class AvailableInteractionSurface:
    surface_ref: str
    surface_kind: InteractionSurfaceKind | str
    target_ref: str | None
    action_kinds: tuple[str, ...]
    constraints: tuple[str, ...]
    affordance_hint_refs: tuple[str, ...]
    source_authority: str
    is_permission: bool = False
    hidden_truth_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.surface_ref:
            raise ValueError("AvailableInteractionSurface requires surface_ref")
        if not self.action_kinds:
            raise ValueError("AvailableInteractionSurface requires action_kinds")
        if self.is_permission:
            raise ValueError("AvailableInteractionSurface cannot assert permission")
        if not self.hidden_truth_excluded:
            raise ValueError("AvailableInteractionSurface must exclude hidden truth")


@dataclass(frozen=True, slots=True)
class ActionSpaceFrame:
    frame_id: str
    subject_id: str
    tick_index: int
    available_surfaces: tuple[AvailableInteractionSurface, ...]
    allowed_action_kinds_from_body: tuple[str, ...]
    body_constraints: tuple[str, ...]
    action_space_is_permission: bool = False
    action_space_is_selection: bool = False
    action_space_is_execution: bool = False
    hidden_truth_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.frame_id or not self.subject_id:
            raise ValueError("ActionSpaceFrame requires frame_id/subject_id")
        if self.tick_index < 0:
            raise ValueError("ActionSpaceFrame tick_index must be non-negative")
        if self.action_space_is_permission or self.action_space_is_selection or self.action_space_is_execution:
            raise ValueError("ActionSpaceFrame cannot encode permission/selection/execution")
        if not self.hidden_truth_excluded:
            raise ValueError("ActionSpaceFrame must exclude hidden truth")


@dataclass(frozen=True, slots=True)
class ObservationFrame:
    observation_id: str
    subject_id: str
    tick_index: int
    body_state: BodyState
    inventory_state: InventoryState
    visible_objects: tuple[WorldObjectObservation, ...]
    action_space: ActionSpaceFrame
    previous_effect_refs: tuple[str, ...]
    world_time_ref: str | None
    source_authority: str
    hidden_truth_excluded: bool = True
    eval_only_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.observation_id or not self.subject_id:
            raise ValueError("ObservationFrame requires observation_id/subject_id")
        if self.tick_index < 0:
            raise ValueError("ObservationFrame tick_index must be non-negative")
        if not self.source_authority:
            raise ValueError("ObservationFrame requires source_authority")
        if not self.hidden_truth_excluded or not self.eval_only_excluded:
            raise ValueError("ObservationFrame must exclude hidden/eval-only truth")


@dataclass(frozen=True, slots=True)
class PublishedActionEnvelope:
    envelope_id: str
    subject_id: str
    ap01_request_ref: AP01RequestRef | str
    action_kind: str
    target_ref: str | None
    args: dict[str, object]
    intended_effect: str
    source_tick_ref: str
    source_phase_refs: tuple[str, ...]
    permission_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    affordance_binding_refs: tuple[str, ...]
    request_boundary_preserved: bool = True
    submitted_to_world: bool = False
    executed_by_world: bool = False
    no_hidden_truth_used: bool = True
    no_eval_only_used: bool = True
    no_scenario_label_used: bool = True
    hidden_truth_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.envelope_id or not self.subject_id or not self.ap01_request_ref:
            raise ValueError("PublishedActionEnvelope requires envelope_id/subject_id/ap01_request_ref")
        if isinstance(self.ap01_request_ref, str):
            object.__setattr__(self, "ap01_request_ref", AP01RequestRef(request_ref=self.ap01_request_ref))
        elif not isinstance(self.ap01_request_ref, AP01RequestRef):
            raise TypeError("ap01_request_ref must be AP01RequestRef or str")
        if not self.action_kind or not self.intended_effect:
            raise ValueError("PublishedActionEnvelope requires action_kind/intended_effect")
        if self.submitted_to_world or self.executed_by_world:
            raise ValueError("PublishedActionEnvelope is publication-only, not execution state")
        if not self.request_boundary_preserved:
            raise ValueError("PublishedActionEnvelope must preserve AP01 request boundary")
        if not self.source_tick_ref or not self.source_phase_refs:
            raise ValueError("PublishedActionEnvelope requires source_tick_ref/source_phase_refs")
        if not self.no_hidden_truth_used or not self.no_eval_only_used or not self.no_scenario_label_used:
            raise ValueError("PublishedActionEnvelope requires no_hidden/no_eval/no_scenario flags")
        if not self.hidden_truth_excluded:
            raise ValueError("PublishedActionEnvelope must exclude hidden truth")

    @property
    def ap01_request_id(self) -> str:
        return self.ap01_request_ref.request_ref if isinstance(self.ap01_request_ref, AP01RequestRef) else self.ap01_request_ref


@dataclass(frozen=True, slots=True)
class ActionEffectFrame:
    effect_id: str
    subject_id: str
    tick_index: int
    request_ref: str | None
    envelope_ref: str | None
    action_kind: str
    target_ref: str | None
    effect_status: EffectStatus | str
    body_delta: dict[str, object]
    inventory_delta: dict[str, object]
    world_delta_public: dict[str, object]
    observed_result_refs: tuple[str, ...]
    blocked_reason: str | None = None
    failure_reason: str | None = None
    partial_reason: str | None = None
    correlation_status: CorrelationStatus | str = CorrelationStatus.AMBIGUOUS
    hidden_truth_excluded: bool = True
    eval_only_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.effect_id or not self.subject_id:
            raise ValueError("ActionEffectFrame requires effect_id/subject_id")
        if self.tick_index < 0:
            raise ValueError("ActionEffectFrame tick_index must be non-negative")
        if not self.action_kind:
            raise ValueError("ActionEffectFrame requires action_kind")
        if not self.hidden_truth_excluded or not self.eval_only_excluded:
            raise ValueError("ActionEffectFrame must exclude hidden/eval-only truth")


@dataclass(frozen=True, slots=True)
class PublicWorldSnapshot:
    snapshot_id: str
    subject_id: str
    tick_index: int
    visible_body_state: BodyState
    visible_inventory_state: InventoryState
    visible_objects: tuple[WorldObjectObservation, ...]
    visible_surfaces: tuple[AvailableInteractionSurface, ...]
    public_effect_refs: tuple[str, ...]
    hidden_truth_excluded: bool = True

    def __post_init__(self) -> None:
        if not self.snapshot_id or not self.subject_id:
            raise ValueError("PublicWorldSnapshot requires snapshot_id/subject_id")
        if self.tick_index < 0:
            raise ValueError("PublicWorldSnapshot tick_index must be non-negative")
        if not self.hidden_truth_excluded:
            raise ValueError("PublicWorldSnapshot must exclude hidden truth")


@dataclass(frozen=True, slots=True)
class EvalOnlyWorldTruth:
    snapshot_id: str
    tick_index: int
    hidden_objects: tuple[dict[str, object], ...] = ()
    hidden_inventory: dict[str, object] = field(default_factory=dict)
    true_recipe_table: dict[str, object] = field(default_factory=dict)
    expected_outcome: str | None = None
    scenario_labels: tuple[str, ...] = ()
    must_never_enter_subject_visible: bool = True

    def __post_init__(self) -> None:
        if not self.snapshot_id:
            raise ValueError("EvalOnlyWorldTruth requires snapshot_id")
        if self.tick_index < 0:
            raise ValueError("EvalOnlyWorldTruth tick_index must be non-negative")
        if not self.must_never_enter_subject_visible:
            raise ValueError("EvalOnlyWorldTruth must never be mixed into subject-visible payload")
