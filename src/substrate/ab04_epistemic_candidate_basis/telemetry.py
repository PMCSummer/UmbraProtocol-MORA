from __future__ import annotations

from .models import (
    AB4BasisStatus,
    AB4CandidateKind,
    AB4EIGLevel,
    AB4EpistemicBasisInput,
    AB4EpistemicCandidateBasis,
    AB4Telemetry,
)


def build_ab4_telemetry(
    *,
    candidate_input: AB4EpistemicBasisInput,
    bases: tuple[AB4EpistemicCandidateBasis, ...],
    unsafe_basis_count: int,
) -> AB4Telemetry:
    usable = sum(1 for item in bases if item.basis_status is AB4BasisStatus.USABLE)
    blocked = sum(1 for item in bases if item.basis_status is AB4BasisStatus.BLOCKED)
    inspect = sum(1 for item in bases if item.candidate_kind is AB4CandidateKind.INSPECT)
    wait_or_reobserve = sum(
        1
        for item in bases
        if item.candidate_kind in {AB4CandidateKind.WAIT, AB4CandidateKind.REOBSERVE}
    )
    high_eig = sum(1 for item in bases if item.expected_information_gain.level is AB4EIGLevel.HIGH)
    low_or_none = sum(
        1
        for item in bases
        if item.expected_information_gain.level in {AB4EIGLevel.NONE, AB4EIGLevel.LOW}
    )
    return AB4Telemetry(
        tick_ref=candidate_input.tick_ref,
        basis_count=len(bases),
        usable_basis_count=usable,
        blocked_basis_count=blocked,
        inspect_basis_count=inspect,
        wait_or_reobserve_basis_count=wait_or_reobserve,
        high_eig_count=high_eig,
        low_or_none_eig_count=low_or_none,
        unsafe_basis_count=unsafe_basis_count,
        no_basis_count=1 if not bases else 0,
    )
