import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    required property string title
    required property string subtitle
    property bool diagnosticsMode: false
    property bool active: true
    opacity: active ? 1.0 : 0.0
    y: active ? 0 : root.phaseShiftDistance()

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    function reducedMotion() {
        return root.theme.reduced_motion || shellBridge.reducedMotionEnabled
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
