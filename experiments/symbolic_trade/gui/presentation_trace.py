from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PresentationBasis(str, Enum):
    DIRECT_TRACE = "direct_trace_based"
    INFERRED_SUMMARY = "inferred_from_stage5_summary"
    NOT_EXPOSED = "not_exposed"


@dataclass(frozen=True, slots=True)
class ResourceVisualState:
    owner: str
    resource_kind: str
    level_ru: str
    visibility_ru: str
    is_claim: bool


@dataclass(frozen=True, slots=True)
class ChamberActorState:
    actor_id: str
    label_ru: str
    resources: tuple[ResourceVisualState, ...]
    notes_ru: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ChamberEvent:
    event_kind: str
    label_ru: str
    source_actor: str
    target_actor: str
    causal_status: str
    active: bool
    refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ChamberState:
    actor_a: ChamberActorState
    actor_b: ChamberActorState
    aperture_status: str
    aperture_open: bool
    offer_visible: bool
    affordance_visible: bool
    invocation_request_visible: bool
    actuator_invoked_visible: bool
    transfer_result_visible: bool
    transfer_result: str
    completion_visible: bool
    completion_claim: bool
    residue_visible: bool
    passive_packet_ref_count: int
    causal_post_invocation_ref_count: int
    events: tuple[ChamberEvent, ...]


@dataclass(frozen=True, slots=True)
class PresentationFrame:
    step_index: int
    step_id: str
    title_ru: str
    explanation_ru: str
    event_kind: str
    chamber_state: ChamberState
    phase_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    basis: PresentationBasis
    public_status: str


@dataclass(frozen=True, slots=True)
class PlaybackTrace:
    scenario_id: str
    execute_world_actuator: bool
    frames: tuple[PresentationFrame, ...]

    @property
    def frame_count(self) -> int:
        return len(self.frames)


def _enum_or_raw(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, str) and "." in value:
        return value.rsplit(".", 1)[-1].lower()
    return str(value)


def _phase_refs(payload: dict[str, Any], phase: str) -> tuple[str, ...]:
    return tuple(
        str(ref)
        for ref in payload.get("phase_coverage_evidence", []) or []
        if str(ref).startswith(f"{phase}:")
    )


def _claim_resources(visible_packets: list[dict[str, Any]], *, reveal: bool) -> tuple[ResourceVisualState, ...]:
    if not reveal:
        return ()
    resources: list[ResourceVisualState] = []
    for packet in visible_packets:
        if packet.get("source_authority") != "counterpart_claim":
            continue
        resource = packet.get("resource_kind")
        level = packet.get("reported_level")
        if not resource or not level:
            continue
        resources.append(
            ResourceVisualState(
                owner="B",
                resource_kind=str(resource),
                level_ru="заявлен профицит" if str(level) == "surplus" else "заявлен дефицит",
                visibility_ru="видимое заявление",
                is_claim=True,
            )
        )
    return tuple(resources)


def _a_resources(*, reveal: bool) -> tuple[ResourceVisualState, ...]:
    if not reveal:
        return ()
    return (
        ResourceVisualState(
            owner="A",
            resource_kind="water",
            level_ru="дефицит",
            visibility_ru="self-state A",
            is_claim=False,
        ),
        ResourceVisualState(
            owner="A",
            resource_kind="food",
            level_ru="профицит",
            visibility_ru="self-state A",
            is_claim=False,
        ),
    )


