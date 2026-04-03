import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    required property string title
    required property string subtitle
    property bool diagnosticsMode: false

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.colors.app_background
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.theme.spacing.xl
        spacing: root.theme.spacing.md

        Text {
            text: root.title
            color: root.theme.colors.text_primary
            font.family: root.theme.typography.display_title.families[0]
            font.pixelSize: root.theme.typography.display_title.size
            font.weight: root.fontWeight("display_title")
        }

        Text {
            text: root.subtitle
            color: root.theme.colors.text_secondary
            font.family: root.theme.typography.secondary_text.families[0]
            font.pixelSize: root.theme.typography.secondary_text.size
            font.weight: root.fontWeight("secondary_text")
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.theme.colors.panel_secondary
            border.width: root.theme.lines.thin
            border.color: root.theme.colors.divider_subtle

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: root.theme.spacing.lg
                spacing: root.theme.spacing.sm

                Text {
                    text: "Shell Placeholder"
                    color: root.theme.colors.text_primary
                    font.family: root.theme.typography.section_title.families[0]
                    font.pixelSize: root.theme.typography.section_title.size
                    font.weight: root.fontWeight("section_title")
                }

                Text {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    wrapMode: Text.WordWrap
                    color: root.diagnosticsMode ? root.theme.colors.text_secondary : root.theme.colors.text_primary
                    text: "Foundation-only tab shell.\nNo deep engine wiring in this increment.\nReserved for next bounded implementation step."
                    font.family: root.diagnosticsMode
                                 ? root.theme.typography.mono_text.families[0]
                                 : root.theme.typography.body_text.families[0]
                    font.pixelSize: root.diagnosticsMode
                                    ? root.theme.typography.mono_text.size
                                    : root.theme.typography.body_text.size
                    font.weight: root.fontWeight(root.diagnosticsMode ? "mono_text" : "body_text")
                }
            }
        }
    }
}

