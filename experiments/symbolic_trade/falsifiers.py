from __future__ import annotations

from dataclasses import asdict
import subprocess
from pathlib import Path

from .clarification_policy import ClarificationRoute, MissingInformationKind, ResponseReadinessStatus
from .models import CounterpartSignalKind, FalsifierResult, SignalAuthority, SubjectVisiblePacket, TransferOutcome
from .transfer_affordance import TransferAffordanceStatus


_FORBIDDEN_SIGNAL_TERMS = ("trade", "offer", "request", "ack", "deal", "bargain", "exchange", "market")
_FORBIDDEN_CORE_PREFIXES = (
    "src/substrate/w01",
    "src/substrate/w02",
    "src/substrate/w03",
    "src/substrate/w04",
    "src/substrate/w05",
    "src/substrate/w06",
    "src/substrate/subject_tick/",
    "src/substrate/runtime_topology/policy.py",
    "src/substrate/runtime_tap_trace.py",
)
_DESIRED_MARKER_TERMS = ("desired_state", "desired_outcome", "requested_outcome", "goal_target", "goal_state")
_FORBIDDEN_PHASE_SHORTCUT_TERMS = (
    "trade_intent:true",
    "wants_trade:true",
    "mutual_benefit_oracle:true",
    "deal_success_signal",
    "barter_success_signal",
    "should_trade:true",
)
_FORBIDDEN_STAGE25_KEY_TOKENS = (
    "harness_truth",
    "hidden_truth",
    "true_inventory",
    "b_true_inventory",
    "true_need_surplus_pairing",
    "mutual_benefit_oracle",
    "success_labels",
    "expected_success_label",
)
_FORBIDDEN_STAGE25_VALUE_TOKENS = (
    "mutually_beneficial_trade_possible_eval_only",
    "potential_reciprocity_eval_only",
    "true_need_surplus_pairing",
    "mutual_benefit_oracle:true",
    "should_trade:true",
    "wants_trade:true",
    "trade_intent:true",
    "trade_offer:true",
)
_FORBIDDEN_STAGE25_PATH_VALUE_TOKENS = (
    ("reason_codes", "mutual_benefit_oracle"),
    ("reason_codes", "should_trade:true"),
    ("reason_codes", "trade_offer:true"),
    ("downstream_permission_delta", "should_trade:true"),
    ("downstream_permission_delta", "wants_trade:true"),
    ("downstream_permission_delta", "trade_intent:true"),
    ("output_refs", "true_need_surplus_pairing"),
)
_FORBIDDEN_STAGE3_ORACLE_TOKENS = (
    "mutual_benefit_oracle",
    "oracle",
    "true_need_surplus_pairing",
    "eval_only_success_label",
    "harness_truth",
)
_FORBIDDEN_STAGE3_SHORTCUT_TERMS = (
    "trade_intent",
    "should_trade",
    "mutual_benefit_detected",
    "economic_agency",
    "deal",
    "barter",
    "contract",
    "wants_trade",
)


