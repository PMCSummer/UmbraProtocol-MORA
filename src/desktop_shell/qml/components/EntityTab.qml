import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: root
    required property var theme
    required property var railModel
    required property var bridge
    property bool active: true
    opacity: active ? 1.0 : 0.0
    y: active ? 0 : root.phaseShiftDistance()

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    function reducedMotion() {
        return root.theme.reduced_motion || root.bridge.reducedMotionEnabled
    }

    function phaseShiftDistance() {
        var base = root.theme.spacing.md
        return reducedMotion() ? Math.round(base * root.theme.motion.reduced_distance_scale) : base
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

    Rectangle {
        anchors.fill: parent
        color: root.theme.colors.app_background
    }

    Behavior on opacity {
        NumberAnimation {
            duration: root.motionDuration("fade_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
        }
    }

    Behavior on y {
        NumberAnimation {
            duration: root.motionDuration("phase_shift_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
        }
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
                active: root.active
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
                    active: root.active
                }

                CriticalRail {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height * root.theme.hierarchy.critical_rail_weight
                    Layout.fillHeight: true
                    theme: root.theme
                    railModel: root.railModel
                    bridge: root.bridge
                    active: root.active
                }
            }
        }
    }
}
