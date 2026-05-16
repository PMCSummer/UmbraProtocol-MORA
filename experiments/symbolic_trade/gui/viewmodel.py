from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..runner import list_scenarios, run_stage5_affordance_trace, stage5_result_to_dict
from .localization import REQUIRED_RUSSIAN_LABELS, RUSSIAN_UI_STRINGS


@dataclass(frozen=True, slots=True)
class Stage5TimelineStep:
    step_index: int
    step_id: str
    title_ru: str
    short_explanation_ru: str
    status: str
    evidence_refs: tuple[str, ...]
    public_payload_summary: str
    hidden_or_eval_excluded: bool
    is_decision_bearing: bool
    claim_boundary_note_ru: str


@dataclass(slots=True)
class Stage5TimelineState:
    steps: tuple[Stage5TimelineStep, ...]
    current_step_index: int = 0
    play_state: str = "paused"

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def current_step(self) -> Stage5TimelineStep:
        if not self.steps:
            raise IndexError("Timeline has no steps")
        return self.steps[self.current_step_index]

    @property
    def can_go_next(self) -> bool:
        return self.current_step_index < max(0, self.step_count - 1)

    @property
    def can_go_previous(self) -> bool:
        return self.current_step_index > 0

    def go_next(self) -> None:
        if self.can_go_next:
            self.current_step_index += 1

    def go_previous(self) -> None:
        if self.can_go_previous:
            self.current_step_index -= 1

    def go_first(self) -> None:
        self.current_step_index = 0

    def go_last(self) -> None:
        if self.step_count:
            self.current_step_index = self.step_count - 1

    def reset_timeline(self) -> None:
        self.current_step_index = 0
        self.play_state = "paused"

    def set_step(self, index: int) -> None:
        if not self.step_count:
            self.current_step_index = 0
            return
        self.current_step_index = min(max(0, index), self.step_count - 1)


@dataclass(slots=True)
class Stage5GuiViewModel:
    scenario_id: str
    execute_world_actuator: bool
    readiness_status: str
    offer_candidate_emitted: bool
    affordance_selection_status: str
    invocation_request_created: bool
    world_actuator_invoked: bool
    transfer_result: str
    completion_claim: bool
    verification_status: str
    residue_status: str
    passive_packet_ref_count: int
    causal_post_invocation_ref_count: int
    phase_coverage_evidence: tuple[str, ...]
    anti_shortcut_items: tuple[dict[str, Any], ...]
    causal_spine_items: tuple[dict[str, str], ...]
    scene_items: tuple[dict[str, Any], ...]
    result_items: tuple[dict[str, Any], ...]
    compare_items: tuple[dict[str, str], ...]
    timeline_state: Stage5TimelineState
    developer_payload: dict[str, Any] = field(default_factory=dict)

    @property
    def current_step(self) -> Stage5TimelineStep:
        return self.timeline_state.current_step

    @property
    def current_step_index(self) -> int:
        return self.timeline_state.current_step_index

    @property
    def step_count(self) -> int:
        return self.timeline_state.step_count

    @property
    def can_go_next(self) -> bool:
        return self.timeline_state.can_go_next

    @property
    def can_go_previous(self) -> bool:
        return self.timeline_state.can_go_previous

    @property
    def play_state(self) -> str:
        return self.timeline_state.play_state

    def set_play_state(self, value: str) -> None:
        self.timeline_state.play_state = value

    def go_next(self) -> None:
        self.timeline_state.go_next()

    def go_previous(self) -> None:
        self.timeline_state.go_previous()

    def go_first(self) -> None:
        self.timeline_state.go_first()

    def go_last(self) -> None:
        self.timeline_state.go_last()

    def reset_timeline(self) -> None:
        self.timeline_state.reset_timeline()

    def set_step(self, index: int) -> None:
        self.timeline_state.set_step(index)


def list_stage5_gui_scenarios() -> tuple[str, ...]:
    return list_scenarios()


