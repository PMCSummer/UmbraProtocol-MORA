from desktop_shell.bridge import ShellBridge


def test_bridge_exposes_required_entity_states() -> None:
    bridge = ShellBridge()
    assert bridge.entityStates == ["empty", "active", "waiting", "subject-speaking"]
    assert bridge.entitySurfaceState == "empty"
    assert bridge.dialogueMessages == []
    assert bridge.composerEnabled is True


def test_bridge_state_switch_updates_messages_and_composer() -> None:
    bridge = ShellBridge()
    bridge.setEntitySurfaceState("waiting")
    assert bridge.entitySurfaceState == "waiting"
    assert bridge.composerEnabled is False
    assert bridge.dialogueMessages
    assert any(item["meta"] == "state" for item in bridge.dialogueMessages)

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

