from __future__ import annotations

from substrate.subject_tick import SubjectTickContext, SubjectTickInput, execute_subject_tick


def build_subject_tick(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool = False,
    context: SubjectTickContext | None = None,
):
    return execute_subject_tick(
        SubjectTickInput(
            case_id=case_id,
            energy=energy,
            cognitive=cognitive,
            safety=safety,
            unresolved_preference=unresolved_preference,
        ),
        context=context,
    )