def run_stage5_gui_payload(
    scenario_id: str,
    *,
    execute_world_actuator: bool = False,
    include_eval_only: bool = False,
    include_ledger: bool = True,
    include_records: bool = True,
) -> dict[str, Any]:
    trace = run_stage5_affordance_trace(
        scenario_id,
        include_falsifiers=True,
        include_eval_only=include_eval_only,
        execute_world_actuator=execute_world_actuator,
    )
    return stage5_result_to_dict(
        trace,
        include_eval_only=include_eval_only,
        include_affordance_records=include_records,
        include_affordance_ledger=include_ledger,
    )


def _falsifier_status(payload: dict[str, Any], name: str) -> bool:
    for item in payload.get("falsifier_summary", []):
        if item.get("name") == name:
            return bool(item.get("passed"))
    return False


def _anti_shortcut_items(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    checks = [
        (REQUIRED_RUSSIAN_LABELS[0], "stage5_hidden_inventory_used_in_affordance_decision"),
        (REQUIRED_RUSSIAN_LABELS[1], "stage5_b_claim_as_fact"),
        (REQUIRED_RUSSIAN_LABELS[2], "stage5_a_deficit_as_permission"),
        (REQUIRED_RUSSIAN_LABELS[3], "stage5_a_surplus_as_auto_offer"),
        (REQUIRED_RUSSIAN_LABELS[4], "stage5_invocation_request_as_execution"),
        (REQUIRED_RUSSIAN_LABELS[5], "stage5_execution_without_explicit_actuator_flag"),
        (REQUIRED_RUSSIAN_LABELS[6], "stage5_passive_packet_as_causal_response"),
        (REQUIRED_RUSSIAN_LABELS[7], "stage5_transfer_result_as_completion_oracle"),
        (REQUIRED_RUSSIAN_LABELS[8], "stage5_w06_revision_executed"),
        (REQUIRED_RUSSIAN_LABELS[9], "stage5_core_contamination"),
        (REQUIRED_RUSSIAN_LABELS[10], "stage5_eval_only_used_in_affordance_decision"),
    ]
    return tuple(
        {
            "label_ru": label,
            "passed": _falsifier_status(payload, falsifier_name),
            "falsifier_name": falsifier_name,
        }
        for label, falsifier_name in checks
    )


def _status_ru(status: str) -> str:
    status_map = {
        "sufficient_for_bounded_offer": "готовность достаточна",
        "clarification_required": "нужно уточнение",
        "revalidation_required": "нужна перепроверка",
        "blocked": "заблокировано",
        "observe_only": "только наблюдение",
        "abstain": "воздержаться",
        "not_attempted": RUSSIAN_UI_STRINGS["status_not_attempted"],
        "succeeded": RUSSIAN_UI_STRINGS["status_succeeded"],
        "failed_unknown": RUSSIAN_UI_STRINGS["status_failed"],
        "failed_blocked": RUSSIAN_UI_STRINGS["status_failed"],
        "verified": RUSSIAN_UI_STRINGS["status_verified"],
        "unverified": RUSSIAN_UI_STRINGS["status_unverified"],
        "trace_derived": RUSSIAN_UI_STRINGS["status_trace_derived"],
        "inferred_from_stage5_summary": RUSSIAN_UI_STRINGS["status_inferred"],
        "not_exposed": RUSSIAN_UI_STRINGS["status_not_exposed"],
        "skipped": RUSSIAN_UI_STRINGS["status_skipped"],
        "failed": RUSSIAN_UI_STRINGS["status_failed"],
        "missing": RUSSIAN_UI_STRINGS["status_missing"],
    }
    return status_map.get(status, status)


def _enum_or_raw(value: Any) -> Any:
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, str) and "." in value:
        return value.rsplit(".", 1)[-1].lower()
    return value


def _phase_codes(payload: dict[str, Any]) -> set[str]:
    return {str(item).split(":", 1)[0] for item in payload.get("phase_coverage_evidence", [])}


def _phase_status_code(phase: str, payload: dict[str, Any]) -> str:
    phase_codes = _phase_codes(payload)
    selection = payload.get("selection_record", {})
    episode = payload.get("episode_record", {})

    if phase == "W04":
        permission = str(selection.get("permission_status", "unknown"))
        if permission == "blocked":
            return "blocked"
        if phase in phase_codes:
            return "trace_derived"
        return "missing"
    if phase == "W06":
        residue = str(episode.get("residue_status", ""))
        if "residue" in residue:
            return "trace_derived"
        if phase in phase_codes:
            return "inferred_from_stage5_summary"
        return "missing"

    if phase in phase_codes:
        return "trace_derived"
    return "missing"