def _base_events(
    *,
    claim_refs: tuple[str, ...],
    passive_refs: tuple[str, ...],
    causal_refs: tuple[str, ...],
    show_claim: bool,
    show_offer: bool,
    show_affordance: bool,
    show_request: bool,
    show_invocation: bool,
    show_result: bool,
    show_completion: bool,
    transfer_result: str,
    completion_claim: bool,
) -> tuple[ChamberEvent, ...]:
    events: list[ChamberEvent] = []
    if show_claim:
        events.append(
            ChamberEvent(
                event_kind="claim",
                label_ru="B сообщает ресурсное заявление",
                source_actor="B",
                target_actor="A",
                causal_status="claim_not_fact",
                active=True,
                refs=claim_refs,
            )
        )
    if show_offer:
        events.append(
            ChamberEvent(
                event_kind="offer_candidate",
                label_ru="A формирует кандидат предложения",
                source_actor="A",
                target_actor="B",
                causal_status="candidate_not_execution",
                active=True,
                refs=(),
            )
        )
    if show_affordance:
        events.append(
            ChamberEvent(
                event_kind="affordance_selection",
                label_ru="Выбрана возможность внешнего действия",
                source_actor="A",
                target_actor="aperture",
                causal_status="selection_not_invocation",
                active=True,
                refs=(),
            )
        )
    if show_request:
        events.append(
            ChamberEvent(
                event_kind="invocation_request",
                label_ru="Создан запрос к внешнему исполнителю",
                source_actor="A",
                target_actor="world_actuator",
                causal_status="request_not_execution",
                active=True,
                refs=(),
            )
        )
    if show_invocation:
        events.append(
            ChamberEvent(
                event_kind="world_actuator_invocation",
                label_ru="Внешний исполнитель вызван",
                source_actor="world_actuator",
                target_actor="aperture",
                causal_status="causally_after_invocation",
                active=True,
                refs=causal_refs,
            )
        )
    if show_result:
        status = "каузальный результат" if causal_refs else "пассивное наблюдение"
        events.append(
            ChamberEvent(
                event_kind="transfer_result",
                label_ru=f"Результат переноса: {transfer_result}",
                source_actor="aperture",
                target_actor="A/B",
                causal_status=status,
                active=True,
                refs=causal_refs if causal_refs else passive_refs,
            )
        )
    if show_completion:
        events.append(
            ChamberEvent(
                event_kind="completion_verification",
                label_ru="Завершение подтверждено полной цепочкой" if completion_claim else "Завершение не подтверждено",
                source_actor="verification",
                target_actor="episode",
                causal_status="verified" if completion_claim else "not_verified",
                active=True,
                refs=causal_refs,
            )
        )
    return tuple(events)


def _chamber_state(
    payload: dict[str, Any],
    *,
    reveal_a: bool,
    reveal_claim: bool,
    show_offer: bool,
    show_affordance: bool,
    show_request: bool,
    show_invocation: bool,
    show_result: bool,
    show_completion: bool,
    show_residue: bool,
) -> ChamberState:
    visible_packets = list(payload.get("visible_packets", []) or [])
    selection = payload.get("selection_record", {}) or {}
    episode = payload.get("episode_record", {}) or {}
    transfer_result = str(payload.get("transfer_result", "unknown"))
    completion_claim = bool(episode.get("completion_claim", False))
    passive_refs = tuple(str(ref) for ref in episode.get("passive_packet_refs", []) or [])
    causal_refs = tuple(str(ref) for ref in episode.get("causal_post_invocation_refs", []) or [])
    claim_refs = tuple(
        str(packet.get("packet_id"))
        for packet in visible_packets
        if packet.get("source_authority") == "counterpart_claim"
    )
    permission = str(selection.get("permission_status", "unknown"))
    selected_status = _enum_or_raw(selection.get("selected_affordance_status", selection.get("selection_status", "")))
    aperture_open = permission != "blocked" and selected_status != "blocked"
    if any(str(packet.get("aperture_state")) == "closed" for packet in visible_packets):
        aperture_open = False
    aperture_status = "открыта" if aperture_open else "заблокирована"

    actor_a = ChamberActorState(
        actor_id="A",
        label_ru="Субъект A",
        resources=_a_resources(reveal=reveal_a),
        notes_ru=("self-state не является разрешением",) if reveal_a else (),
    )
    actor_b = ChamberActorState(
        actor_id="B",
        label_ru="Scripted B",
        resources=_claim_resources(visible_packets, reveal=reveal_claim),
        notes_ru=("заявления B не являются фактами",) if reveal_claim else (),
    )
    events = _base_events(
        claim_refs=claim_refs,
        passive_refs=passive_refs,
        causal_refs=causal_refs,
        show_claim=reveal_claim,
        show_offer=show_offer,
        show_affordance=show_affordance,
        show_request=show_request,
        show_invocation=show_invocation,
        show_result=show_result,
        show_completion=show_completion,
        transfer_result=transfer_result,
        completion_claim=completion_claim,
    )
    return ChamberState(
        actor_a=actor_a,
        actor_b=actor_b,
        aperture_status=aperture_status,
        aperture_open=aperture_open,
        offer_visible=show_offer,
        affordance_visible=show_affordance,
        invocation_request_visible=show_request,
        actuator_invoked_visible=show_invocation,
        transfer_result_visible=show_result,
        transfer_result=transfer_result if show_result else "not_shown",
        completion_visible=show_completion,
        completion_claim=completion_claim if show_completion else False,
        residue_visible=show_residue,
        passive_packet_ref_count=len(passive_refs),
        causal_post_invocation_ref_count=len(causal_refs),
        events=events,
    )


