import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var theme
    required property var bridge
    property string title: ""
    property string subtitle: ""
    property bool active: true
    default property alias contentData: contentColumn.data

    color: root.theme.colors.panel_secondary
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle
    radius: root.theme.radii.sm
    opacity: root.active ? 1.0 : 0.0
    y: root.active ? 0 : root.phaseShiftDistance()

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

    function phaseShiftDistance() {
        var base = root.theme.spacing.sm
        return reducedMotion() ? Math.round(base * root.theme.motion.reduced_distance_scale) : base
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
        anchors.margins: root.theme.spacing.md
        spacing: root.theme.spacing.sm

        ColumnLayout {
            Layout.fillWidth: true
            spacing: root.theme.spacing.xxs

            Text {
                text: root.title
                color: root.theme.colors.text_primary
                font.family: root.theme.typography.section_title.families[0]
                font.pixelSize: root.theme.typography.section_title.size
                font.weight: root.fontWeight("section_title")
            }

            Text {
                visible: root.subtitle.length > 0
                text: root.subtitle
                color: root.theme.colors.text_secondary
                font.family: root.theme.typography.secondary_text.families[0]
                font.pixelSize: root.theme.typography.secondary_text.size
                font.weight: root.fontWeight("secondary_text")
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                maximumLineCount: 2
                elide: Text.ElideRight
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: root.theme.lines.thin
            color: root.theme.colors.divider_subtle
            opacity: 0.8
        }

        ColumnLayout {
            id: contentColumn
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: root.theme.spacing.sm
        }
    }
}