def _causal_spine(payload: dict[str, Any]) -> tuple[dict[str, str], ...]:
    sel = payload.get("selection_record", {})
    env = payload.get("world_actuator_envelope", {})
    ep = payload.get("episode_record", {})
    return (
        {
            "phase": "W01",
            "label_ru": "Вход принят / отклонён",
            "status": _phase_status_code("W01", payload),
            "status_ru": _status_ru(_phase_status_code("W01", payload)),
        },
        {
            "phase": "W02",
            "label_ru": "Повторяемость / регулярность",
            "status": _phase_status_code("W02", payload),
            "status_ru": _status_ru(_phase_status_code("W02", payload)),
        },
        {
            "phase": "W03",
            "label_ru": "Ограниченный prior",
            "status": _phase_status_code("W03", payload),
            "status_ru": _status_ru(_phase_status_code("W03", payload)),
        },
        {
            "phase": "W04",
            "label_ru": "Применимость / запрет / уточнение",
            "status": _phase_status_code("W04", payload),
            "status_ru": _status_ru(_phase_status_code("W04", payload)),
        },
        {
            "phase": "W05",
            "label_ru": "Желаемое ≠ наблюдаемое ≠ разрешённое",
            "status": _phase_status_code("W05", payload),
            "status_ru": _status_ru(_phase_status_code("W05", payload)),
        },
        {
            "phase": "W06",
            "label_ru": "Последствие ошибки / residue",
            "status": _phase_status_code("W06", payload),
            "status_ru": _status_ru(_phase_status_code("W06", payload)),
        },
        {
            "phase": "Response",
            "label_ru": "Кандидат ответа",
            "status": "verified" if bool(sel.get("response_candidate_ref")) else "blocked",
            "status_ru": "есть" if bool(sel.get("response_candidate_ref")) else "нет",
        },
        {
            "phase": "Affordance",
            "label_ru": "Выбор возможности действия",
            "status": "verified" if str(_enum_or_raw(sel.get("selection_status", ""))) == "selected_for_invocation_request" else "blocked",
            "status_ru": str(_enum_or_raw(sel.get("selection_status", "unknown"))),
        },
        {
            "phase": "Actuator",
            "label_ru": "Вызов внешнего исполнителя",
            "status": "verified" if env.get("invoked") else "skipped",
            "status_ru": "вызван" if env.get("invoked") else "не вызван",
        },
        {
            "phase": "Verification",
            "label_ru": "Проверка результата",
            "status": "verified" if ep.get("verification_status") == "verified" else "unverified",
            "status_ru": _status_ru(str(ep.get("verification_status", "unknown"))),
        },
    )


def _timeline_step(
    index: int,
    step_id: str,
    title_ru: str,
    short_explanation_ru: str,
    status: str,
    evidence_refs: tuple[str, ...],
    public_payload_summary: str,
    is_decision_bearing: bool,
    claim_boundary_note_ru: str,
) -> Stage5TimelineStep:
    return Stage5TimelineStep(
        step_index=index,
        step_id=step_id,
        title_ru=title_ru,
        short_explanation_ru=short_explanation_ru,
        status=status,
        evidence_refs=evidence_refs,
        public_payload_summary=public_payload_summary,
        hidden_or_eval_excluded=True,
        is_decision_bearing=is_decision_bearing,
        claim_boundary_note_ru=claim_boundary_note_ru,
    )


