import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    required property var theme
    required property var bridge
    required property string content
    property bool active: true
    property bool subtle: false

    color: root.subtle ? root.theme.colors.panel_secondary : root.theme.colors.input_background
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle
    radius: root.theme.radii.sm
    opacity: root.active ? 1.0 : 0.0

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

    Behavior on opacity {
        NumberAnimation {
            duration: root.motionDuration("fade_ms")
            easing.type: Easing.InOutSine
        }
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: root.theme.spacing.sm
        contentWidth: monoText.paintedWidth
        contentHeight: monoText.paintedHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        Text {
            id: monoText
            width: Flickable.view.width
            text: root.content
            color: root.theme.colors.text_secondary
            wrapMode: Text.Wrap
            font.family: root.theme.typography.mono_text.families[0]
            font.pixelSize: root.theme.typography.mono_text.size
            font.weight: Font.Normal
            lineHeight: 1.34
            lineHeightMode: Text.ProportionalHeight
        }
    }
}
