from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum

from substrate.contracts import RuntimeState, TransitionResult
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickResult


class RuntimeRouteClass(str, Enum):
    PRODUCTION_CONTOUR = "production_contour"
    HELPER_PATH = "helper_path"
    TEST_ONLY_ABLATION = "test_only_ablation"


class RuntimeDispatchRestriction(StrEnum):
    PRODUCTION_ROUTE_REQUIRED = "production_route_required"
    HELPER_ROUTE_NOT_LAWFUL_PRODUCTION = "helper_route_not_lawful_production"
    NON_PRODUCTION_ROUTE_REQUIRES_EXPLICIT_CONSUMER_OPT_IN = (
        "non_production_route_requires_explicit_consumer_opt_in"
    )
    TEST_ONLY_ROUTE_REQUIRES_EXPLICIT_ALLOW = "test_only_route_requires_explicit_allow"
    TEST_ONLY_ROUTE_REQUIRES_ABLATION_BASIS = "test_only_route_requires_ablation_basis"
    PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS = "production_route_forbids_ablation_flags"
    NON_PRODUCTION_ROUTE_FORBIDS_F01_PERSISTENCE = "non_production_route_forbids_f01_persistence"
    PERSISTENCE_REQUIRES_F01_INPUTS = "persistence_requires_f01_inputs"
    DISPATCH_CONTRACT_MUST_BE_READ = "dispatch_contract_must_be_read"
    TOPOLOGY_BOUND_TO_RT01_CONTOUR = "topology_bound_to_rt01_contour"


class RuntimeRouteBindingConsequence(StrEnum):
    LAWFUL_PRODUCTION_CONTOUR = "lawful_production_contour"
    NON_LAWFUL_HELPER_ROUTE = "non_lawful_helper_route"
    TEST_ONLY_ABLATION_ROUTE = "test_only_ablation_route"


@dataclass(frozen=True, slots=True)
class RuntimeContourNode:
    node_id: str
    phase_id: str
    authority_role: str
    computational_role: str
    surfaces: tuple[str, ...]
    checkpoint_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeContourEdge:
    source_phase: str
    target_phase: str
    relation: str


@dataclass(frozen=True, slots=True)
class RuntimeTickGraph:
    graph_id: str
    contour_id: str
    runtime_order: tuple[str, ...]
    nodes: tuple[RuntimeContourNode, ...]
    edges: tuple[RuntimeContourEdge, ...]
    mandatory_checkpoint_ids: tuple[str, ...]
    source_of_truth_surfaces: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class RuntimeTopologyBundle:
    bundle_id: str
    contour_id: str
    runtime_entry: str
    execution_spine_phase: str
    downstream_obedience_phase: str
    shared_domain_paths: tuple[str, ...]
    enforcement_hooks: tuple[str, ...]
    f01_transition_route: str
    tick_graph: RuntimeTickGraph
    reason: str


@dataclass(frozen=True, slots=True)
class RuntimeDispatchRequest:
    tick_input: SubjectTickInput
    context: SubjectTickContext | None = None
    route_class: RuntimeRouteClass = RuntimeRouteClass.PRODUCTION_CONTOUR
    allow_helper_route: bool = False
    allow_test_only_route: bool = False
    allow_non_production_consumer_opt_in: bool = False
    persist_via_f01: bool = False
    runtime_state: RuntimeState | None = None
    transition_id: str | None = None
    requested_at: str | None = None
    cause_chain: tuple[str, ...] = ("runtime-topology-dispatch",)


@dataclass(frozen=True, slots=True)
class RuntimeDispatchDecision:
    accepted: bool
    lawful_production_route: bool
    route_binding_consequence: RuntimeRouteBindingConsequence
    route_class: RuntimeRouteClass
    restrictions: tuple[RuntimeDispatchRestriction, ...]
    reason: str
    requires_dispatch_entry: bool
    topology_ref: str


@dataclass(frozen=True, slots=True)
class RuntimeDispatchResult:
    decision: RuntimeDispatchDecision
    bundle: RuntimeTopologyBundle
    tick_graph: RuntimeTickGraph
    request: RuntimeDispatchRequest
    subject_tick_result: SubjectTickResult | None
    persist_transition: TransitionResult | None
    dispatch_lineage: tuple[str, ...] = field(default_factory=tuple)
