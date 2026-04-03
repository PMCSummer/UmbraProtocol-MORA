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
            }

            PlaceholderTab {
                theme: shellTheme
                title: "Trace"
                subtitle: "Trace stream shell. Provenance lanes reserved for next increment."
            }

            PlaceholderTab {
                theme: shellTheme
                title: "Language"
                subtitle: "Language shell. Lexical/dictum panes remain bounded and staged."
            }

            PlaceholderTab {
                theme: shellTheme
                title: "Viability"
                subtitle: "Viability shell. Pressure/escalation visuals reserved for dedicated step."
            }

            PlaceholderTab {
                theme: shellTheme
                title: "Diagnostics"
                subtitle: "Machine-facing diagnostics shell with restrained raw hierarchy."
                diagnosticsMode: true
            }
        }
    }
}

