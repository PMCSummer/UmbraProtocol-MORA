import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var theme
    required property var railModel
    color: root.theme.colors.panel_primary
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.theme.spacing.lg
        spacing: root.theme.spacing.xs

        Text {
            text: "Critical Rail"
            color: root.theme.colors.text_primary
            font.family: root.theme.typography.section_title.families[0]
            font.pixelSize: root.theme.typography.section_title.size
            font.weight: root.fontWeight("section_title")
        }

        Repeater {
            model: root.railModel
            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: root.theme.spacing.md

                Text {
                    Layout.fillWidth: true
                    text: modelData.label
                    color: root.theme.colors.text_secondary
                    font.family: root.theme.typography.status_label.families[0]
                    font.pixelSize: root.theme.typography.status_label.size
                    font.weight: root.fontWeight("status_label")
                    elide: Text.ElideRight
                }

                Text {
                    text: modelData.value
                    color: root.theme.colors.text_primary
                    font.family: root.theme.typography.mono_text.families[0]
                    font.pixelSize: root.theme.typography.mono_text.size
                    font.weight: root.fontWeight("mono_text")
                    horizontalAlignment: Text.AlignRight
                }
            }
        }
    }
}