def _run_git_lines(repo_root: Path, args: list[str]) -> tuple[str, ...]:
    result = subprocess.run(
        args,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ()
    return tuple(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())


def _modified_paths(repo_root: Path) -> tuple[str, ...]:
    tracked = set(_run_git_lines(repo_root, ["git", "diff", "--name-only"]))
    tracked.update(_run_git_lines(repo_root, ["git", "diff", "--cached", "--name-only"]))
    return tuple(sorted(tracked))


def _untracked_paths(repo_root: Path) -> tuple[str, ...]:
    return _run_git_lines(repo_root, ["git", "ls-files", "-o", "--exclude-standard"])


def _contains_any_term(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in _FORBIDDEN_SIGNAL_TERMS)


def _contains_desired_marker(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in _DESIRED_MARKER_TERMS)


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


def _walk_paths(node, *, path: str = ""):
    if isinstance(node, dict):
        for key, value in node.items():
            next_path = f"{path}.{key}" if path else str(key)
            yield from _walk_paths(value, path=next_path)
        return
    if isinstance(node, (list, tuple)):
        for idx, value in enumerate(node):
            next_path = f"{path}[{idx}]"
            yield from _walk_paths(value, path=next_path)
        return
    yield path, node


def _stage25_visible_payload(probe_run) -> dict[str, object]:
    payload = asdict(probe_run)
    payload.pop("eval_only", None)
    return payload


def _scan_stage25_leaks(probe_run) -> tuple[tuple[str, ...], tuple[str, ...]]:
    payload = _stage25_visible_payload(probe_run)
    key_hits: list[str] = []
    value_hits: list[str] = []

    def _scan(node, *, path: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                next_path = f"{path}.{key}" if path else str(key)
                key_lower = str(key).lower()
                if any(token == key_lower for token in _FORBIDDEN_STAGE25_KEY_TOKENS):
                    key_hits.append(next_path)
                _scan(value, path=next_path)
            return
        if isinstance(node, (list, tuple)):
            for idx, value in enumerate(node):
                next_path = f"{path}[{idx}]"
                _scan(value, path=next_path)
            return
        if isinstance(node, str):
            path_lower = path.lower()
            value_lower = node.lower()
            if any(token in value_lower for token in _FORBIDDEN_STAGE25_VALUE_TOKENS):
                value_hits.append(f"{path}={node}")
            for path_token, value_token in _FORBIDDEN_STAGE25_PATH_VALUE_TOKENS:
                if path_token in path_lower and value_token in value_lower:
                    value_hits.append(f"{path}={node}")

    _scan(payload, path="")

    return tuple(dict.fromkeys(key_hits)), tuple(dict.fromkeys(value_hits))


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

    desired_as_evidence = bool(summary.get("desired_used_as_evidence", False))
    if not desired_as_evidence:
        for packet in packets:
            if packet.source_authority is not SignalAuthority.OBSERVED_EVENT:
                continue
            if any(_contains_desired_marker(fragment) for fragment in _packet_strings(packet)):
                desired_as_evidence = True
                break

    oracle_leak = any(
        "mutually_beneficial_trade_possible" in " ".join(_packet_strings(packet))
        for packet in packets
    )

    one_shot_regularization = bool(summary.get("stable_regularities_from_single_claim", False))
    if not one_shot_regularization and len(packets) <= 1:
        one_shot_regularization = (
            bool(summary.get("stable_exchange_rule_claimed", False))
            or bool(summary.get("stable_counterpart_reliability_claimed", False))
            or bool(summary.get("mature_pattern_claimed", False))
            or int(summary.get("regularity_promotion_count", 0)) > 0
        )

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

    correction_created = bool(summary.get("correction_candidate_created", False))
    execution_prohibited = bool(summary.get("execution_prohibited", True))
    correction_executed = bool(summary.get("correction_executed", False)) or bool(
        summary.get("correction_candidate_executed", False)
    )
    correction_seam_broken = correction_executed or (correction_created and not execution_prohibited)

    repo = repo_root or Path(__file__).resolve().parents[2]
    changed_paths = set(_modified_paths(repo))
    changed_paths.update(_untracked_paths(repo))
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
        FalsifierResult("correction_candidate_executed", not correction_seam_broken, "correction candidate treated as executed or execution guard broken" if correction_seam_broken else "ok"),
        FalsifierResult("phase_core_modification", not core_modified, "forbidden core files modified" if core_modified else "ok"),
    )


def run_stage2_trace_falsifiers(trace_run, *, repo_root: Path | None = None) -> tuple[FalsifierResult, ...]:
    records = [record for step in trace_run.steps for record in step.phase_records]
    phase_codes = {record.phase_code for record in records}
    packet_meta: dict[str, tuple[str, str]] = {}
    for step in trace_run.steps:
        for packet_ref in step.packet_refs:
            packet_meta[packet_ref.packet_id] = (packet_ref.signal_kind, packet_ref.source_authority)

    joined_record_text = "\n".join(
        " ".join(
            (
                record.phase_code,
                " ".join(record.input_refs),
                " ".join(record.output_refs),
                " ".join(record.reason_codes),
                " ".join(record.uncertainty_markers),
                " ".join(record.prohibited_claims),
                " ".join(record.downstream_permission_delta),
            )
        )
        for record in records
    ).lower()

    hidden_truth_leak = (
        "harness_truth" in joined_record_text
        or "mutually_beneficial_trade_possible_eval_only" in joined_record_text
        or any("hidden_truth_excluded:false" in " ".join(record.reason_codes).lower() for record in records)
    )

    one_shot_promoted = False
    if trace_run.packet_count <= 1:
        one_shot_promoted = any(
            record.phase_code in {"W02", "W03"}
            and (
                "provisional_repeated_pattern" in record.decision_status
                or "bounded_prior_candidate" in record.decision_status
                or "stable" in " ".join(record.reason_codes).lower()
            )
            for record in records
        )

    w04_usefulness_permission = any(
        record.phase_code == "W04"
        and (
            "usefulness_override" in " ".join(record.reason_codes).lower()
            or "should_trade" in " ".join(record.downstream_permission_delta).lower()
        )
        for record in records
    )

    w05_desired_predicted_permission = any(
        record.phase_code == "W05"
        and (
            "desired_as_permission" in " ".join(record.reason_codes).lower()
            or "predicted_as_permission" in " ".join(record.reason_codes).lower()
            or "desired_as_permission:true" in record.downstream_permission_delta
            or "predicted_as_permission:true" in record.downstream_permission_delta
            or (
                (
                    "desired_not_evidence" not in record.prohibited_claims
                    or "predicted_utility_not_permission" not in record.prohibited_claims
                )
                and (
                    "execution_authorization_granted:true" in record.downstream_permission_delta
                    or "permission_granted:true" in record.downstream_permission_delta
                )
            )
        )
        for record in records
    )

    w06_executed = any(
        record.phase_code == "W06"
        and (
            any(item == "correction_executed:true" for item in record.downstream_permission_delta)
            or any(item == "execution_prohibited:false" for item in record.downstream_permission_delta)
            or not record.execution_prohibited
        )
        for record in records
    )

    blocked_aperture_clean_allowed = any(
        record.phase_code == "W04"
        and any("aperture:blocked" == ref for ref in record.input_refs)
        and "may_deploy_candidate:true" in record.downstream_permission_delta
        for record in records
    )

    noisy_cleaned_fact = any(
        record.phase_code in {"W01", "W06"}
        and ("contradiction" in " ".join(record.input_refs).lower())
        and not record.uncertainty_markers
        for record in records
    )

    false_claim_truth = False
    for record in records:
        if record.phase_code != "W01" or record.decision_status != "admitted":
            continue
        packet_id = record.source_packet_ids[0] if record.source_packet_ids else ""
        signal_kind, source_authority = packet_meta.get(packet_id, ("", ""))
        if signal_kind != "resource_status_signal" or source_authority != "counterpart_claim":
            continue
        if "counterpart_claim_admitted_as_scaffold" not in record.reason_codes:
            false_claim_truth = True
            break

    eval_label_in_trace = "mutually_beneficial_trade_possible_eval_only" in joined_record_text
    trade_shortcut = any(term in joined_record_text for term in _FORBIDDEN_PHASE_SHORTCUT_TERMS)
    missing_coverage = not {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(phase_codes)

    repo = repo_root or Path(__file__).resolve().parents[2]
    changed_paths = set(_modified_paths(repo))
    changed_paths.update(_untracked_paths(repo))
    core_modified = any(any(path.startswith(prefix) for prefix in _FORBIDDEN_CORE_PREFIXES) for path in changed_paths)

    return (
        FalsifierResult("subject_trace_hidden_truth_leakage", not hidden_truth_leak, "hidden/eval truth leaked into trace" if hidden_truth_leak else "ok"),
        FalsifierResult("phase_adapter_core_contamination", not core_modified, "forbidden core path touched" if core_modified else "ok"),
        FalsifierResult("one_shot_claim_promoted_by_w02_or_w03", not one_shot_promoted, "one-shot signal promoted to regularity/schema" if one_shot_promoted else "ok"),
        FalsifierResult("w04_usefulness_as_permission", not w04_usefulness_permission, "w04 usefulness converted into permission" if w04_usefulness_permission else "ok"),
        FalsifierResult("w05_desired_or_predicted_as_permission", not w05_desired_predicted_permission, "w05 desired/predicted promoted to permission" if w05_desired_predicted_permission else "ok"),
        FalsifierResult("w06_correction_candidate_executed", not w06_executed, "w06 correction candidate executed or execution guard broken" if w06_executed else "ok"),
        FalsifierResult("blocked_aperture_still_allows_clean_applicability", not blocked_aperture_clean_allowed, "blocked aperture still clean-allowed by w04" if blocked_aperture_clean_allowed else "ok"),
        FalsifierResult("noisy_signal_cleaned_into_fact", not noisy_cleaned_fact, "noisy/contradictory signal cleaned into fact" if noisy_cleaned_fact else "ok"),
        FalsifierResult("false_counterpart_claim_becomes_truth", not false_claim_truth, "counterpart claim promoted to fact in trace" if false_claim_truth else "ok"),
        FalsifierResult("eval_label_in_phase_trace", not eval_label_in_trace, "eval-only label leaked into phase trace" if eval_label_in_trace else "ok"),
        FalsifierResult("trade_specific_phase_shortcut", not trade_shortcut, "trade-specific shortcut appeared in phase trace" if trade_shortcut else "ok"),
        FalsifierResult("phase_trace_without_w01_to_w06_coverage", not missing_coverage, "phase coverage incomplete" if missing_coverage else "ok"),
    )


def run_stage25_reaction_falsifiers(probe_run, *, repo_root: Path | None = None) -> tuple[FalsifierResult, ...]:
    steps = probe_run.steps
    records = [item.phase_trace_summary for item in steps]
    visible_blob = "\n".join(
        " ".join(
            [
                step.packet_id,
                step.world_event_reaction.signal_kind,
                step.world_event_reaction.source_authority,
                " ".join(step.world_event_reaction.reason_codes),
                " ".join(step.counterpart_claim_reaction.reason_codes),
                " ".join(step.phase_trace_summary.reason_codes),
                " ".join(step.phase_trace_summary.prohibited_claims),
            ]
        )
        for step in steps
    ).lower()
    key_hits, value_hits = _scan_stage25_leaks(probe_run)

    self_state_as_world_fact = any(step.world_event_reaction.self_state_as_world_evidence for step in steps)
    deficit_as_permission = bool(probe_run.self_state_probe.deficit_markers) and any(
        step.phase_trace_summary.w04_usefulness_as_permission
        or "deficit_as_permission" in " ".join(step.phase_trace_summary.reason_codes).lower()
        or "self_state_permission_granted:true" in " ".join(step.phase_trace_summary.reason_codes).lower()
        for step in steps
    )
    surplus_as_offer = bool(probe_run.self_state_probe.surplus_markers) and (
        any("trade_offer" in " ".join(step.phase_trace_summary.reason_codes).lower() for step in steps)
        or any("trade_offer:true" in hit.lower() for hit in value_hits)
        or any("wants_trade:true" in hit.lower() for hit in value_hits)
        or any("trade_intent:true" in hit.lower() for hit in value_hits)
        or any("should_trade:true" in hit.lower() for hit in value_hits)
    )
    b_claim_as_fact = any(step.counterpart_claim_reaction.claim_detected and step.counterpart_claim_reaction.promoted_to_fact for step in steps)
    complementarity_oracle = any(
        token in hit.lower()
        for hit in value_hits
        for token in (
            "mutual_benefit_oracle",
            "true_need_surplus_pairing",
            "mutually_beneficial_trade_possible_eval_only",
            "potential_reciprocity_eval_only",
            "should_trade:true",
        )
    )
    usefulness_as_permission = any(step.phase_trace_summary.w04_usefulness_as_permission for step in steps)
    desired_as_observed = any(step.phase_trace_summary.w05_desired_as_observed for step in steps)
    predicted_as_permitted = any(step.phase_trace_summary.w05_predicted_as_permitted for step in steps)
    blocked_aperture_clean_route = any(
        step.world_event_reaction.blocked_aperture_seen and step.phase_trace_summary.w04_clean_applicability_allowed for step in steps
    )
    noisy_cleaned_fact = any(
        step.world_event_reaction.contradiction_seen and not step.phase_trace_summary.w06_residual_uncertainty_present for step in steps
    )
    false_claim_no_residue = any(
        step.counterpart_claim_reaction.claim_detected
        and "false_counterpart_claim" in probe_run.scenario_id
        and not step.phase_trace_summary.w06_residual_uncertainty_present
        for step in steps
    )
    correction_executed = any(step.phase_trace_summary.w06_correction_executed for step in steps) or any(
        not step.phase_trace_summary.w06_execution_prohibited for step in steps
    )
    hidden_truth_leak = bool(key_hits or value_hits)

    full_execution_claim = probe_run.execution_surface.execution_level.value == "full_subject_tick_execution"
    step_projection_detected = any(
        "projection" in step.execution_surface_source.lower()
        or "projection" in step.phase_trace_summary.provenance.lower()
        or bool(step.adapter_limitations)
        for step in steps
    )
    step_non_tick_source = any(step.execution_surface_source != "subject_tick.execute_subject_tick" for step in steps)
    step_unverified_coverage = any(not step.phase_trace_summary.phase_coverage_verified for step in steps)
    required_phase_codes = {"W01", "W02", "W03", "W04", "W05", "W06"}

    step_missing_tick_evidence = False
    for step in steps:
        summary = step.phase_trace_summary
        if not required_phase_codes.issubset(set(summary.phase_coverage)):
            step_missing_tick_evidence = True
            break
        evidence_phase_codes = {
            item.split(":", 1)[0]
            for item in summary.phase_coverage_evidence
            if ":" in item
        }
        if not required_phase_codes.issubset(evidence_phase_codes):
            step_missing_tick_evidence = True
            break

    projection_labeled_real = full_execution_claim and (
        probe_run.execution_surface.adapter_projection_used
        or step_projection_detected
        or step_non_tick_source
    )
    execution_level_overclaim = full_execution_claim and (
        probe_run.execution_surface.subject_tick_used is False
        or probe_run.execution_surface.adapter_projection_used
        or probe_run.execution_surface.owner_surface_used
        or bool(probe_run.execution_surface.fallback_reasons)
        or "subject_tick.execute_subject_tick" not in set(probe_run.execution_surface.successful_surfaces)
        or any(item.startswith("subject_tick.execute_subject_tick") for item in probe_run.execution_surface.failed_surfaces)
        or step_non_tick_source
        or step_projection_detected
        or step_unverified_coverage
        or step_missing_tick_evidence
    )
    stage25_trade_shortcut_terms = (
        "trade_intent:true",
        "trade_offer:true",
        "wants_trade:true",
        "should_trade:true",
        "mutual_benefit_oracle:true",
        "barter_success_signal",
        "deal_success_signal",
        "exchange_oracle:true",
    )
    trade_shortcut = any(term in visible_blob for term in stage25_trade_shortcut_terms)
    one_shot_regularized = len(steps) == 1 and any(
        "provisional_repeated_pattern" in " ".join(step.phase_trace_summary.reason_codes).lower()
        or "bounded_prior_candidate" in " ".join(step.phase_trace_summary.reason_codes).lower()
        for step in steps
    )
    fake_coverage = any(
        (
            step.phase_trace_summary.coverage_complete
            and (
                not step.phase_trace_summary.phase_coverage_verified
                or step.phase_trace_summary.phase_coverage_verification_mode != "tick_result_artifact_presence"
                or not required_phase_codes.issubset(set(step.phase_trace_summary.phase_coverage))
                or not required_phase_codes.issubset(
                    {
                        item.split(":", 1)[0]
                        for item in step.phase_trace_summary.phase_coverage_evidence
                        if ":" in item
                    }
                )
            )
        )
        for step in steps
    )
    claim_boundary_missing = not (
        getattr(probe_run.claim_boundary, "instrumentation_only", False)
        and getattr(probe_run.claim_boundary, "adapter_projection_not_competence", False)
    )

    repo = repo_root or Path(__file__).resolve().parents[2]
    changed_paths = set(_modified_paths(repo))
    changed_paths.update(_untracked_paths(repo))
    core_modified = any(any(path.startswith(prefix) for prefix in _FORBIDDEN_CORE_PREFIXES) for path in changed_paths)

    return (
        FalsifierResult("a_self_state_hidden_as_world_fact", not self_state_as_world_fact, "self state leaked into world evidence channel" if self_state_as_world_fact else "ok"),
        FalsifierResult("a_deficit_as_permission", not deficit_as_permission, "deficit state promoted to permission" if deficit_as_permission else "ok"),
        FalsifierResult("a_surplus_as_trade_offer", not surplus_as_offer, "surplus state promoted to trade offer shortcut" if surplus_as_offer else "ok"),
        FalsifierResult("b_claim_as_fact", not b_claim_as_fact, "counterpart claim promoted to fact" if b_claim_as_fact else "ok"),
        FalsifierResult(
            "mirrored_complementarity_as_oracle",
            not complementarity_oracle,
            "complementarity oracle leaked via structured path"
            if complementarity_oracle
            else "ok",
        ),
        FalsifierResult("usefulness_as_permission", not usefulness_as_permission, "usefulness bypassed permission boundary" if usefulness_as_permission else "ok"),
        FalsifierResult("desired_as_observed", not desired_as_observed, "desired state promoted into observed evidence channel" if desired_as_observed else "ok"),
        FalsifierResult("predicted_as_permitted", not predicted_as_permitted, "predicted success promoted into permission channel" if predicted_as_permitted else "ok"),
        FalsifierResult("blocked_aperture_clean_route", not blocked_aperture_clean_route, "blocked aperture still allowed clean applicability route" if blocked_aperture_clean_route else "ok"),
        FalsifierResult("noisy_claim_cleaned_into_fact", not noisy_cleaned_fact, "noisy claim cleaned into fact without residue" if noisy_cleaned_fact else "ok"),
        FalsifierResult("false_claim_no_residue", not false_claim_no_residue, "false claim handled without residue/revalidation marker" if false_claim_no_residue else "ok"),
        FalsifierResult("correction_candidate_executed", not correction_executed, "correction candidate executed or execution guard broken" if correction_executed else "ok"),
        FalsifierResult(
            "hidden_truth_leakage_stage25",
            not hidden_truth_leak,
            (
                f"hidden/eval-only truth leaked into visible stage25 trace; "
                f"key_paths={list(key_hits)[:3]} value_paths={list(value_hits)[:3]}"
            )
            if hidden_truth_leak
            else "ok",
        ),
        FalsifierResult(
            "adapter_projection_labeled_real",
            not projection_labeled_real,
            "projection provenance present while full subject tick execution claimed"
            if projection_labeled_real
            else "ok",
        ),
        FalsifierResult(
            "execution_level_overclaim",
            not execution_level_overclaim,
            "full execution claim inconsistent with per-step provenance/surfaces/coverage evidence"
            if execution_level_overclaim
            else "ok",
        ),
        FalsifierResult("core_contamination", not core_modified, "forbidden core path touched" if core_modified else "ok"),
        FalsifierResult("trade_specific_signal", not trade_shortcut, "trade-specific shortcut semantics detected in visible stage25 trace" if trade_shortcut else "ok"),
        FalsifierResult("one_shot_regularization", not one_shot_regularized, "one-shot signal promoted to regularity/prior" if one_shot_regularized else "ok"),
        FalsifierResult(
            "phase_coverage_fake",
            not fake_coverage,
            "stage25 claimed W01-W06 coverage without tick-derived verification evidence"
            if fake_coverage
            else "ok",
        ),
        FalsifierResult("claim_boundary_missing", not claim_boundary_missing, "stage25 claim boundary missing or incomplete" if claim_boundary_missing else "ok"),
    )


def run_stage3_response_falsifiers(stage3_run, *, repo_root: Path | None = None) -> tuple[FalsifierResult, ...]:
    candidates = stage3_run.response_candidates
    selected_kind = stage3_run.selected_response_kind.value
    selected_candidate = next((item for item in candidates if item.response_id == stage3_run.selected_response_id), None)
    response_blob = "\n".join(
        " ".join(
            (
                item.response_kind.value,
                item.requested_effect,
                " ".join(item.reason_codes),
                " ".join(item.evidence_refs),
                " ".join(item.phase_evidence_refs),
                " ".join(item.prohibited_claims),
                " ".join(item.boundary_markers),
                " ".join(item.response_basis_summary),
                " ".join(item.forbidden_basis_markers),
            )
        )
        for item in candidates
    ).lower()

    payload = asdict(stage3_run)
    payload.pop("eval_only", None)
    leak_key_hits: list[str] = []
    leak_value_hits: list[str] = []
    forbidden_key_tokens = {
        "hidden_truth",
        "harness_truth",
        "true_inventory",
        "b_true_inventory",
        "true_need_surplus_pairing",
        "mutual_benefit_oracle",
        "eval_label",
        "success_label",
        "expected_success_label",
        "scenario_expected_outcome",
    }
    forbidden_value_tokens = (
        "hidden_truth:",
        "harness_truth:",
        "eval_label:",
        "success_label:",
        "expected_success_label:",
        "mutual_benefit_oracle",
        "should_trade",
        "wants_trade",
        "trade_intent",
        "economic_agency",
        "true_inventory",
        "scenario_expected_outcome",
        "true_need_surplus_pairing",
    )

    def _path_segments(path: str) -> tuple[str, ...]:
        segments: list[str] = []
        for chunk in path.split("."):
            base = chunk.split("[", 1)[0]
            if base:
                segments.append(base.lower())
        return tuple(segments)

    for path, value in _walk_paths(payload):
        segments = _path_segments(path)
        if any(token in segments for token in forbidden_key_tokens):
            leak_key_hits.append(path)
        if isinstance(value, str):
            value_lower = value.lower()
            if any(token in value_lower for token in forbidden_value_tokens):
                if (
                    "no_hidden_truth_claim" in value_lower
                    or "no_economic_agency_claim" in value_lower
                    or "without_oracle" in value_lower
                    or value_lower.endswith("_not_used")
                ):
                    continue
                leak_value_hits.append(f"{path}={value}")

    hidden_truth_used_for_response = any(item.hidden_truth_used for item in candidates) or bool(leak_key_hits or leak_value_hits)
    eval_label_used_for_response = any(item.eval_only_used for item in candidates) or any(
        "eval_only" in fragment.lower() or "success_label" in fragment.lower()
        for item in candidates
        for fragment in (
            *item.evidence_refs,
            *item.reason_codes,
            *item.phase_evidence_refs,
        )
    ) or any(
        "eval_label" in hit.lower() or "success_label" in hit.lower()
        for hit in (*leak_key_hits, *leak_value_hits)
    )
    deficit_as_permission = any(
        item.response_kind.value in {"offer_candidate", "transfer_attempt_candidate"}
        and (
            "counterpart_claim:" not in " ".join(item.evidence_refs)
            or not any(
                marker in " ".join(item.response_basis_summary)
                for marker in (
                    "self_state_deficit_surplus_markers_are_not_permissions",
                    "self_state_asymmetry_marker_present_without_permission_upgrade",
                )
            )
        )
        for item in candidates
    ) or "deficit_as_permission" in response_blob
    surplus_as_offer = any(
        item.response_kind.value == "offer_candidate"
        and (
            "surplus_shortcut_offer" in " ".join(item.reason_codes).lower()
            or "counterpart_claim:" not in " ".join(item.evidence_refs)
            or not any(
                marker in " ".join(item.response_basis_summary)
                for marker in (
                    "bounded_complementarity_candidate_without_oracle",
                    "transfer_confirmation_visible_as_observation_not_hidden_truth",
                )
            )
        )
        for item in candidates
    )
    b_claim_as_fact = any(
        "counterpart_fact:" in " ".join(item.evidence_refs)
        or "counterpart_claim_as_fact" in " ".join(item.reason_codes).lower()
        for item in candidates
    )
    mirrored_complementarity_oracle = any(
        any(
            token in " ".join(
                (
                    *item.reason_codes,
                    *item.evidence_refs,
                    *item.phase_evidence_refs,
                    *item.response_basis_summary,
                    *item.forbidden_basis_markers,
                )
            ).lower()
            for token in (
                "mutual_benefit_oracle",
                "true_need_surplus_pairing",
                "oracle:true",
                "oracle_detected",
                "mirrored_oracle_used",
            )
        )
        for item in candidates
    )
    usefulness_as_permission = any(
        "usefulness_as_permission" in " ".join(item.reason_codes).lower()
        or item.permitted_status == "permission_granted_by_usefulness"
        for item in candidates
    )
    desired_as_observed = any(
        "desired_as_observed" in " ".join(item.reason_codes).lower()
        for item in candidates
    )
    predicted_as_permitted = any(
        "predicted_as_permitted" in " ".join(item.reason_codes).lower()
        for item in candidates
    )
    blocked_aperture_transfer_candidate = any(
        item.response_kind.value in {"offer_candidate", "transfer_attempt_candidate"}
        and (
            "blocked_aperture_event_visible" in " ".join(item.response_basis_summary).lower()
            or "blocked_aperture_visible" in " ".join(item.reason_codes).lower()
            or any("aperture:blocked" in ref.lower() for ref in item.phase_evidence_refs)
        )
        for item in candidates
    )
    noisy_claim_cleaned_into_fact = any(
        item.response_kind.value in {"offer_candidate", "transfer_attempt_candidate"}
        and (
            "contradiction_or_noise_visible" in " ".join(item.response_basis_summary).lower()
            or "contradiction_visible" in " ".join(item.reason_codes).lower()
        )
        and not (
            "revalidate" in " ".join(item.reason_codes).lower()
            or item.residual_uncertainty_refs
            or any("residual_uncertainty_present:true" in ref.lower() for ref in item.phase_evidence_refs)
        )
        for item in candidates
    )
    false_claim_clean_offer = any(
        (
            "claim_not_fact_boundary_preserved" in " ".join(item.response_basis_summary).lower()
            and not (
                "revalidate" in " ".join(item.reason_codes).lower()
                or item.residual_uncertainty_refs
                or any("residual_uncertainty_present:true" in ref.lower() for ref in item.phase_evidence_refs)
            )
        )
        and item.response_kind.value in {"offer_candidate", "transfer_attempt_candidate"}
        for item in candidates
    )
    one_shot_exchange_schema = any(
        (
            "one_shot_promoted_to_schema" in " ".join(item.reason_codes).lower()
            or (
                item.response_kind.value in {"offer_candidate", "transfer_attempt_candidate"}
                and len(item.evidence_refs) <= 1
            )
        )
        for item in candidates
    )
    trade_specific_response_kind = any(
        any(term in item.response_kind.value for term in _FORBIDDEN_STAGE3_SHORTCUT_TERMS)
        or any(term in " ".join(item.reason_codes).lower() for term in _FORBIDDEN_STAGE3_SHORTCUT_TERMS)
        for item in candidates
    )
    required_phase_codes = {"W01", "W02", "W03", "W04", "W05", "W06"}
    response_without_phase_causality = any(
        item.response_kind.value in {"offer_candidate", "transfer_attempt_candidate"}
        and (
            not {"W01", "W04", "W05", "W06"}.issubset(set(item.source_phase_coverage))
            or not {"W01", "W04", "W05", "W06"}.issubset(
                {
                    evidence.split(":", 1)[0]
                    for evidence in item.phase_evidence_refs
                    if ":" in evidence
                }
            )
            or not item.response_basis_summary
            or not item.forbidden_basis_markers
        )
        for item in candidates
    )
    candidate_executes_transfer = any(
        (not item.execution_prohibited) or "executed_transfer" in item.requested_effect.lower()
        for item in candidates
    )
    w05_routing_as_execution = any(
        "w05_route_as_permission" in " ".join(item.reason_codes).lower()
        or item.permitted_status == "executed"
        for item in candidates
    )
    w06_correction_executed = any(
        "w06_correction_executed" in " ".join(item.reason_codes).lower()
        or "correction_executed:true" in " ".join(item.reason_codes).lower()
        for item in candidates
    )

    selected_basis_blob = (
        " ".join(selected_candidate.response_basis_summary).lower() if selected_candidate is not None else ""
    )
    selected_reason_blob = " ".join(selected_candidate.reason_codes).lower() if selected_candidate is not None else ""
    control_same_as_mirrored = selected_kind in {"offer_candidate", "transfer_attempt_candidate"} and not (
        (
            "visible_claim_relation_present" in selected_reason_blob
            or "resource_asymmetry_candidate" in selected_reason_blob
            or "visible_counterpart_claim_relation_present" in selected_basis_blob
        )
        and ("counterpart_claim_not_fact" in " ".join(selected_candidate.boundary_markers).lower())
        and ("hidden_truth_not_used" in " ".join(selected_candidate.forbidden_basis_markers).lower())
        if selected_candidate is not None
        else False
    )

    phase_coverage_fake = (
        stage3_run.phase_coverage_verified
        and not required_phase_codes.issubset(
            {
                item.split(":", 1)[0]
                for item in stage3_run.phase_coverage_evidence
                if ":" in item
            }
        )
    )

    claim_boundary_missing = not any("stage3_response_candidate_probe_only" == item for item in stage3_run.claim_boundary)

    repo = repo_root or Path(__file__).resolve().parents[2]
    changed_paths = set(_modified_paths(repo))
    changed_paths.update(_untracked_paths(repo))
    core_modified = any(any(path.startswith(prefix) for prefix in _FORBIDDEN_CORE_PREFIXES) for path in changed_paths)

    return (
        FalsifierResult(
            "stage3_hidden_truth_used_for_response",
            not hidden_truth_used_for_response,
            (
                f"hidden truth or oracle leaked into candidate-visible payload; "
                f"key_paths={list(leak_key_hits)[:3]} value_paths={list(leak_value_hits)[:3]}"
            )
            if hidden_truth_used_for_response
            else "ok",
        ),
        FalsifierResult("stage3_eval_label_used_for_response", not eval_label_used_for_response, "eval labels used in response extraction" if eval_label_used_for_response else "ok"),
        FalsifierResult("stage3_deficit_as_permission", not deficit_as_permission, "deficit alone promoted to response permission" if deficit_as_permission else "ok"),
        FalsifierResult("stage3_surplus_as_offer_shortcut", not surplus_as_offer, "surplus shortcut used as offer" if surplus_as_offer else "ok"),
        FalsifierResult("stage3_b_claim_as_fact", not b_claim_as_fact, "counterpart claim promoted to fact" if b_claim_as_fact else "ok"),
        FalsifierResult("stage3_mirrored_complementarity_oracle", not mirrored_complementarity_oracle, "mirrored complementarity oracle leaked into response basis" if mirrored_complementarity_oracle else "ok"),
        FalsifierResult("stage3_usefulness_as_permission", not usefulness_as_permission, "usefulness substituted for permission" if usefulness_as_permission else "ok"),
        FalsifierResult("stage3_desired_as_observed", not desired_as_observed, "desired state treated as observed evidence" if desired_as_observed else "ok"),
        FalsifierResult("stage3_predicted_as_permitted", not predicted_as_permitted, "predicted success treated as permission" if predicted_as_permitted else "ok"),
        FalsifierResult("stage3_blocked_aperture_transfer_candidate", not blocked_aperture_transfer_candidate, "blocked aperture produced transfer candidate" if blocked_aperture_transfer_candidate else "ok"),
        FalsifierResult("stage3_noisy_claim_cleaned_into_fact", not noisy_claim_cleaned_into_fact, "noisy claim cleaned into fact/candidate" if noisy_claim_cleaned_into_fact else "ok"),
        FalsifierResult("stage3_false_claim_clean_offer", not false_claim_clean_offer, "false claim yielded clean offer candidate" if false_claim_clean_offer else "ok"),
        FalsifierResult("stage3_one_shot_exchange_schema", not one_shot_exchange_schema, "one-shot event promoted into exchange schema" if one_shot_exchange_schema else "ok"),
        FalsifierResult("stage3_trade_specific_response_kind", not trade_specific_response_kind, "trade-specific shortcut response kind/semantic detected" if trade_specific_response_kind else "ok"),
        FalsifierResult("stage3_response_without_phase_causality", not response_without_phase_causality, "response candidate missing W01->W06 phase evidence chain" if response_without_phase_causality else "ok"),
        FalsifierResult("stage3_candidate_executes_transfer", not candidate_executes_transfer, "candidate path marked as executed transfer" if candidate_executes_transfer else "ok"),
        FalsifierResult("stage3_w05_routing_as_execution_permission", not w05_routing_as_execution, "w05 route treated as execution permission" if w05_routing_as_execution else "ok"),
        FalsifierResult("stage3_w06_correction_as_executed", not w06_correction_executed, "w06 correction treated as executed update" if w06_correction_executed else "ok"),
        FalsifierResult("stage3_control_scenario_same_as_mirrored", not control_same_as_mirrored, "selected offer/transfer candidate lacks structural complementarity boundary basis" if control_same_as_mirrored else "ok"),
        FalsifierResult("stage3_core_contamination", not core_modified, "forbidden core path touched" if core_modified else "ok"),
        FalsifierResult("stage3_phase_coverage_fake", not phase_coverage_fake, "stage3 claimed phase coverage without evidence" if phase_coverage_fake else "ok"),
        FalsifierResult("stage3_claim_boundary_missing", not claim_boundary_missing, "stage3 claim boundary missing" if claim_boundary_missing else "ok"),
    )


def run_stage4_cycle_falsifiers(stage4_run, *, repo_root: Path | None = None) -> tuple[FalsifierResult, ...]:
    payload = asdict(stage4_run)
    payload.pop("eval_only", None)
    packets = stage4_run.visible_packets
    readiness = stage4_run.readiness_decision
    invocation = stage4_run.transfer_invocation_candidate
    affordance = stage4_run.transfer_affordance_record
    attempt = stage4_run.transfer_attempt_record
    result = stage4_run.transfer_result_record
    episode = stage4_run.transfer_episode_record
    response_details = stage4_run.scripted_b_response_details
    w06 = stage4_run.w06_correction_boundary

    has_counterpart_need_claim = any(
        packet.get("signal_kind") == "resource_status_signal"
        and packet.get("source_authority") == "counterpart_claim"
        and packet.get("reported_level") == "deficit"
        for packet in packets
    )
    has_counterpart_surplus_claim = any(
        packet.get("signal_kind") == "resource_status_signal"
        and packet.get("source_authority") == "counterpart_claim"
        and packet.get("reported_level") == "surplus"
        for packet in packets
    )
    has_counterpart_claim = any(packet.get("source_authority") == "counterpart_claim" for packet in packets)

    offer_emitted = stage4_run.offer_candidate_emitted
    transfer_attempted = attempt.attempted
    transfer_failed = result.outcome in {TransferOutcome.FAILED_BLOCKED, TransferOutcome.FAILED_UNKNOWN, TransferOutcome.CONTRADICTED}
    aperture_blocked = affordance.status is TransferAffordanceStatus.BLOCKED

    clarification_loop_without_progress = (
        any(not record.progress_made for record in stage4_run.clarification_records)
        and readiness.status is ResponseReadinessStatus.CLARIFICATION_REQUIRED
    )
    has_progress_clarification = any(
        record.route is ClarificationRoute.TARGETED_QUERY
        and record.target_field is not None
        and record.progress_made
        for record in stage4_run.clarification_records
    )
    clarification_when_sufficient_info_exists = (
        readiness.status is ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER
        and bool(stage4_run.clarification_records)
        and not has_progress_clarification
    )
    generic_clarification_without_target = any(
        record.route is ClarificationRoute.TARGETED_QUERY and record.target_field is None
        for record in stage4_run.clarification_records
    )
    offer_without_counterpart_need = offer_emitted and not has_counterpart_need_claim
    offer_without_counterpart_surplus = offer_emitted and not has_counterpart_surplus_claim
    offer_without_a_surplus = offer_emitted and affordance.resource_kind is None
    offer_without_a_deficit = offer_emitted and MissingInformationKind.SELF_DEFICIT in set(readiness.critical_missing_fields)
    offer_when_aperture_blocked = offer_emitted and aperture_blocked and invocation.eligible
    transfer_without_affordance = transfer_attempted and affordance.status is not TransferAffordanceStatus.AVAILABLE
    transfer_without_offer_candidate = transfer_attempted and not offer_emitted
    transfer_without_execution_flag = transfer_attempted and not invocation.execution_requested
    transfer_candidate_executes_directly = offer_emitted and transfer_attempted and invocation.source_offer_candidate_id is None
    counterpart_claim_as_fact = any(
        packet.get("source_authority") == "counterpart_claim" and not packet.get("claim_not_fact_marker", False)
        for packet in packets
    )
    surplus_as_automatic_offer = offer_emitted and not has_counterpart_claim
    deficit_as_permission = offer_emitted and (offer_without_counterpart_need or offer_without_counterpart_surplus)
    claim_boundary_blob = " ".join(stage4_run.claim_boundary).lower()
    readiness_boundary_blob = " ".join(stage4_run.readiness_decision.claim_boundary).lower()
    claim_not_fact_present = "counterpart_claim_not_fact" in claim_boundary_blob or "counterpart_claim_not_fact" in readiness_boundary_blob
    b_surplus_as_guaranteed_availability = offer_emitted and has_counterpart_surplus_claim and not claim_not_fact_present
    offer_executes_transfer_directly = offer_emitted and transfer_attempted and invocation.execution_requested and invocation.execution_prohibited
    transfer_result_as_trade_success_oracle = (
        result.result_used_as_success_authority
        or (
            stage4_run.exchange_completion_claim
            and (
                not episode.verified
                or not episode.reciprocal_transfer_observed
                or not attempt.attempted
                or result.outcome is not TransferOutcome.SUCCEEDED
            )
        )
    )
    failed_transfer_erases_residue = transfer_failed and not stage4_run.w06_residue_or_revalidation
    w06_correction_candidate_executed = (
        (w06.correction_candidate_created and w06.correction_executed)
        or (w06.correction_candidate_created and not w06.correction_execution_prohibited)
        or (transfer_failed and not w06.w06_residue_present)
        or (w06.correction_candidate_created and not w06.w06_guardrail_preserved)
    )
    a04_binding_without_authority = not affordance.a04_binding_authority_present
    a02_gap_silently_ignored = (
        affordance.status in {TransferAffordanceStatus.BLOCKED, TransferAffordanceStatus.CONTESTED, TransferAffordanceStatus.MISSING}
        and not affordance.a02_gap_markers
    )
    p02_episode_completion_inflation = episode.verified and (not episode.observed_result or not episode.attempted)

    forbidden_tokens = (
        "hidden_truth",
        "harness_truth",
        "mutual_benefit_oracle",
        "success_label",
        "expected_success_label",
        "should_trade",
        "wants_trade",
        "trade_intent",
        "economic_agency",
        "true_inventory",
    )
    leak_hits: list[str] = []
    for path, value in _walk_paths(payload):
        path_lower = path.lower()
        if "eval_only" in path_lower:
            continue
        if any(token in path_lower for token in forbidden_tokens):
            leak_hits.append(path)
        if isinstance(value, str):
            lower = value.lower()
            if any(token in lower for token in forbidden_tokens):
                if "no_hidden_truth_claim" in lower or "no_economic_agency_claim" in lower:
                    continue
                leak_hits.append(f"{path}={value}")

    hidden_inventory_used = any("true_inventory" in item or "harness_truth" in item for item in leak_hits)
    mutual_oracle_used = any("mutual_benefit_oracle" in item for item in leak_hits)
    trade_shortcut_used = any(
        token in " ".join(
            (
                " ".join(stage4_run.claim_boundary),
                " ".join(stage4_run.readiness_decision.reason_codes),
                " ".join(stage4_run.transfer_invocation_candidate.reason_codes),
            )
        ).lower()
        for token in ("should_trade", "wants_trade", "trade_intent")
    )
    pre_scripted_response_as_invocation_response = any(
        item.response_record_source == "pre_scripted_visible_packet"
        and item.caused_by_transfer_invocation
        for item in response_details
    )
    passive_transfer_packet_as_trade_success = (
        any(
            item.response_record_source in {"pre_scripted_visible_packet", "passive_observed_packet"}
            and item.transfer_outcome == "succeeded"
            and not item.caused_by_transfer_invocation
            for item in response_details
        )
        and stage4_run.exchange_completion_claim
    )
    offer_candidate_as_transfer_execution = (
        offer_emitted
        and attempt.attempted
        and not invocation.execution_requested
    )
    available_affordance_as_invoked = (
        affordance.status is TransferAffordanceStatus.AVAILABLE
        and invocation.eligible
        and not invocation.execution_requested
        and (attempt.attempted or stage4_run.post_invocation_response_count > 0)
    )
    b_response_without_invocation_causality = any(
        item.caused_by_transfer_invocation
        and (
            not attempt.attempted
            or item.causing_invocation_id is None
            or item.attempt_id is None
        )
        for item in response_details
    )

    repo = repo_root or Path(__file__).resolve().parents[2]
    changed_paths = set(_modified_paths(repo))
    changed_paths.update(_untracked_paths(repo))
    core_modified = any(any(path.startswith(prefix) for prefix in _FORBIDDEN_CORE_PREFIXES) for path in changed_paths)

    return (
        FalsifierResult("clarification_loop_without_progress", not clarification_loop_without_progress, "clarification loop remained unresolved without fallback" if clarification_loop_without_progress else "ok"),
        FalsifierResult("clarification_when_sufficient_info_exists", not clarification_when_sufficient_info_exists, "clarification asked despite sufficient bounded-offer info" if clarification_when_sufficient_info_exists else "ok"),
        FalsifierResult("generic_clarification_without_target", not generic_clarification_without_target, "clarification route missing targeted field" if generic_clarification_without_target else "ok"),
        FalsifierResult("offer_without_counterpart_need", not offer_without_counterpart_need, "offer candidate emitted without visible counterpart need claim" if offer_without_counterpart_need else "ok"),
        FalsifierResult("offer_without_counterpart_surplus", not offer_without_counterpart_surplus, "offer candidate emitted without visible counterpart surplus claim" if offer_without_counterpart_surplus else "ok"),
        FalsifierResult("offer_without_a_surplus", not offer_without_a_surplus, "offer candidate emitted without self surplus resource" if offer_without_a_surplus else "ok"),
        FalsifierResult("offer_without_a_deficit", not offer_without_a_deficit, "offer candidate emitted without self deficit marker" if offer_without_a_deficit else "ok"),
        FalsifierResult("offer_when_aperture_blocked", not offer_when_aperture_blocked, "blocked aperture still yielded eligible offer->transfer route" if offer_when_aperture_blocked else "ok"),
        FalsifierResult("transfer_without_affordance", not transfer_without_affordance, "transfer attempted without available external affordance" if transfer_without_affordance else "ok"),
        FalsifierResult("transfer_without_offer_candidate", not transfer_without_offer_candidate, "transfer attempted without bounded offer candidate" if transfer_without_offer_candidate else "ok"),
        FalsifierResult("transfer_without_explicit_execution_flag", not transfer_without_execution_flag, "transfer attempted without explicit execution flag" if transfer_without_execution_flag else "ok"),
        FalsifierResult("transfer_candidate_executes_directly", not transfer_candidate_executes_directly, "candidate path executed transfer directly" if transfer_candidate_executes_directly else "ok"),
        FalsifierResult("counterpart_claim_as_fact", not counterpart_claim_as_fact, "counterpart claim promoted to fact in stage4 payload" if counterpart_claim_as_fact else "ok"),
        FalsifierResult("hidden_b_inventory_used_for_offer", not hidden_inventory_used, "hidden inventory leaked into candidate-visible stage4 fields" if hidden_inventory_used else "ok"),
        FalsifierResult("mutual_benefit_oracle_used", not mutual_oracle_used, "mutual-benefit oracle leaked into stage4 visible path" if mutual_oracle_used else "ok"),
        FalsifierResult("surplus_as_automatic_offer", not surplus_as_automatic_offer, "self surplus auto-promoted to offer without counterpart relation" if surplus_as_automatic_offer else "ok"),
        FalsifierResult("deficit_as_permission", not deficit_as_permission, "self deficit promoted into permission/offer route" if deficit_as_permission else "ok"),
        FalsifierResult("b_surplus_as_guaranteed_availability", not b_surplus_as_guaranteed_availability, "counterpart surplus claim treated as guaranteed availability" if b_surplus_as_guaranteed_availability else "ok"),
        FalsifierResult("offer_executes_transfer_directly", not offer_executes_transfer_directly, "offer path bypassed invocation guard and executed directly" if offer_executes_transfer_directly else "ok"),
        FalsifierResult("transfer_result_as_trade_success_oracle", not transfer_result_as_trade_success_oracle, "transfer result treated as trade-success oracle" if transfer_result_as_trade_success_oracle else "ok"),
        FalsifierResult("failed_transfer_erases_residue", not failed_transfer_erases_residue, "failed transfer did not preserve residue/revalidation" if failed_transfer_erases_residue else "ok"),
        FalsifierResult("w06_correction_candidate_executed", not w06_correction_candidate_executed, "w06 correction execution marker leaked in stage4 path" if w06_correction_candidate_executed else "ok"),
        FalsifierResult("pre_scripted_response_as_invocation_response", not pre_scripted_response_as_invocation_response, "pre-scripted visible packet marked as invocation-caused response" if pre_scripted_response_as_invocation_response else "ok"),
        FalsifierResult("passive_transfer_packet_as_trade_success", not passive_transfer_packet_as_trade_success, "passive transfer packet treated as exchange completion authority" if passive_transfer_packet_as_trade_success else "ok"),
        FalsifierResult("offer_candidate_as_transfer_execution", not offer_candidate_as_transfer_execution, "offer candidate path treated as execution without explicit invocation" if offer_candidate_as_transfer_execution else "ok"),
        FalsifierResult("available_affordance_as_invoked", not available_affordance_as_invoked, "available affordance misreported as invoked without execution request" if available_affordance_as_invoked else "ok"),
        FalsifierResult("b_response_without_invocation_causality", not b_response_without_invocation_causality, "counterpart response marked causal without invocation linkage" if b_response_without_invocation_causality else "ok"),
        FalsifierResult("a04_binding_without_authority", not a04_binding_without_authority, "external affordance binding missing authority metadata" if a04_binding_without_authority else "ok"),
        FalsifierResult("a02_gap_silently_ignored", not a02_gap_silently_ignored, "transfer affordance gap present without A02-compatible marker" if a02_gap_silently_ignored else "ok"),
        FalsifierResult("p02_episode_completion_inflation", not p02_episode_completion_inflation, "p02 episode marked verified without attempt/observation chain" if p02_episode_completion_inflation else "ok"),
        FalsifierResult("core_contamination", not core_modified, "forbidden core path touched" if core_modified else "ok"),
    )
