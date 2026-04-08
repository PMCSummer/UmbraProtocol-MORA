from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ObedienceStatus(str, Enum):
    ALLOW_CONTINUE = "allow_continue"
    ALLOW_CONTINUE_WITH_RESTRICTION = "allow_continue_with_restriction"
    MUST_REPAIR = "must_repair"
    MUST_REVALIDATE = "must_revalidate"
    MUST_HALT = "must_halt"
    INSUFFICIENT_AUTHORITY_BASIS = "insufficient_authority_basis"
    INVALIDATED_UPSTREAM_SURFACE = "invalidated_upstream_surface"
    BLOCKED_BY_SURVIVAL_OVERRIDE = "blocked_by_survival_override"


class ObedienceFallback(str, Enum):
    CONTINUE = "continue"
    REPAIR = "repair"
    REVALIDATE = "revalidate"
    HALT = "halt"


@dataclass(frozen=True, slots=True)
class UpstreamRestriction:
    restriction_code: str
    source_phase: str
    authority_role: str
    computational_role: str
    source_of_truth_surface: str
    required_fallback: ObedienceFallback
    reason: str
    provenance_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ObedienceCheckpoint:
    checkpoint_id: str
    status: str
    source_phase: str
    relation_kind: str
    reason: str


@dataclass(frozen=True, slots=True)
class DownstreamObedienceDecision:
    status: ObedienceStatus
    fallback: ObedienceFallback
    lawful_continue: bool
    authority_basis_ok: bool
    invalidated_upstream_surface: bool
    blocked_by_survival_override: bool
    source_of_truth_surface: str
    requires_restrictions_read: bool
    restrictions: tuple[UpstreamRestriction, ...]
    checkpoints: tuple[ObedienceCheckpoint, ...]
    reason: str

