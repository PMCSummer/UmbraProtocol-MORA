from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from typing import Callable

from substrate.ksurf1_knowledge_affordance_surface import (
    KnowledgeSurfaceValidationResult,
    build_knowledge_affordance_frame,
    encyclopedia_locked_slot_fixture,
    encyclopedia_partial_unlock_fixture,
    hidden_provider_blocked_fixture,
    jei_index_hint_fixture,
    machine_status_hint_fixture,
    manual_claim_fixture,
    provider_conflict_fixture,
    quest_objective_hint_fixture,
    scanner_candidate_fixture,
    stale_lossy_provider_fixture,
)


def _case_jei_hint_not_recipe_truth():
    return jei_index_hint_fixture()


def _case_encyclopedia_locked_slot():
    return encyclopedia_locked_slot_fixture()


def _case_encyclopedia_partial_unlock():
    return encyclopedia_partial_unlock_fixture()


def _case_quest_objective_hint():
    return quest_objective_hint_fixture()


def _case_machine_status_hint():
    return machine_status_hint_fixture()


def _case_scanner_candidate_hint():
    return scanner_candidate_fixture()


def _case_manual_claim_hint():
    return manual_claim_fixture()


def _case_provider_conflict():
    return provider_conflict_fixture()


def _case_hidden_provider_blocked():
    return hidden_provider_blocked_fixture()


def _case_stale_lossy_provider():
    return stale_lossy_provider_fixture()


def _case_provider_truth_rejected():
    src = manual_claim_fixture()
    bad_claim = replace(src.provider_claim_refs[0], authority_marker="truth")
    return replace(src, provider_claim_refs=(bad_claim,))


def _case_provider_value_rejected():
    src = manual_claim_fixture()
    bad_provider = replace(src.provider_refs[0], metadata={"rarity": "legendary"})
    return replace(src, provider_refs=(bad_provider,))


CASES: dict[str, Callable[[], object]] = {
    "jei_hint_not_recipe_truth": _case_jei_hint_not_recipe_truth,
    "encyclopedia_locked_slot": _case_encyclopedia_locked_slot,
    "encyclopedia_partial_unlock": _case_encyclopedia_partial_unlock,
    "quest_objective_hint": _case_quest_objective_hint,
    "machine_status_hint": _case_machine_status_hint,
    "scanner_candidate_hint": _case_scanner_candidate_hint,
    "manual_claim_hint": _case_manual_claim_hint,
    "provider_conflict": _case_provider_conflict,
    "hidden_provider_blocked": _case_hidden_provider_blocked,
    "stale_lossy_provider": _case_stale_lossy_provider,
    "provider_truth_rejected": _case_provider_truth_rejected,
    "provider_value_rejected": _case_provider_value_rejected,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="K-SURF1 knowledge affordance demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-providers", action="store_true")
    parser.add_argument("--show-slots", action="store_true")
    parser.add_argument("--show-conflicts", action="store_true")
    parser.add_argument("--show-authority", action="store_true")
    parser.add_argument("--show-blocked", action="store_true")
    parser.add_argument("--show-counters", action="store_true")
    return parser


def _payload(case_id: str, result: KnowledgeSurfaceValidationResult) -> dict[str, object]:
    frame = result.frame
    return {
        "case_id": case_id,
        "validation_status": result.status.value,
        "provider_count": result.counters.provider_count,
        "hint_count": result.counters.hint_count,
        "locked_slot_count": result.counters.locked_slot_count,
        "partial_slot_count": result.counters.partial_slot_count,
        "conflict_count": result.counters.conflict_count,
        "blocked_reasons": result.blocked_reasons,
        "authority_flags": asdict(result.authority_flags),
        "action_request_emitted": frame.action_request_emitted if frame else False,
        "action_selected": frame.action_selected if frame else False,
        "goal_selected": frame.goal_selected if frame else False,
        "fact_claimed": frame.fact_claimed if frame else False,
        "cause_confirmed": frame.cause_confirmed if frame else False,
        "value_assigned": frame.value_assigned if frame else False,
        "mature_recipe_claimed": frame.mature_recipe_claimed if frame else False,
        "mature_skill_claimed": frame.mature_skill_claimed if frame else False,
        "automation_claimed": frame.automation_claimed if frame else False,
        "bounded_claim": "K-SURF1 produces source-bound non-authoritative knowledge hints/slots/conflicts and never creates action authority or truth closure.",
        "_result": result,
    }


def main() -> int:
    args = _parser().parse_args()
    if args.list_cases:
        for case_id in CASES:
            print(case_id)
        return 0

    if not args.case_id or args.case_id not in CASES:
        print("Specify --case with a valid case id or use --list-cases.")
        return 2

    source = CASES[args.case_id]()
    result = build_knowledge_affordance_frame(source)  # type: ignore[arg-type]
    payload = _payload(args.case_id, result)

    frame = result.frame
    if args.show_providers and frame is not None:
        payload["providers"] = frame.provider_refs
    if args.show_slots and frame is not None:
        payload["slots"] = {
            "locked": frame.locked_slot_refs,
            "partial": frame.partial_slot_refs,
        }
    if args.show_conflicts and frame is not None:
        payload["conflicts"] = frame.provider_conflict_refs
    if args.show_authority:
        payload["authority"] = asdict(result.authority_flags)
    if args.show_blocked:
        payload["blocked"] = result.blocked_reasons
    if args.show_counters:
        payload["counters"] = asdict(result.counters)

    payload.pop("_result", None)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.report:
        print(f"case_id: {payload['case_id']}")
        print(f"validation_status: {payload['validation_status']}")
        print(
            "counts: "
            f"providers={payload['provider_count']} hints={payload['hint_count']} "
            f"locked={payload['locked_slot_count']} partial={payload['partial_slot_count']} "
            f"conflicts={payload['conflict_count']}"
        )
        print(f"blocked_reasons: {payload['blocked_reasons']}")
        print(f"authority_flags: {payload['authority_flags']}")
        print(
            "no_claims/action: "
            f"ap01={payload['action_request_emitted']} action={payload['action_selected']} "
            f"goal={payload['goal_selected']} fact={payload['fact_claimed']} cause={payload['cause_confirmed']} "
            f"value={payload['value_assigned']} recipe={payload['mature_recipe_claimed']} "
            f"skill={payload['mature_skill_claimed']} automation={payload['automation_claimed']}"
        )
        if "providers" in payload:
            print(f"providers: {payload['providers']}")
        if "slots" in payload:
            print(f"slots: {payload['slots']}")
        if "conflicts" in payload:
            print(f"conflicts: {payload['conflicts']}")
        if "counters" in payload:
            print(f"counters: {payload['counters']}")
        print(f"bounded_claim: {payload['bounded_claim']}")
        return 0

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
