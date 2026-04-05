from __future__ import annotations

from substrate.discourse_update import build_discourse_update
from substrate.grounded_semantic import build_grounded_semantic_substrate
from substrate.modus_hypotheses import build_modus_hypotheses


def build_grounded_semantic_substrate_normative(
    dictum_result_or_bundle: object,
    *,
    utterance_surface: object | None = None,
    memory_anchor_ref: str | None = None,
    cooperation_anchor_ref: str | None = None,
) -> object:
    modus = build_modus_hypotheses(dictum_result_or_bundle)  # type: ignore[arg-type]
    discourse = build_discourse_update(modus)
    return build_grounded_semantic_substrate(
        dictum_result_or_bundle,  # type: ignore[arg-type]
        utterance_surface=utterance_surface,  # type: ignore[arg-type]
        memory_anchor_ref=memory_anchor_ref,
        cooperation_anchor_ref=cooperation_anchor_ref,
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse,
    )
