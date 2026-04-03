import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    required property var messages

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    ListView {
        id: listView
        anchors.fill: parent
        model: root.messages
        spacing: root.theme.spacing.sm
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        delegate: Item {
            required property var modelData
            width: listView.width
            height: bubble.implicitHeight + root.theme.spacing.xs

            Rectangle {
                id: bubble
                width: Math.min(listView.width * 0.86, bubbleText.implicitWidth + root.theme.spacing.xl)
                anchors.left: modelData.source === "operator" ? undefined : parent.left
                anchors.right: modelData.source === "operator" ? parent.right : undefined
                anchors.leftMargin: 0
                anchors.rightMargin: 0
                radius: root.theme.radii.md
                border.width: root.theme.lines.thin
                border.color: root.theme.colors.divider_subtle
                color: modelData.source === "operator"
                       ? root.theme.colors.panel_secondary
                       : root.theme.colors.input_background

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: root.theme.spacing.sm
                    spacing: root.theme.spacing.xs

                    Text {
                        text: modelData.source === "subject"
                              ? "Subject"
                              : (modelData.source === "operator" ? "Operator" : "State")
                        color: modelData.source === "state"
                               ? root.theme.colors.accent_advisory
                               : root.theme.colors.text_secondary
                        font.family: root.theme.typography.status_label.families[0]
                        font.pixelSize: root.theme.typography.status_label.size
                        font.weight: root.fontWeight("status_label")
                    }

                    Text {
                        id: bubbleText
                        text: modelData.text
                        wrapMode: Text.WordWrap
                        color: root.theme.colors.text_primary
                        font.family: root.theme.typography.body_text.families[0]
                        font.pixelSize: root.theme.typography.body_text.size
                        font.weight: root.fontWeight("body_text")
                    }
                }
            }
        }
    }
}

