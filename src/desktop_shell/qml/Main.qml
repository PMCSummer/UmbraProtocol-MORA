import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: root
    width: 1460
    height: 900
    minimumWidth: 1120
    minimumHeight: 720
    visible: true
    title: "Umbra Protocol // Entity Shell"
    color: shellTheme.colors.app_background
    property bool reducedMotion: shellTheme.reduced_motion || shellBridge.reducedMotionEnabled

    function motionDuration(key) {
        var base = shellTheme.motion[key]
        if (base === undefined) {
            return shellTheme.motion.fade_ms
        }
        return reducedMotion ? Math.round(base * shellTheme.motion.reduced_duration_scale) : base
    }

    function easingForClass(className) {
        if (className === shellTheme.motion.easing_sharp_warning) {
            return Easing.OutCubic
        }
        if (className === shellTheme.motion.easing_slow_settle) {
            return Easing.InOutQuad
        }
        return Easing.InOutSine
    }

    function fontWeight(roleName) {
        var value = shellTheme.typography[roleName].weight
        return value === "bold" ? Font.DemiBold : Font.Normal
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: shellTheme.colors.divider_subtle
        }

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            spacing: 0
            background: Rectangle { color: shellTheme.colors.app_background }

            Repeater {
                model: ["Entity", "Trace", "Language", "Viability", "Diagnostics"]
                TabButton {
                    required property string modelData
                    text: modelData
                    height: 42
                    leftPadding: shellTheme.spacing.lg
                    rightPadding: shellTheme.spacing.lg
                    font.family: shellTheme.typography.status_label.families[0]
                    font.pixelSize: shellTheme.typography.status_label.size
                    font.weight: root.fontWeight("status_label")
                    contentItem: Text {
                        text: parent.text
                        color: parent.checked ? shellTheme.colors.text_primary : shellTheme.colors.text_secondary
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.checked ? shellTheme.colors.panel_primary : shellTheme.colors.panel_secondary
                        border.width: 0
                        Behavior on color {
                            ColorAnimation {
                                duration: root.motionDuration("fade_ms")
                                easing.type: root.easingForClass(shellTheme.motion.easing_soft_standard)
                            }
                        }
                    }
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            EntityTab {
                theme: shellTheme
                railModel: shellBridge.criticalRail
                bridge: shellBridge
                active: tabBar.currentIndex === 0
            }

            PlaceholderTab {
                theme: shellTheme
                title: "Trace"
                subtitle: "Trace stream shell. Provenance lanes reserved for next increment."
                active: tabBar.currentIndex === 1
            }

            PlaceholderTab {
                theme: shellTheme
                title: "Language"
                subtitle: "Language shell. Lexical/dictum panes remain bounded and staged."
                active: tabBar.currentIndex === 2
            }

            PlaceholderTab {
                theme: shellTheme
                title: "Viability"
                subtitle: "Viability shell. Pressure/escalation visuals reserved for dedicated step."
                active: tabBar.currentIndex === 3
            }

            PlaceholderTab {
                theme: shellTheme
                title: "Diagnostics"
                subtitle: "Machine-facing diagnostics shell with restrained raw hierarchy."
                diagnosticsMode: true
                active: tabBar.currentIndex === 4
            }
        }
    }
}
