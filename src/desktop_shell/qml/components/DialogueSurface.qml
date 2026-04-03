import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: root
    required property var theme
    required property var bridge
    property bool active: true
    color: root.theme.colors.panel_primary
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    function stateLabel(stateName) {
        if (stateName === "empty") return "Empty"
        if (stateName === "active") return "Active"
        if (stateName === "waiting") return "Waiting"
        if (stateName === "subject-speaking") return "Subject speaking"
        return stateName
    }

    function stateHint(stateName) {
        if (stateName === "empty") return "No dialogue yet. Presence channel is idle."
        if (stateName === "active") return "Contact is active."
        if (stateName === "waiting") return "Awaiting next turn."
        if (stateName === "subject-speaking") return "Subject response in progress."
        return "Unknown state."
    }

    function reducedMotion() {
        return root.theme.reduced_motion || root.bridge.reducedMotionEnabled
    }

    function motionDuration(key) {
        var base = root.theme.motion[key]
        if (base === undefined) {
            return root.theme.motion.fade_ms
        }
        return reducedMotion() ? Math.round(base * root.theme.motion.reduced_duration_scale) : base
    }

    function easingForClass(className) {
        if (className === root.theme.motion.easing_sharp_warning) {
            return Easing.OutCubic
        }
        if (className === root.theme.motion.easing_slow_settle) {
            return Easing.InOutQuad
        }
        return Easing.InOutSine
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.theme.spacing.lg
        spacing: root.theme.spacing.sm

        RowLayout {
            Layout.fillWidth: true
            spacing: root.theme.spacing.sm

            Text {
                text: "Dialogue"
                color: root.theme.colors.text_primary
                font.family: root.theme.typography.section_title.families[0]
                font.pixelSize: root.theme.typography.section_title.size
                font.weight: root.fontWeight("section_title")
            }

            Item { Layout.fillWidth: true }

            Rectangle {
                color: root.theme.colors.panel_secondary
                border.width: root.theme.lines.thin
                border.color: root.theme.colors.divider_subtle
                radius: root.theme.radii.sm
                implicitWidth: badgeText.implicitWidth + root.theme.spacing.md
                implicitHeight: badgeText.implicitHeight + root.theme.spacing.xs
                opacity: root.active ? 1.0 : 0.0
                Behavior on opacity {
                    NumberAnimation {
                        duration: root.motionDuration("fade_ms")
                        easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
                    }
                }
                Text {
                    id: badgeText
                    anchors.centerIn: parent
                    text: root.bridge.entityStateBadge
                    color: root.theme.colors.text_secondary
                    font.family: root.theme.typography.status_label.families[0]
                    font.pixelSize: root.theme.typography.status_label.size
                    font.weight: root.fontWeight("status_label")
                }
            }
        }

        Text {
            text: root.stateHint(root.bridge.entitySurfaceState)
            color: root.theme.colors.text_secondary
            font.family: root.theme.typography.secondary_text.families[0]
            font.pixelSize: root.theme.typography.secondary_text.size
            font.weight: root.fontWeight("secondary_text")
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: chipsFlow.implicitHeight

            Flow {
                id: chipsFlow
                width: parent.width
                spacing: root.theme.spacing.xs

                Repeater {
                    model: root.bridge.entityStates
                    delegate: Rectangle {
                        required property var modelData
                        radius: root.theme.radii.sm
                        border.width: root.theme.lines.thin
                        border.color: root.theme.colors.divider_subtle
                        color: root.bridge.entitySurfaceState === modelData
                               ? root.theme.colors.panel_secondary
                               : root.theme.colors.panel_primary
                        implicitHeight: 26
                        implicitWidth: stateText.implicitWidth + root.theme.spacing.md
                        opacity: root.active ? 1.0 : 0.0

                        Text {
                            id: stateText
                            anchors.centerIn: parent
                            text: root.stateLabel(modelData)
                            color: root.bridge.entitySurfaceState === modelData
                                   ? root.theme.colors.text_primary
                                   : root.theme.colors.text_secondary
                            font.family: root.theme.typography.status_label.families[0]
                            font.pixelSize: root.theme.typography.status_label.size
                            font.weight: root.fontWeight("status_label")
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: root.bridge.setEntitySurfaceState(parent.modelData)
                        }

                        Behavior on color {
                            ColorAnimation {
                                duration: root.motionDuration("fade_ms")
                                easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
                            }
                        }
                        Behavior on opacity {
                            NumberAnimation {
                                duration: root.motionDuration("line_reveal_ms")
                                easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.theme.colors.input_background
            border.width: root.theme.lines.thin
            border.color: root.theme.colors.divider_subtle
            radius: root.theme.radii.sm

            Loader {
                anchors.fill: parent
                anchors.margins: root.theme.spacing.md
                active: root.bridge.entitySurfaceState !== "empty"
                sourceComponent: MessageList {
                    theme: root.theme
                    messages: root.bridge.dialogueMessages
                    reducedMotion: root.reducedMotion()
                }
            }

            Item {
                anchors.fill: parent
                visible: root.bridge.entitySurfaceState === "empty"
                opacity: visible ? 1.0 : 0.0
                Behavior on opacity {
                    NumberAnimation {
                        duration: root.motionDuration("fade_ms")
                        easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
                    }
                }
                Column {
                    anchors.centerIn: parent
                    spacing: root.theme.spacing.sm
                    Text {
                        text: "No exchange yet"
                        color: root.theme.colors.text_primary
                        font.family: root.theme.typography.body_text.families[0]
                        font.pixelSize: root.theme.typography.body_text.size
                        font.weight: root.fontWeight("body_text")
                    }
                    Text {
                        text: "Begin contact to open the dialogue lane."
                        color: root.theme.colors.text_secondary
                        font.family: root.theme.typography.secondary_text.families[0]
                        font.pixelSize: root.theme.typography.secondary_text.size
                        font.weight: root.fontWeight("secondary_text")
                    }
                }
            }
        }

        DialogueComposer {
            Layout.fillWidth: true
            Layout.preferredHeight: 112
            theme: root.theme
            bridge: root.bridge
            enabled: root.bridge.composerEnabled
            onSubmitRequested: function(payload) {
                root.bridge.submitDraftMessage(payload)
            }
        }
    }
}