def _timeline_from_payload(payload: dict[str, Any]) -> Stage5TimelineState:
    selection = payload.get("selection_record", {})
    request = payload.get("affordance_use_request", {})
    envelope = payload.get("world_actuator_envelope", {})
    episode = payload.get("episode_record", {})
    visible_packets = payload.get("visible_packets", [])

    phase_codes = _phase_codes(payload)
    claim_packets = tuple(
        str(item.get("packet_id"))
        for item in visible_packets
        if item.get("source_authority") == "counterpart_claim"
    )
    passive_refs = tuple(str(item) for item in episode.get("passive_packet_refs", []) or [])
    causal_refs = tuple(str(item) for item in episode.get("causal_post_invocation_refs", []) or [])
    completion_missing = tuple(str(item) for item in episode.get("completion_basis_missing", []) or [])

    steps = (
        _timeline_step(
            1,
            "scenario_loaded",
            "Сценарий загружен",
            "Пакеты сценария и режим запуска загружены в презентационный слой.",
            "trace_derived" if payload.get("scenario_id") else "missing",
            (f"scenario:{payload.get('scenario_id')}",),
            "Сценарий выбран и данные Stage 5 доступны.",
            False,
            "Только загрузка данных, без когнитивного вывода.",
        ),
        _timeline_step(
            2,
            "a_self_state_available",
            "Self-state A доступен",
            "GUI использует только сводки Stage 5 о self-state, без прямого вычисления потребностей.",
            "inferred_from_stage5_summary" if selection.get("permission_status") else "not_exposed",
            ("selection_record.permission_status",),
            f"readiness={selection.get('permission_status')}",
            True,
            "Дефицит/профицит A не являются автоматическим разрешением.",
        ),
        _timeline_step(
            3,
            "b_visible_claim_received",
            "Видимое заявление B принято как claim",
            "Сигнал B учитывается как заявление, а не как установленный факт.",
            "trace_derived" if claim_packets else "not_exposed",
            claim_packets,
            f"visible_claim_packets={len(claim_packets)}",
            True,
            "Claim/fact разделение сохраняется.",
        ),
        _timeline_step(
            4,
            "w01_world_packet_admitted",
            "W01: допуск world packet",
            "Проверка наличия trace-следа W01.",
            "trace_derived" if "W01" in phase_codes else "missing",
            tuple(ref for ref in payload.get("phase_coverage_evidence", []) if str(ref).startswith("W01:")),
            "Есть ли W01-след в evidence.",
            True,
            "Наличие следа не означает truth laundering.",
        ),
        _timeline_step(
            5,
            "w02_regularities_checked",
            "W02: регулярности проверены",
            "Показывается только наличие/отсутствие следа W02 в trace.",
            "trace_derived" if "W02" in phase_codes else "not_exposed",
            tuple(ref for ref in payload.get("phase_coverage_evidence", []) if str(ref).startswith("W02:")),
            "GUI не доказывает устойчивую модель мира.",
            True,
            "Регулярность не превращается в факт по одному событию.",
        ),
        _timeline_step(
            6,
            "w03_prior_or_schema_boundary_checked",
            "W03: границы prior/schema",
            "Показывается наличие следа W03 и граница bounded prior.",
            "trace_derived" if "W03" in phase_codes else "not_exposed",
            tuple(ref for ref in payload.get("phase_coverage_evidence", []) if str(ref).startswith("W03:")),
            "Схема ограничена, не универсальна.",
            True,
            "Нет прямого trade-oracle вывода.",
        ),
        _timeline_step(
            7,
            "w04_applicability_checked",
            "W04: применимость/запрет",
            "Слой применимости отделён от действия.",
            _phase_status_code("W04", payload),
            tuple(ref for ref in payload.get("phase_coverage_evidence", []) if str(ref).startswith("W04:")),
            f"permission_status={selection.get('permission_status')}",
            True,
            "W04 не является selector исполнения.",
        ),
        _timeline_step(
            8,
            "w05_prediction_permission_separation_checked",
            "W05: desired/predicted/permitted разделены",
            "Показывается trace-сигнал разделения прогноз/разрешение.",
            "trace_derived" if "W05" in phase_codes else "not_exposed",
            tuple(ref for ref in payload.get("phase_coverage_evidence", []) if str(ref).startswith("W05:")),
            "Доступность affordance не равна вызову.",
            True,
            "W05 routing не даёт права на исполнение.",
        ),
        _timeline_step(
            9,
            "w06_revision_residue_checked",
            "W06: residue/revalidation",
            "Показывается сохранение residue и запрет executed correction.",
            _phase_status_code("W06", payload),
            tuple(ref for ref in payload.get("phase_coverage_evidence", []) if str(ref).startswith("W06:")),
            f"residue_status={episode.get('residue_status')}",
            True,
            "Correction candidate не исполняется.",
        ),
        _timeline_step(
            10,
            "response_candidate_evaluated",
            "Кандидат ответа оценён",
            "Offer candidate отделён от исполнения передачи.",
            "verified" if bool(selection.get("response_candidate_ref")) else "blocked",
            (str(selection.get("response_candidate_ref")),) if selection.get("response_candidate_ref") else (),
            f"offer_candidate={bool(selection.get('response_candidate_ref'))}",
            True,
            "Offer candidate не исполняет transfer напрямую.",
        ),
        _timeline_step(
            11,
            "affordance_selected_or_rejected",
            "Affordance выбрана или отклонена",
            "Выбор affordance отделён от invocate/execute этапов.",
            "verified" if str(_enum_or_raw(selection.get("selection_status"))) == "selected_for_invocation_request" else "blocked",
            (str(selection.get("selected_affordance_id")),) if selection.get("selected_affordance_id") else (),
            f"selection_status={_enum_or_raw(selection.get('selection_status'))}",
            True,
            "Доступная affordance не равна invoked.",
        ),
        _timeline_step(
            12,
            "invocation_request_created_or_blocked",
            "Создание invocation request",
            "Request отделён от world execution.",
            "verified" if bool(request.get("selected_affordance_ref")) else "blocked",
            (str(request.get("request_id")),) if request.get("request_id") else (),
            f"request_valid={request.get('request_valid')}",
            True,
            "Запрос не является фактом исполнения.",
        ),
        _timeline_step(
            13,
            "world_actuator_invoked_or_not",
            "Вызов внешнего исполнителя",
            "Вызов возможен только при explicit execution flag и валидном request.",
            "verified" if bool(envelope.get("invoked")) else "skipped",
            tuple(item for item in (envelope.get("invocation_id"), envelope.get("attempt_id")) if item),
            f"invoked={envelope.get('invoked')} explicit_flag={envelope.get('explicit_execution_flag')}",
            True,
            "Subject motor-control claim не формируется.",
        ),
        _timeline_step(
            14,
            "transfer_result_observed",
            "Результат передачи наблюдён",
            "Результат отделён от completion oracle.",
            "verified" if payload.get("transfer_result") == "succeeded" else ("failed" if payload.get("transfer_result") not in {None, "not_attempted"} else "skipped"),
            tuple(causal_refs),
            f"transfer_result={payload.get('transfer_result')} passive={len(passive_refs)} causal={len(causal_refs)}",
            True,
            "Один transfer_result не доказывает завершение.",
        ),
        _timeline_step(
            15,
            "completion_verified_or_rejected",
            "Проверка завершения эпизода",
            "Completion true только при полной цепочке верификации.",
            "verified" if bool(episode.get("completion_claim")) else "blocked",
            tuple(item for item in completion_missing if item),
            f"completion_claim={episode.get('completion_claim')} verification={episode.get('verification_status')}",
            True,
            "Completion claim не строится из transfer_result в одиночку.",
        ),
    )

    return Stage5TimelineState(steps=steps)


