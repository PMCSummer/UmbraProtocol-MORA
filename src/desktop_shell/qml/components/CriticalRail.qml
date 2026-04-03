import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var theme
    required property var railModel
    required property var bridge
    property bool active: true
    color: root.theme.colors.panel_primary
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
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

        Text {
            text: "Critical Rail"
            color: root.theme.colors.text_primary
            font.family: root.theme.typography.section_title.families[0]
            font.pixelSize: root.theme.typography.section_title.size
            font.weight: root.fontWeight("section_title")
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: root.theme.spacing.xs

                Repeater {
                    model: root.railModel
                    delegate: ColumnLayout {
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        spacing: root.theme.spacing.xs
                        opacity: root.active ? 1.0 : 0.0
                        y: root.active ? 0.0 : root.theme.spacing.xs

                        Behavior on opacity {
                            NumberAnimation {
                                duration: root.motionDuration("line_reveal_ms")
                                easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
                            }
                        }
                        Behavior on y {
                            NumberAnimation {
                                duration: root.motionDuration("line_reveal_ms")
                                easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
                            }
                        }

                        RowLayout {
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
                                maximumLineCount: 1
                            }

                            Text {
                                Layout.preferredWidth: Math.max(118, Math.min(220, parent.width * 0.44))
                                text: modelData.value
                                color: root.theme.colors.text_primary
                                font.family: root.theme.typography.mono_text.families[0]
                                font.pixelSize: root.theme.typography.mono_text.size
                                font.weight: root.fontWeight("mono_text")
                                horizontalAlignment: Text.AlignRight
                                elide: Text.ElideRight
                                maximumLineCount: 1
                            }
                        }

                        Rectangle {
                            visible: index === 4 || index === 7
                            Layout.fillWidth: true
                            Layout.preferredHeight: root.theme.lines.thin
                            color: root.theme.colors.divider_subtle
                            opacity: root.active ? 1.0 : 0.0
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
        }
    }
}