def _frame(
    payload: dict[str, Any],
    *,
    step_index: int,
    step_id: str,
    title_ru: str,
    explanation_ru: str,
    event_kind: str,
    phase_refs: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    basis: PresentationBasis = PresentationBasis.INFERRED_SUMMARY,
    public_status: str = "inferred_from_stage5_summary",
    reveal_a: bool = False,
    reveal_claim: bool = False,
    show_offer: bool = False,
    show_affordance: bool = False,
    show_request: bool = False,
    show_invocation: bool = False,
    show_result: bool = False,
    show_completion: bool = False,
    show_residue: bool = False,
) -> PresentationFrame:
    return PresentationFrame(
        step_index=step_index,
        step_id=step_id,
        title_ru=title_ru,
        explanation_ru=explanation_ru,
        event_kind=event_kind,
        chamber_state=_chamber_state(
            payload,
            reveal_a=reveal_a,
            reveal_claim=reveal_claim,
            show_offer=show_offer,
            show_affordance=show_affordance,
            show_request=show_request,
            show_invocation=show_invocation,
            show_result=show_result,
            show_completion=show_completion,
            show_residue=show_residue,
        ),
        phase_refs=phase_refs,
        evidence_refs=evidence_refs,
        basis=basis,
        public_status=public_status,
    )