def build_stage5_gui_view_model(
    payload: dict[str, Any],
    *,
    dev_mode: bool = False,
    include_eval_only: bool = False,
) -> Stage5GuiViewModel:
    selection = payload.get("selection_record", {})
    request = payload.get("affordance_use_request", {})
    envelope = payload.get("world_actuator_envelope", {})
    episode = payload.get("episode_record", {})
    visible_packets = payload.get("visible_packets", [])

    scene_items = tuple(
        {
            "packet_id": item.get("packet_id"),
            "signal_kind": item.get("signal_kind"),
            "source_authority": item.get("source_authority"),
            "resource_kind": item.get("resource_kind"),
            "reported_level": item.get("reported_level"),
            "claim_not_fact": item.get("claim_not_fact_marker"),
        }
        for item in visible_packets
    )

    completion_basis_missing = list(episode.get("completion_basis_missing", []) or [])
    completion_reason = "-"
    if not bool(episode.get("completion_claim", False)):
        completion_reason = ", ".join(completion_basis_missing) if completion_basis_missing else "нет полной верификационной цепочки"

    result_items = (
        {"label_ru": "Готовность", "value": selection.get("permission_status")},
        {"label_ru": RUSSIAN_UI_STRINGS["offer_candidate"], "value": bool(selection.get("response_candidate_ref"))},
        {"label_ru": RUSSIAN_UI_STRINGS["affordance_selected"], "value": _enum_or_raw(selection.get("selection_status"))},
        {"label_ru": RUSSIAN_UI_STRINGS["invocation_request"], "value": bool(request.get("selected_affordance_ref"))},
        {"label_ru": RUSSIAN_UI_STRINGS["actuator_invoked"], "value": bool(envelope.get("invoked"))},
        {"label_ru": RUSSIAN_UI_STRINGS["result_observed"], "value": payload.get("transfer_result")},
        {"label_ru": RUSSIAN_UI_STRINGS["passive_packets"], "value": len(episode.get("passive_packet_refs", []) or [])},
        {"label_ru": RUSSIAN_UI_STRINGS["causal_packets"], "value": len(episode.get("causal_post_invocation_refs", []) or [])},
        {"label_ru": RUSSIAN_UI_STRINGS["completion_verified_chain"], "value": bool(episode.get("completion_claim"))},
        {"label_ru": RUSSIAN_UI_STRINGS["completion_not_verified_reason"], "value": completion_reason},
        {"label_ru": RUSSIAN_UI_STRINGS["residue_retained"], "value": episode.get("residue_status")},
    )

    compare_items = (
        {"title": RUSSIAN_UI_STRINGS["shortcut_baseline"], "text": RUSSIAN_UI_STRINGS["shortcut_text"]},
        {"title": RUSSIAN_UI_STRINGS["mora_trace"], "text": RUSSIAN_UI_STRINGS["mora_text"]},
    )

    developer_payload = {
        "scenario_id": payload.get("scenario_id"),
        "readiness_status": selection.get("permission_status"),
        "offer_candidate_emitted": bool(selection.get("response_candidate_ref")),
        "affordance_selected": _enum_or_raw(selection.get("selection_status")),
        "invocation_request_created": bool(request.get("selected_affordance_ref")),
        "world_actuator_invoked": envelope.get("invoked"),
        "transfer_result": payload.get("transfer_result"),
        "completion_claim": episode.get("completion_claim"),
        "verification_status": episode.get("verification_status"),
        "passive_packet_refs": episode.get("passive_packet_refs", []),
        "causal_post_invocation_refs": episode.get("causal_post_invocation_refs", []),
        "phase_coverage_evidence": payload.get("phase_coverage_evidence", []),
        "module_responsibility_ledger": payload.get("module_responsibility_ledger", {}),
        "falsifier_summary": payload.get("falsifier_summary", []),
    }
    if dev_mode and include_eval_only and "eval_only" in payload:
        developer_payload["eval_only"] = payload["eval_only"]

    return Stage5GuiViewModel(
        scenario_id=str(payload.get("scenario_id", "")),
        execute_world_actuator=bool(envelope.get("explicit_execution_flag", False)),
        readiness_status=str(selection.get("permission_status", "unknown")),
        offer_candidate_emitted=bool(selection.get("response_candidate_ref")),
        affordance_selection_status=str(_enum_or_raw(selection.get("selection_status", "unknown"))),
        invocation_request_created=bool(request.get("selected_affordance_ref")),
        world_actuator_invoked=bool(envelope.get("invoked", False)),
        transfer_result=str(payload.get("transfer_result", "unknown")),
        completion_claim=bool(episode.get("completion_claim", False)),
        verification_status=str(episode.get("verification_status", "unknown")),
        residue_status=str(episode.get("residue_status", "unknown")),
        passive_packet_ref_count=len(episode.get("passive_packet_refs", []) or []),
        causal_post_invocation_ref_count=len(episode.get("causal_post_invocation_refs", []) or []),
        phase_coverage_evidence=tuple(payload.get("phase_coverage_evidence", []) or []),
        anti_shortcut_items=_anti_shortcut_items(payload),
        causal_spine_items=_causal_spine(payload),
        scene_items=scene_items,
        result_items=result_items,
        compare_items=compare_items,
        timeline_state=_timeline_from_payload(payload),
        developer_payload=developer_payload if dev_mode else {"mode": RUSSIAN_UI_STRINGS["dev_mode_disabled"]},
    )
