import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: root
    required property var theme
    required property var railModel
    required property var bridge

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

        ColumnLayout {
            Layout.fillWidth: true
            spacing: root.theme.spacing.xs

            Text {
                text: "Entity"
                color: root.theme.colors.text_primary
                font.family: root.theme.typography.display_title.families[0]
                font.pixelSize: root.theme.typography.display_title.size
                font.weight: root.fontWeight("display_title")
            }

            Text {
                text: "Dialogue-first shell with bounded lexical and regulation surfaces."
                color: root.theme.colors.text_secondary
                font.family: root.theme.typography.secondary_text.families[0]
                font.pixelSize: root.theme.typography.secondary_text.size
                font.weight: root.fontWeight("secondary_text")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: root.theme.spacing.lg

            DialogueSurface {
                Layout.preferredWidth: parent.width * root.theme.hierarchy.entity_dialogue_weight
                Layout.fillHeight: true
                theme: root.theme
                bridge: root.bridge
            }

            ColumnLayout {
                Layout.preferredWidth: parent.width * root.theme.hierarchy.entity_side_weight
                Layout.fillHeight: true
                spacing: root.theme.spacing.lg

                MirrorHost3D {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height * root.theme.hierarchy.mirror_host_weight
                    Layout.fillHeight: true
                    theme: root.theme
                    bridge: root.bridge
                }

                CriticalRail {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height * root.theme.hierarchy.critical_rail_weight
                    Layout.fillHeight: true
                    theme: root.theme
                    railModel: root.railModel
                }
            }
        }
    }
}
