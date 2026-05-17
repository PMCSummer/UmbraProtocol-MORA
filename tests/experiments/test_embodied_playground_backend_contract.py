from __future__ import annotations

from experiments.embodied_playground.falsifiers import (
    action_without_ap01_envelope,
    backend_selects_action,
)
from experiments.embodied_playground.models import (
    CorrelationStatus,
    EffectStatus,
    PublishedActionEnvelope,
)
from experiments.embodied_playground.world_backend import ContractOnlyWorldBackend, WorldBackend


def _envelope() -> PublishedActionEnvelope:
    return PublishedActionEnvelope(
        envelope_id="env:1",
        subject_id="subject_a",
        ap01_request_ref="ap01_request:1",
        action_kind="inspect",
        target_ref="object:panel",
        args={"distance": 1},
        intended_effect="inspection",
        source_tick_ref="tick:1",
        source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
        permission_refs=("W04:permit",),
        evidence_refs=("W01:obs",),
        affordance_binding_refs=("A04:bind",),
    )


def test_contract_only_backend_implements_required_interface() -> None:
    backend = ContractOnlyWorldBackend()
    assert isinstance(backend, WorldBackend)
    reset = backend.reset(seed=7, scenario_config={"name": "contract_only"})
    assert reset["reset"] is True
    obs = backend.observe("subject_a")
    action_space = backend.action_space("subject_a")
    snapshot = backend.public_snapshot("subject_a")
    eval_snapshot = backend.eval_snapshot()
    assert obs.subject_id == "subject_a"
    assert action_space.subject_id == "subject_a"
    assert snapshot.subject_id == "subject_a"
    assert eval_snapshot.must_never_enter_subject_visible is True


def test_world_backend_protocol_returns_typed_frames() -> None:
    backend = ContractOnlyWorldBackend()
    observation = backend.observe("subject_a")
    action_space = backend.action_space("subject_a")
    public_snapshot = backend.public_snapshot("subject_a")
    eval_snapshot = backend.eval_snapshot()
    assert observation.__class__.__name__ == "ObservationFrame"
    assert action_space.__class__.__name__ == "ActionSpaceFrame"
    assert public_snapshot.__class__.__name__ == "PublicWorldSnapshot"
    assert eval_snapshot.__class__.__name__ == "EvalOnlyWorldTruth"


def test_contract_only_backend_outputs_strict_model_types() -> None:
    from experiments.embodied_playground.models import (
        ActionEffectFrame,
        ActionSpaceFrame,
        EvalOnlyWorldTruth,
        ObservationFrame,
        PublicWorldSnapshot,
    )

    backend = ContractOnlyWorldBackend()
    observation = backend.observe("subject_a")
    action_space = backend.action_space("subject_a")
    snapshot = backend.public_snapshot("subject_a")
    effect = backend.submit_action(_envelope())
    eval_snapshot = backend.eval_snapshot()

    assert isinstance(observation, ObservationFrame)
    assert isinstance(action_space, ActionSpaceFrame)
    assert isinstance(snapshot, PublicWorldSnapshot)
    assert isinstance(effect, ActionEffectFrame)
    assert isinstance(eval_snapshot, EvalOnlyWorldTruth)


def test_submit_action_requires_published_envelope_and_effect_is_correlated() -> None:
    backend = ContractOnlyWorldBackend()
    envelope = _envelope()
    effect = backend.submit_action(envelope)
    assert effect.request_ref == envelope.ap01_request_id
    assert effect.envelope_ref == envelope.envelope_id
    assert effect.correlation_status == CorrelationStatus.CORRELATED_TO_REQUEST
    assert effect.effect_status == EffectStatus.UNKNOWN
    assert action_without_ap01_envelope(effect) is False


def test_envelope_is_not_execution_and_not_completion_claim() -> None:
    envelope = _envelope()
    assert envelope.submitted_to_world is False
    assert envelope.executed_by_world is False
    assert envelope.request_boundary_preserved is True
    assert backend_selects_action(ContractOnlyWorldBackend()) is False


def test_effect_without_request_cannot_claim_correlated_to_request() -> None:
    from experiments.embodied_playground.models import ActionEffectFrame

    effect = ActionEffectFrame(
        effect_id="effect:bad",
        subject_id="subject_a",
        tick_index=1,
        request_ref=None,
        envelope_ref=None,
        action_kind="inspect",
        target_ref="object:panel",
        effect_status=EffectStatus.FAILED,
        body_delta={},
        inventory_delta={},
        world_delta_public={},
        observed_result_refs=("result:failed",),
        correlation_status=CorrelationStatus.CORRELATED_TO_REQUEST,
    )
    assert action_without_ap01_envelope(effect) is True
