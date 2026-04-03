import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    required property var bridge
    required property var items
    property bool active: true
    property bool monoMeta: false

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

    ListView {
        id: listView
        anchors.fill: parent
        model: root.items
        clip: true
        spacing: root.theme.spacing.xs
        boundsBehavior: Flickable.StopAtBounds

        delegate: Rectangle {
            required property var modelData
            required property int index
            width: listView.width
            height: row.implicitHeight + root.theme.spacing.sm
            color: root.theme.colors.panel_primary
            border.width: root.theme.lines.thin
            border.color: root.theme.colors.divider_subtle
            radius: root.theme.radii.sm
            opacity: root.active ? 1.0 : 0.0
            x: 0

            Behavior on opacity {
                NumberAnimation {
                    duration: root.motionDuration("fade_ms")
                    easing.type: Easing.InOutSine
                }
            }

            ColumnLayout {
                id: row
                anchors.fill: parent
                anchors.margins: root.theme.spacing.sm
                spacing: root.theme.spacing.xxs

                RowLayout {
                    Layout.fillWidth: true
                    spacing: root.theme.spacing.sm

                    Text {
                        Layout.fillWidth: true
                        text: modelData.title
                        color: root.theme.colors.text_primary
                        font.family: root.theme.typography.body_text.families[0]
                        font.pixelSize: root.theme.typography.body_text.size
                        font.weight: root.fontWeight("body_text")
                        elide: Text.ElideRight
                    }

                    Text {
                        text: modelData.state
                        color: modelData.tone === "warning"
                               ? root.theme.colors.accent_warning
                               : (modelData.tone === "caution"
                                  ? root.theme.colors.accent_caution
                                  : root.theme.colors.text_secondary)
                        font.family: root.theme.typography.status_label.families[0]
                        font.pixelSize: root.theme.typography.status_label.size
                        font.weight: root.fontWeight("status_label")
                    }
                }

                Text {
                    visible: modelData.meta !== undefined && modelData.meta !== null
                    text: modelData.meta
                    color: root.theme.colors.text_secondary
                    font.family: root.monoMeta
                                 ? root.theme.typography.mono_text.families[0]
                                 : root.theme.typography.secondary_text.families[0]
                    font.pixelSize: root.monoMeta
                                    ? root.theme.typography.mono_text.size
                                    : root.theme.typography.secondary_text.size
                    font.weight: root.fontWeight(root.monoMeta ? "mono_text" : "secondary_text")
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
