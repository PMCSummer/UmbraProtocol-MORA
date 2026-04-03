import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var theme
    required property bool enabled
    signal submitRequested(string payload)

    color: root.theme.colors.input_background
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle
    radius: root.theme.radii.sm

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: root.theme.spacing.sm
        spacing: root.theme.spacing.sm

        TextArea {
            id: input
            Layout.fillWidth: true
            Layout.fillHeight: true
            enabled: root.enabled
            placeholderText: root.enabled
                             ? "Type for contact..."
                             : "Composer disabled in this state."
            color: root.theme.colors.text_primary
            placeholderTextColor: root.theme.colors.state_muted
            wrapMode: TextArea.Wrap
            background: null
            font.family: root.theme.typography.body_text.families[0]
            font.pixelSize: root.theme.typography.body_text.size
            font.weight: root.fontWeight("body_text")
        }

        Rectangle {
            id: sendSurface
            Layout.preferredWidth: 108
            Layout.fillHeight: true
            radius: root.theme.radii.sm
            border.width: root.theme.lines.thin
            border.color: root.theme.colors.divider_subtle
            color: root.enabled ? root.theme.colors.panel_secondary : root.theme.colors.panel_primary
            opacity: root.enabled ? 1.0 : 0.55

            Text {
                anchors.centerIn: parent
                text: "Transmit"
                color: root.theme.colors.text_primary
                font.family: root.theme.typography.status_label.families[0]
                font.pixelSize: root.theme.typography.status_label.size
                font.weight: root.fontWeight("status_label")
            }

            MouseArea {
                anchors.fill: parent
                enabled: root.enabled
                onClicked: {
                    if (input.text.trim().length === 0) {
                        return
                    }
                    root.submitRequested(input.text)
                    input.text = ""
                }
            }
        }
    }
}

