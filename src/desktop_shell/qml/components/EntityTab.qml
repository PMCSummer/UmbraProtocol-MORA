import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: root
    required property var theme
    required property var railModel

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

            Rectangle {
                id: dialoguePanel
                Layout.preferredWidth: parent.width * root.theme.hierarchy.entity_dialogue_weight
                Layout.fillHeight: true
                color: root.theme.colors.panel_primary
                border.width: root.theme.lines.thin
                border.color: root.theme.colors.divider_subtle

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: root.theme.spacing.lg
                    spacing: root.theme.spacing.sm

                    Text {
                        text: "Dialogue"
                        color: root.theme.colors.text_primary
                        font.family: root.theme.typography.section_title.families[0]
                        font.pixelSize: root.theme.typography.section_title.size
                        font.weight: root.fontWeight("section_title")
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: root.theme.colors.input_background
                        border.width: root.theme.lines.thin
                        border.color: root.theme.colors.divider_subtle

                        ScrollView {
                            anchors.fill: parent
                            anchors.margins: root.theme.spacing.md
                            clip: true
                            TextArea {
                                readOnly: true
                                wrapMode: TextArea.Wrap
                                color: root.theme.colors.text_primary
                                textFormat: TextEdit.PlainText
                                text: "Entity presence shell initialized.\nNo mirror engine semantics yet.\nNo language overclaim in this layer."
                                background: null
                                font.family: root.theme.typography.body_text.families[0]
                                font.pixelSize: root.theme.typography.body_text.size
                                font.weight: root.fontWeight("body_text")
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 96
                        color: root.theme.colors.input_background
                        border.width: root.theme.lines.thin
                        border.color: root.theme.colors.divider_subtle

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: root.theme.spacing.sm
                            spacing: root.theme.spacing.sm

                            TextArea {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                placeholderText: "Type to engage the entity shell..."
                                color: root.theme.colors.text_primary
                                placeholderTextColor: root.theme.colors.state_muted
                                background: null
                                wrapMode: TextArea.Wrap
                                font.family: root.theme.typography.body_text.families[0]
                                font.pixelSize: root.theme.typography.body_text.size
                                font.weight: root.fontWeight("body_text")
                            }

                            Rectangle {
                                Layout.preferredWidth: 108
                                Layout.fillHeight: true
                                color: root.theme.colors.panel_secondary
                                border.width: root.theme.lines.thin
                                border.color: root.theme.colors.divider_subtle
                                Text {
                                    anchors.centerIn: parent
                                    text: "Transmit"
                                    color: root.theme.colors.text_primary
                                    font.family: root.theme.typography.status_label.families[0]
                                    font.pixelSize: root.theme.typography.status_label.size
                                    font.weight: root.fontWeight("status_label")
                                }
                            }
                        }
                    }
                }
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

