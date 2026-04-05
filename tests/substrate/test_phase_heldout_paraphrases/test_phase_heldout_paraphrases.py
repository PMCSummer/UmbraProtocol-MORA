from __future__ import annotations

from substrate.discourse_update import ProposalType
from substrate.grounded_semantic import derive_grounded_downstream_contract
from substrate.modus_hypotheses import IllocutionKind
from tests.substrate.phase_axis_testkit import build_phase_axis_context


_DIRECT_PARAPHRASES: tuple[str, ...] = (
    "alpha remains stable today",
    "today alpha stays stable",
    "at present alpha is steady",
)

_REPORTED_PARAPHRASES: tuple[str, ...] = (
    "he said alpha remains stable today",
    "according to him, alpha remains stable today",
    'he said "alpha remains stable today"',
)


def test_heldout_direct_paraphrases_preserve_nonquoted_causal_profile() -> None:
    contexts = [
        build_phase_axis_context(text, f"heldout-direct-{idx}")
        for idx, text in enumerate(_DIRECT_PARAPHRASES, start=1)
    ]
    assert len({ctx.surface.surface.raw_text for ctx in contexts}) == len(_DIRECT_PARAPHRASES)

    for ctx in contexts:
        force_kinds = {
            hypothesis.illocution_kind
            for record in ctx.modus.bundle.hypothesis_records
            for hypothesis in record.illocution_hypotheses
        }
        proposal_types = {proposal.proposal_type for proposal in ctx.discourse_update.bundle.update_proposals}
        assert IllocutionKind.QUOTED_FORCE_CANDIDATE not in force_kinds
        assert IllocutionKind.REPORTED_FORCE_CANDIDATE not in force_kinds
        assert not proposal_types.intersection(
            {
                ProposalType.REPORTED_CONTENT_UPDATE,
                ProposalType.QUOTED_CONTENT_UPDATE,
                ProposalType.ECHOIC_CONTENT_UPDATE,
            }
        )


def test_heldout_reported_paraphrases_preserve_reported_or_quoted_profile() -> None:
    contexts = [
        build_phase_axis_context(text, f"heldout-reported-{idx}")
        for idx, text in enumerate(_REPORTED_PARAPHRASES, start=1)
    ]
    assert len({ctx.surface.surface.raw_text for ctx in contexts}) == len(_REPORTED_PARAPHRASES)

    for ctx in contexts:
        force_kinds = {
            hypothesis.illocution_kind
            for record in ctx.modus.bundle.hypothesis_records
            for hypothesis in record.illocution_hypotheses
        }
        proposal_types = {proposal.proposal_type for proposal in ctx.discourse_update.bundle.update_proposals}
        grounded_contract = derive_grounded_downstream_contract(ctx.grounded_compatibility)
        has_force_signal = bool(
            force_kinds.intersection(
                {
                    IllocutionKind.REPORTED_FORCE_CANDIDATE,
                    IllocutionKind.QUOTED_FORCE_CANDIDATE,
                    IllocutionKind.ECHOIC_FORCE_CANDIDATE,
                }
            )
        )
        has_proposal_signal = bool(
            proposal_types.intersection(
                {
                    ProposalType.REPORTED_CONTENT_UPDATE,
                    ProposalType.QUOTED_CONTENT_UPDATE,
                    ProposalType.ECHOIC_CONTENT_UPDATE,
                }
            )
        )
        assert has_force_signal or has_proposal_signal or grounded_contract.source_mode.value in {
            "reported_content",
            "quoted_content",
            "mixed",
        }