def build_playback_trace(payload: dict[str, Any]) -> PlaybackTrace:
    selection = payload.get("selection_record", {}) or {}
    request = payload.get("affordance_use_request", {}) or {}
    envelope = payload.get("world_actuator_envelope", {}) or {}
    episode = payload.get("episode_record", {}) or {}

    offer = bool(selection.get("response_candidate_ref"))
    selected = _enum_or_raw(selection.get("selection_status")) == "selected_for_invocation_request"
    request_created = bool(request.get("selected_affordance_ref"))
    invoked = bool(envelope.get("invoked", False))
    transfer_result = str(payload.get("transfer_result", "unknown"))
    result_available = transfer_result not in {"not_attempted", "unknown", "None"}
    completion = bool(episode.get("completion_claim", False))
    residue = "residue" in str(episode.get("residue_status", ""))
    causal_refs = tuple(str(ref) for ref in episode.get("causal_post_invocation_refs", []) or [])
    passive_refs = tuple(str(ref) for ref in episode.get("passive_packet_refs", []) or [])

    frames = (
        _frame(
            payload,
            step_index=1,
            step_id="scenario_loaded",
            title_ru="Сценарий загружен",
            explanation_ru="Загружена символическая камера: A, scripted B, стена и апертура.",
            event_kind="initial",
            evidence_refs=(f"scenario:{payload.get('scenario_id')}",),
            basis=PresentationBasis.DIRECT_TRACE,
            public_status="trace_derived",
        ),
        _frame(
            payload,
            step_index=2,
            step_id="a_self_state_available",
            title_ru="Self-state A показан",
            explanation_ru="A имеет дефицит воды и профицит еды как self-state, но это не разрешение.",
            event_kind="self_state",
            reveal_a=True,
        ),
        _frame(
            payload,
            step_index=3,
            step_id="b_visible_claim_received",
            title_ru="B отправляет видимое заявление",
            explanation_ru="B сообщает ресурсные claims; GUI показывает их как claims, не факты.",
            event_kind="counterpart_claim",
            reveal_a=True,
            reveal_claim=True,
            basis=PresentationBasis.DIRECT_TRACE,
            public_status="trace_derived",
            evidence_refs=tuple(
                str(packet.get("packet_id"))
                for packet in payload.get("visible_packets", []) or []
                if packet.get("source_authority") == "counterpart_claim"
            ),
        ),
        _frame(
            payload,
            step_index=4,
            step_id="w01_world_packet_admitted",
            title_ru="W01: claim/fact discipline",
            explanation_ru="Пакет принят как видимый сигнал; claim B не превращён в факт.",
            event_kind="w01",
            reveal_a=True,
            reveal_claim=True,
            phase_refs=_phase_refs(payload, "W01"),
            basis=PresentationBasis.DIRECT_TRACE if _phase_refs(payload, "W01") else PresentationBasis.NOT_EXPOSED,
            public_status="trace_derived" if _phase_refs(payload, "W01") else "not_exposed",
        ),
        _frame(
            payload,
            step_index=5,
            step_id="w02_regularities_checked",
            title_ru="W02: regularity boundary",
            explanation_ru="Регулярность и prior показываются только как bounded support, не как truth oracle.",
            event_kind="w02",
            reveal_a=True,
            reveal_claim=True,
            phase_refs=_phase_refs(payload, "W02"),
            public_status="trace_derived" if _phase_refs(payload, "W02") else "not_exposed",
        ),
        _frame(
            payload,
            step_index=6,
            step_id="w03_prior_or_schema_boundary_checked",
            title_ru="W03: prior/schema boundary",
            explanation_ru="Prior/schema показывается как ограниченная поддержка, не как универсальная trade-схема.",
            event_kind="w03",
            reveal_a=True,
            reveal_claim=True,
            phase_refs=_phase_refs(payload, "W03"),
            public_status="trace_derived" if _phase_refs(payload, "W03") else "not_exposed",
        ),
        _frame(
            payload,
            step_index=7,
            step_id="w04_applicability_checked",
            title_ru="W04: применимость проверена",
            explanation_ru="Aperture/permission проверены отдельно от действия.",
            event_kind="w04",
            reveal_a=True,
            reveal_claim=True,
            phase_refs=_phase_refs(payload, "W04"),
            public_status="blocked" if str(selection.get("permission_status")) == "blocked" else "trace_derived",
        ),
        _frame(
            payload,
            step_index=8,
            step_id="w05_prediction_permission_separation_checked",
            title_ru="W05: прогноз не равен разрешению",
            explanation_ru="Желаемое, предсказанное, наблюдаемое и разрешённое остаются разделёнными.",
            event_kind="w05",
            reveal_a=True,
            reveal_claim=True,
            phase_refs=_phase_refs(payload, "W05"),
            public_status="trace_derived" if _phase_refs(payload, "W05") else "not_exposed",
        ),
        _frame(
            payload,
            step_index=9,
            step_id="w06_revision_residue_checked",
            title_ru="W06: residue/revalidation",
            explanation_ru="Ошибка или блокировка сохраняют residue; correction candidate не исполняется.",
            event_kind="w06",
            reveal_a=True,
            reveal_claim=True,
            show_residue=residue,
            phase_refs=_phase_refs(payload, "W06"),
            public_status="trace_derived" if _phase_refs(payload, "W06") else "not_exposed",
        ),
        _frame(
            payload,
            step_index=10,
            step_id="response_candidate_evaluated",
            title_ru="Кандидат предложения",
            explanation_ru="Offer candidate может появиться, но он не выполняет передачу.",
            event_kind="offer_candidate",
            reveal_a=True,
            reveal_claim=True,
            show_offer=offer,
            public_status="verified" if offer else "blocked",
            evidence_refs=(str(selection.get("response_candidate_ref")),) if offer else (),
        ),
        _frame(
            payload,
            step_index=11,
            step_id="affordance_selected_or_rejected",
            title_ru="Выбор affordance",
            explanation_ru="External aperture transfer выбирается или отклоняется как harness-level affordance.",
            event_kind="affordance_selection",
            reveal_a=True,
            reveal_claim=True,
            show_offer=offer,
            show_affordance=selected,
            public_status="verified" if selected else "blocked",
            evidence_refs=(str(selection.get("selected_affordance_id")),) if selected else (),
        ),
        _frame(
            payload,
            step_index=12,
            step_id="invocation_request_created_or_blocked",
            title_ru="Invocation request",
            explanation_ru="Запрос создан как request к внешнему исполнителю; это ещё не world execution.",
            event_kind="invocation_request",
            reveal_a=True,
            reveal_claim=True,
            show_offer=offer,
            show_affordance=selected,
            show_request=request_created,
            public_status="verified" if request_created else "blocked",
            evidence_refs=(str(request.get("request_id")),) if request_created else (),
        ),
        _frame(
            payload,
            step_index=13,
            step_id="world_actuator_invoked_or_not",
            title_ru="Вызов внешнего исполнителя",
            explanation_ru="World actuator вызывается только при explicit execution flag и valid request.",
            event_kind="world_actuator",
            reveal_a=True,
            reveal_claim=True,
            show_offer=offer,
            show_affordance=selected,
            show_request=request_created,
            show_invocation=invoked,
            public_status="verified" if invoked else "skipped",
            evidence_refs=tuple(
                ref
                for ref in (envelope.get("invocation_id"), envelope.get("attempt_id"))
                if ref
            ),
        ),
        _frame(
            payload,
            step_index=14,
            step_id="transfer_result_observed",
            title_ru="Результат переноса",
            explanation_ru="Результат показывается отдельно от completion; passive и causal refs разделены.",
            event_kind="transfer_result",
            reveal_a=True,
            reveal_claim=True,
            show_offer=offer,
            show_affordance=selected,
            show_request=request_created,
            show_invocation=invoked,
            show_result=result_available or bool(passive_refs),
            public_status="verified" if transfer_result == "succeeded" else ("failed" if transfer_result.startswith("failed") else "skipped"),
            evidence_refs=causal_refs if causal_refs else passive_refs,
        ),
        _frame(
            payload,
            step_index=15,
            step_id="completion_verified_or_rejected",
            title_ru="Проверка завершения",
            explanation_ru="Completion true только при полной verified chain; transfer result не oracle.",
            event_kind="completion",
            reveal_a=True,
            reveal_claim=True,
            show_offer=offer,
            show_affordance=selected,
            show_request=request_created,
            show_invocation=invoked,
            show_result=result_available or bool(passive_refs),
            show_completion=True,
            show_residue=residue,
            public_status="verified" if completion else "blocked",
            evidence_refs=causal_refs,
        ),
        _frame(
            payload,
            step_index=16,
            step_id="final_claim_boundary",
            title_ru="Граница claim",
            explanation_ru="GUI показывает symbolic harness trace и не claim’ит автономную торговлю или motor control.",
            event_kind="claim_boundary",
            reveal_a=True,
            reveal_claim=True,
            show_offer=offer,
            show_affordance=selected,
            show_request=request_created,
            show_invocation=invoked,
            show_result=result_available or bool(passive_refs),
            show_completion=True,
            show_residue=residue,
            public_status="verified" if not completion or completion else "blocked",
            evidence_refs=tuple(str(item) for item in payload.get("claim_boundary", []) or ()),
        ),
    )

    return PlaybackTrace(
        scenario_id=str(payload.get("scenario_id", "")),
        execute_world_actuator=bool(envelope.get("explicit_execution_flag", False)),
        frames=frames,
    )
