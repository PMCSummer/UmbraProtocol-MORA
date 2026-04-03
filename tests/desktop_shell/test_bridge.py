from desktop_shell.bridge import ShellBridge


def test_bridge_exposes_required_entity_states() -> None:
    bridge = ShellBridge()
    assert bridge.entityStates == ["empty", "active", "waiting", "subject-speaking"]
    assert bridge.entitySurfaceState == "empty"
    assert bridge.dialogueMessages == []
    assert bridge.composerEnabled is True
    semantic = bridge.mirrorSemanticInput
    assert set(semantic.keys()) == {
        "pressure_level",
        "uncertainty_level",
        "conflict_level",
        "recovery_level",
        "warning_level",
    }
    assert isinstance(bridge.reducedMotionEnabled, bool)


def test_bridge_state_switch_updates_messages_and_composer() -> None:
    bridge = ShellBridge()
    empty_semantic = bridge.mirrorSemanticInput
    bridge.setEntitySurfaceState("waiting")
    assert bridge.entitySurfaceState == "waiting"
    assert bridge.composerEnabled is False
    assert bridge.dialogueMessages
    assert any(item["meta"] == "state" for item in bridge.dialogueMessages)
    waiting_semantic = bridge.mirrorSemanticInput
    assert waiting_semantic["uncertainty_level"] > empty_semantic["uncertainty_level"]

    bridge.setEntitySurfaceState("active")
    assert bridge.entitySurfaceState == "active"
    assert bridge.composerEnabled is True
    assert bridge.dialogueMessages


def test_bridge_submit_message_enters_subject_speaking_mode() -> None:
    bridge = ShellBridge()
    bridge.setEntitySurfaceState("active")
    bridge.submitDraftMessage("Status check")

    assert bridge.entitySurfaceState == "subject-speaking"
    assert bridge.composerEnabled is False
    assert bridge.dialogueMessages
    assert any(item["source"] == "operator" for item in bridge.dialogueMessages)
    assert any(item["meta"] == "state" for item in bridge.dialogueMessages)


def test_bridge_semantic_setters_are_clamped_and_updatable() -> None:
    bridge = ShellBridge()
    updated = bridge.setMirrorSemanticLevelsWithWarning(1.2, -0.5, 0.4, 0.3, 2.0)

    assert updated is True
    semantic = bridge.mirrorSemanticInput
    assert semantic["pressure_level"] == 1.0
    assert semantic["uncertainty_level"] == 0.0
    assert semantic["conflict_level"] == 0.4
    assert semantic["recovery_level"] == 0.3
    assert semantic["warning_level"] == 1.0


def test_bridge_reduced_motion_toggle() -> None:
    bridge = ShellBridge()
    initial = bridge.reducedMotionEnabled
    bridge.setReducedMotionEnabled(not initial)
    assert bridge.reducedMotionEnabled is (not initial)
    assert bridge.reducedMotionPreferred() is (not initial)
