import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    required property var bridge
    required property var entries
    property bool active: true
    property int valueColumnMinWidth: 128
    property int valueColumnMaxWidth: 260

    implicitHeight: statusColumn.implicitHeight

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    function toneColor(tone) {
        if (tone === "warning") return root.theme.colors.accent_warning
        if (tone === "caution") return root.theme.colors.accent_caution
        if (tone === "advisory") return root.theme.colors.accent_advisory
        return root.theme.colors.text_primary
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

    ColumnLayout {
        id: statusColumn
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: root.theme.spacing.xs

        Repeater {
            model: root.entries
            delegate: RowLayout {
                id: row
                required property var modelData
                required property int index
                Layout.fillWidth: true
                spacing: root.theme.spacing.md
                opacity: root.active ? 1.0 : 0.0
                y: root.active ? 0 : root.theme.spacing.xs

                Behavior on opacity {
                    NumberAnimation {
                        duration: root.motionDuration("line_reveal_ms")
                        easing.type: Easing.InOutQuad
                    }
                }

                Behavior on y {
                    NumberAnimation {
                        duration: root.motionDuration("line_reveal_ms")
                        easing.type: Easing.InOutQuad
                    }
                }

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
                    Layout.preferredWidth: Math.max(
                                               root.valueColumnMinWidth,
                                               Math.min(root.valueColumnMaxWidth, row.width * 0.46)
                                           )
                    Layout.maximumWidth: root.valueColumnMaxWidth
                    text: modelData.value
                    color: root.toneColor(modelData.tone)
                    font.family: modelData.mono ? root.theme.typography.mono_text.families[0]
                                                 : root.theme.typography.body_text.families[0]
                    font.pixelSize: modelData.mono ? root.theme.typography.mono_text.size
                                                   : root.theme.typography.body_text.size
                    font.weight: root.fontWeight(modelData.mono ? "mono_text" : "body_text")
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }
            }
        }
    }
}
