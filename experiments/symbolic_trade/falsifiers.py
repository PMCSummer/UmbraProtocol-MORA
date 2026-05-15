from __future__ import annotations

import subprocess
from pathlib import Path

from .models import CounterpartSignalKind, FalsifierResult, SignalAuthority, SubjectVisiblePacket


_FORBIDDEN_SIGNAL_TERMS = ("trade", "offer", "request", "ack", "deal", "bargain", "exchange", "market")
_FORBIDDEN_CORE_PREFIXES = (
    "src/substrate/w01",
    "src/substrate/w02",
    "src/substrate/w03",
    "src/substrate/w04",
    "src/substrate/w05",
    "src/substrate/w06",
    "src/substrate/subject_tick/update.py",
    "src/substrate/subject_tick/policy.py",
    "src/substrate/subject_tick/models.py",
    "src/substrate/runtime_topology/policy.py",
    "src/substrate/runtime_tap_trace.py",
)


def _modified_paths(repo_root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ()
    return tuple(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())


def _contains_any_term(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in _FORBIDDEN_SIGNAL_TERMS)


def _packet_strings(packet: SubjectVisiblePacket) -> tuple[str, ...]:
    return (
        packet.packet_id,
        packet.source_id,
        packet.source_authority.value,
        packet.signal_kind.value,
        packet.resource_kind.value if packet.resource_kind else "",
        packet.reported_level.value if packet.reported_level else "",
        packet.aperture_state.value,
        packet.transfer_outcome.value,
        packet.item_kind.value if packet.item_kind else "",
        " ".join(packet.provenance_ref),
    )


def run_symbolic_trade_falsifiers(result, *, repo_root: Path | None = None) -> tuple[FalsifierResult, ...]:
    packets = result.emitted_packets
    markers = set(result.claim_discipline_markers)
    summary = result.trace_summary

    hidden_leak = any(
        (not packet.hidden_truth_excluded)
        or packet.source_authority in {SignalAuthority.HARNESS_TRUTH, SignalAuthority.INFERRED_BY_HARNESS_FOR_EVAL_ONLY}
        for packet in packets
    )

    shortcut_signal = any(_contains_any_term(packet.signal_kind.value) for packet in packets)

    claim_promoted = any(
        packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM and not packet.claim_not_fact_marker
        for packet in packets
    )

    desired_as_evidence = any(
        "desired_as_evidence" in obligation
        for obligation in result.phase_obligation_summary
    ) or bool(summary.get("desired_used_as_evidence", False))

    oracle_leak = any(
        "mutually_beneficial_trade_possible" in " ".join(_packet_strings(packet))
        for packet in packets
    )

    one_shot_regularization = bool(summary.get("stable_regularities_from_single_claim", False))

    blocked_ignored = (
        any(packet.signal_kind is CounterpartSignalKind.BLOCKED for packet in packets)
        and bool(summary.get("transfer_feasible", False))
    )

    false_claim_laundered = any(
        packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM
        and packet.source_authority is not SignalAuthority.COUNTERPART_CLAIM
        for packet in packets
    )

    noisy_cleaned = (
        any(packet.signal_kind is CounterpartSignalKind.CONTRADICTION for packet in packets)
        and "contradiction_visible_without_cleanup" not in markers
    )

    transfer_as_permission = bool(summary.get("transfer_result_grants_permission", False))

    correction_executed = bool(summary.get("correction_candidate_executed", False))

    changed_paths = _modified_paths(repo_root or Path(__file__).resolve().parents[2])
    core_modified = any(
        any(path.startswith(prefix) for prefix in _FORBIDDEN_CORE_PREFIXES)
        for path in changed_paths
    )

    return (
        FalsifierResult("hidden_state_leakage", not hidden_leak, "hidden truth leaked" if hidden_leak else "ok"),
        FalsifierResult("trade_specific_shortcut_signal", not shortcut_signal, "forbidden trade-like signal detected" if shortcut_signal else "ok"),
        FalsifierResult("claim_promoted_to_fact", not claim_promoted, "counterpart claim promoted to fact" if claim_promoted else "ok"),
        FalsifierResult("desired_as_evidence", not desired_as_evidence, "desired state encoded as evidence" if desired_as_evidence else "ok"),
        FalsifierResult("mutual_benefit_oracle_leak", not oracle_leak, "eval-only oracle leaked into subject packets" if oracle_leak else "ok"),
        FalsifierResult("one_shot_regularization", not one_shot_regularization, "one-shot claim regularized" if one_shot_regularization else "ok"),
        FalsifierResult("blocked_aperture_ignored", not blocked_ignored, "blocked aperture still marked feasible" if blocked_ignored else "ok"),
        FalsifierResult("false_claim_truth_laundering", not false_claim_laundered, "claim laundered as observed fact" if false_claim_laundered else "ok"),
        FalsifierResult("noisy_signal_cleaned", not noisy_cleaned, "noisy contradiction cleaned to stable claim" if noisy_cleaned else "ok"),
        FalsifierResult("transfer_result_as_permission", not transfer_as_permission, "transfer result converted to permission" if transfer_as_permission else "ok"),
        FalsifierResult("correction_candidate_executed", not correction_executed, "correction candidate treated as executed" if correction_executed else "ok"),
        FalsifierResult("phase_core_modification", not core_modified, "forbidden core files modified" if core_modified else "ok"),
    )
