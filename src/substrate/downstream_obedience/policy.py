from __future__ import annotations

from substrate.downstream_obedience.models import (
    DownstreamObedienceDecision,
    ObedienceCheckpoint,
    ObedienceFallback,
    ObedienceStatus,
    UpstreamRestriction,
)


def build_downstream_obedience_decision(
    *,
    source_of_truth_surface: str,
    c04_mode_legitimacy: bool,
    c04_mode_claim: str | None,
    c04_authority_role: str,
    c04_computational_role: str,
    c05_legality_reuse_allowed: bool,
    c05_revalidation_required: bool,
    c05_no_safe_reuse: bool,
    c05_action_claim: str | None,
    c05_authority_role: str,
    c05_computational_role: str,
    r04_override_scope: str | None,
    r04_no_strong_override_claim: bool,
    r04_authority_role: str,
    r04_computational_role: str,
    c05_surface_invalidated: bool = False,
) -> DownstreamObedienceDecision:
    restrictions: list[UpstreamRestriction] = []
    checkpoints: list[ObedienceCheckpoint] = []
    authority_basis_ok = True
    invalidated_upstream_surface = False
    blocked_by_survival_override = False

    if c04_authority_role != "arbitration":
        authority_basis_ok = False
        restrictions.append(
            UpstreamRestriction(
                restriction_code="c04_authority_basis_insufficient",
                source_phase="C04",
                authority_role=c04_authority_role,
                computational_role=c04_computational_role,
                source_of_truth_surface=source_of_truth_surface,
                required_fallback=ObedienceFallback.REPAIR,
                reason="c04 arbitration authority missing for lawful mode continuation",
                provenance_ref=c04_mode_claim,
            )
        )
        checkpoints.append(
            ObedienceCheckpoint(
                checkpoint_id="obey.c04_authority_basis",
                status="blocked",
                source_phase="C04",
                relation_kind="arbitrates",
                reason="c04 authority basis insufficient",
            )
        )

    if c05_authority_role not in {"gating", "invalidation"}:
        authority_basis_ok = False
        restrictions.append(
            UpstreamRestriction(
                restriction_code="c05_authority_basis_insufficient",
                source_phase="C05",
                authority_role=c05_authority_role,
                computational_role=c05_computational_role,
                source_of_truth_surface=source_of_truth_surface,
                required_fallback=ObedienceFallback.REPAIR,
                reason="c05 legality authority missing for runtime reuse decision",
                provenance_ref=c05_action_claim,
            )
        )
        checkpoints.append(
            ObedienceCheckpoint(
                checkpoint_id="obey.c05_authority_basis",
                status="blocked",
                source_phase="C05",
                relation_kind="gates",
                reason="c05 authority basis insufficient",
            )
        )

    if not authority_basis_ok:
        return DownstreamObedienceDecision(
            status=ObedienceStatus.INSUFFICIENT_AUTHORITY_BASIS,
            fallback=ObedienceFallback.REPAIR,
            lawful_continue=False,
            authority_basis_ok=False,
            invalidated_upstream_surface=False,
            blocked_by_survival_override=False,
            source_of_truth_surface=source_of_truth_surface,
            requires_restrictions_read=True,
            restrictions=tuple(restrictions),
            checkpoints=tuple(checkpoints),
            reason="downstream obedience denied because authority basis is insufficient",
        )

    if c05_surface_invalidated:
        invalidated_upstream_surface = True
        restrictions.append(
            UpstreamRestriction(
                restriction_code="c05_invalidated_surface_blocks_reuse",
                source_phase="C05",
                authority_role=c05_authority_role,
                computational_role=c05_computational_role,
                source_of_truth_surface=source_of_truth_surface,
                required_fallback=ObedienceFallback.HALT,
                reason="c05 no-safe-reuse / invalidated surface blocks continuation",
                provenance_ref=c05_action_claim,
            )
        )
        checkpoints.append(
            ObedienceCheckpoint(
                checkpoint_id="obey.c05_invalidated_surface",
                status="blocked",
                source_phase="C05",
                relation_kind="gates",
                reason="c05 invalidated upstream surface",
            )
        )
        return DownstreamObedienceDecision(
            status=ObedienceStatus.INVALIDATED_UPSTREAM_SURFACE,
            fallback=ObedienceFallback.HALT,
            lawful_continue=False,
            authority_basis_ok=True,
            invalidated_upstream_surface=invalidated_upstream_surface,
            blocked_by_survival_override=False,
            source_of_truth_surface=source_of_truth_surface,
            requires_restrictions_read=True,
            restrictions=tuple(restrictions),
            checkpoints=tuple(checkpoints),
            reason="downstream obedience blocks continuation on invalidated c05 surface",
        )

    if c05_no_safe_reuse:
        restrictions.append(
            UpstreamRestriction(
                restriction_code="c05_no_safe_reuse_blocks_continue",
                source_phase="C05",
                authority_role=c05_authority_role,
                computational_role=c05_computational_role,
                source_of_truth_surface=source_of_truth_surface,
                required_fallback=ObedienceFallback.HALT,
                reason="c05 no-safe-reuse requires immediate halt",
                provenance_ref=c05_action_claim,
            )
        )
        checkpoints.append(
            ObedienceCheckpoint(
                checkpoint_id="obey.c05_no_safe_reuse",
                status="blocked",
                source_phase="C05",
                relation_kind="gates",
                reason="c05 no-safe-reuse requires halt",
            )
        )
        return DownstreamObedienceDecision(
            status=ObedienceStatus.MUST_HALT,
            fallback=ObedienceFallback.HALT,
            lawful_continue=False,
            authority_basis_ok=True,
            invalidated_upstream_surface=False,
            blocked_by_survival_override=False,
            source_of_truth_surface=source_of_truth_surface,
            requires_restrictions_read=True,
            restrictions=tuple(restrictions),
            checkpoints=tuple(checkpoints),
            reason="downstream obedience requires halt because no-safe-reuse is active",
        )

    if r04_override_scope in {"broad", "emergency"} and not r04_no_strong_override_claim:
        blocked_by_survival_override = True
        restrictions.append(
            UpstreamRestriction(
                restriction_code="r04_survival_override_blocks_continue",
                source_phase="R04",
                authority_role=r04_authority_role,
                computational_role=r04_computational_role,
                source_of_truth_surface=source_of_truth_surface,
                required_fallback=ObedienceFallback.REPAIR,
                reason="r04 survival override blocks ordinary continuation",
            )
        )
        checkpoints.append(
            ObedienceCheckpoint(
                checkpoint_id="obey.r04_survival_override",
                status="enforced_detour",
                source_phase="R04",
                relation_kind="overrides_survival",
                reason="r04 override scope requires repair path",
            )
        )
        return DownstreamObedienceDecision(
            status=ObedienceStatus.BLOCKED_BY_SURVIVAL_OVERRIDE,
            fallback=ObedienceFallback.REPAIR,
            lawful_continue=False,
            authority_basis_ok=True,
            invalidated_upstream_surface=False,
            blocked_by_survival_override=blocked_by_survival_override,
            source_of_truth_surface=source_of_truth_surface,
            requires_restrictions_read=True,
            restrictions=tuple(restrictions),
            checkpoints=tuple(checkpoints),
            reason="downstream obedience blocked by r04 survival override",
        )

    if not c04_mode_legitimacy:
        restrictions.append(
            UpstreamRestriction(
                restriction_code="c04_mode_legitimacy_failed",
                source_phase="C04",
                authority_role=c04_authority_role,
                computational_role=c04_computational_role,
                source_of_truth_surface=source_of_truth_surface,
                required_fallback=ObedienceFallback.REPAIR,
                reason="c04 mode legitimacy is false",
                provenance_ref=c04_mode_claim,
            )
        )
        checkpoints.append(
            ObedienceCheckpoint(
                checkpoint_id="obey.c04_mode_legitimacy",
                status="enforced_detour",
                source_phase="C04",
                relation_kind="arbitrates",
                reason="c04 mode legitimacy failed",
            )
        )
        return DownstreamObedienceDecision(
            status=ObedienceStatus.MUST_REPAIR,
            fallback=ObedienceFallback.REPAIR,
            lawful_continue=False,
            authority_basis_ok=True,
            invalidated_upstream_surface=False,
            blocked_by_survival_override=False,
            source_of_truth_surface=source_of_truth_surface,
            requires_restrictions_read=True,
            restrictions=tuple(restrictions),
            checkpoints=tuple(checkpoints),
            reason="downstream obedience requires repair because c04 mode legitimacy failed",
        )

    if c05_revalidation_required or not c05_legality_reuse_allowed:
        restrictions.append(
            UpstreamRestriction(
                restriction_code="c05_revalidation_required",
                source_phase="C05",
                authority_role=c05_authority_role,
                computational_role=c05_computational_role,
                source_of_truth_surface=source_of_truth_surface,
                required_fallback=ObedienceFallback.REVALIDATE,
                reason="c05 legality requires revalidation before continuation",
                provenance_ref=c05_action_claim,
            )
        )
        checkpoints.append(
            ObedienceCheckpoint(
                checkpoint_id="obey.c05_revalidation",
                status="enforced_detour",
                source_phase="C05",
                relation_kind="gates",
                reason="c05 legality requires revalidation",
            )
        )
        return DownstreamObedienceDecision(
            status=ObedienceStatus.MUST_REVALIDATE,
            fallback=ObedienceFallback.REVALIDATE,
            lawful_continue=False,
            authority_basis_ok=True,
            invalidated_upstream_surface=False,
            blocked_by_survival_override=False,
            source_of_truth_surface=source_of_truth_surface,
            requires_restrictions_read=True,
            restrictions=tuple(restrictions),
            checkpoints=tuple(checkpoints),
            reason="downstream obedience requires revalidation on c05 legality surface",
        )

    if r04_override_scope in {"focused", "narrow"}:
        restrictions.append(
            UpstreamRestriction(
                restriction_code="r04_override_scope_requires_restricted_continue",
                source_phase="R04",
                authority_role=r04_authority_role,
                computational_role=r04_computational_role,
                source_of_truth_surface=source_of_truth_surface,
                required_fallback=ObedienceFallback.CONTINUE,
                reason="r04 override scope requires bounded continuation with restrictions",
            )
        )
        checkpoints.append(
            ObedienceCheckpoint(
                checkpoint_id="obey.r04_restricted_continue",
                status="allowed",
                source_phase="R04",
                relation_kind="modulates",
                reason="bounded continue with r04 restrictions",
            )
        )
        return DownstreamObedienceDecision(
            status=ObedienceStatus.ALLOW_CONTINUE_WITH_RESTRICTION,
            fallback=ObedienceFallback.CONTINUE,
            lawful_continue=True,
            authority_basis_ok=True,
            invalidated_upstream_surface=False,
            blocked_by_survival_override=False,
            source_of_truth_surface=source_of_truth_surface,
            requires_restrictions_read=True,
            restrictions=tuple(restrictions),
            checkpoints=tuple(checkpoints),
            reason="downstream obedience allows continue with explicit restriction envelope",
        )

    checkpoints.append(
        ObedienceCheckpoint(
            checkpoint_id="obey.allow_continue",
            status="allowed",
            source_phase="RT01",
            relation_kind="execution_enforcement",
            reason="all load-bearing authority surfaces allow bounded continue",
        )
    )
    return DownstreamObedienceDecision(
        status=ObedienceStatus.ALLOW_CONTINUE,
        fallback=ObedienceFallback.CONTINUE,
        lawful_continue=True,
        authority_basis_ok=True,
        invalidated_upstream_surface=False,
        blocked_by_survival_override=False,
        source_of_truth_surface=source_of_truth_surface,
        requires_restrictions_read=True,
        restrictions=tuple(restrictions),
        checkpoints=tuple(checkpoints),
        reason="downstream obedience allows bounded continuation",
    )
