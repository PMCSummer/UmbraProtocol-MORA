from __future__ import annotations

from tests.substrate.l06_testkit import build_l06_context


def test_repairs_are_localized_not_generic() -> None:
    result = build_l06_context('he said "you are tired?"', "l06-repair-localized").discourse_update
    assert result.bundle.repair_triggers
    for trigger in result.bundle.repair_triggers:
        assert trigger.localized_ref_ids
        assert trigger.suggested_clarification_type not in {"generic", "clarify", "can_you_clarify"}
        assert "generic" not in trigger.why_this_is_broken.lower()


def test_repair_classes_cover_localized_trouble_kinds() -> None:
    result = build_l06_context("i did not say that", "l06-repair-classes").discourse_update
    classes = {trigger.repair_class.value for trigger in result.bundle.repair_triggers}
    assert classes.intersection(
        {
            "force_repair",
            "polarity_repair",
            "scope_repair",
            "missing_argument_repair",
            "reference_repair",
        }
    )
