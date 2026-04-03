import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: root
    required property var theme
    required property var bridge
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
        }

        RowLayout {
            Layout.fillWidth: true
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
                    implicitHeight: 24
                    implicitWidth: stateText.implicitWidth + root.theme.spacing.md

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
                }
            }

            Item {
                anchors.fill: parent
                visible: root.bridge.entitySurfaceState === "empty"
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
            Layout.preferredHeight: 96
            theme: root.theme
            enabled: root.bridge.composerEnabled
            onSubmitRequested: function(payload) {
                root.bridge.submitDraftMessage(payload)
            }
        }
    }
}

