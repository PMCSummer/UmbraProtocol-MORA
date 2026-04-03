import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: root
    required property var theme
    required property var bridge
    property bool active: true
    opacity: active ? 1.0 : 0.0
    y: active ? 0 : root.phaseShiftDistance()

    property var viabilitySummary: [
        {"label": "Pressure Band", "value": "elevated", "tone": "caution"},
        {"label": "Recoverability", "value": "partial", "tone": "advisory"},
        {"label": "Regulation Bias", "value": "protective"},
        {"label": "Escalation Stage", "value": "bounded-2", "mono": true}
    ]

    property var viabilityItems: [
        {"title": "mixed_deterioration cap enforced", "state": "active", "tone": "caution", "meta": "no_strong_override_claim=true"},
        {"title": "compatibility marker remained stable", "state": "stable", "meta": "formula_version:ok"},
        {"title": "recovery signal weak but present", "state": "partial", "meta": "recoverability:0.42"},
        {"title": "uncertainty gate preserved", "state": "kept", "meta": "boundary_uncertain=true"}
    ]

    readonly property string controlText:
        "pressure=0.58\n"
        + "uncertainty=0.37\n"
        + "conflict=0.29\n"
        + "recovery=0.41\n"
        + "downstream_gate=bounded_accept"

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
        if (className === root.theme.motion.easing_sharp_warning) return Easing.OutCubic
        if (className === root.theme.motion.easing_slow_settle) return Easing.InOutQuad
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
                text: "Viability"
                color: root.theme.colors.text_primary
                font.family: root.theme.typography.display_title.families[0]
                font.pixelSize: root.theme.typography.display_title.size
                font.weight: root.fontWeight("display_title")
            }

            Text {
                text: "Regulatory balance and recoverability reading surface."
                color: root.theme.colors.text_secondary
                font.family: root.theme.typography.secondary_text.families[0]
                font.pixelSize: root.theme.typography.secondary_text.size
                font.weight: root.fontWeight("secondary_text")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: root.theme.spacing.md

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.54
                spacing: root.theme.spacing.md

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 180
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Pressure & Recovery"
                    subtitle: "Current regulatory posture."
                    StatusBlock {
                        Layout.fillWidth: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        entries: root.viabilitySummary
                    }
                }

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Active Regulation Signals"
                    subtitle: "Load-bearing viability markers only."
                    CausalList {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        items: root.viabilityItems
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.46
                spacing: root.theme.spacing.md

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 194
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Balance Minimap"
                    subtitle: "Compact tension strip. No chart sprawl."

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: root.theme.spacing.sm

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 8
                            color: root.theme.colors.panel_primary
                            radius: 4
                            border.width: root.theme.lines.thin
                            border.color: root.theme.colors.divider_subtle
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: parent.width * 0.58
                                radius: 4
                                color: root.theme.colors.accent_caution
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 8
                            color: root.theme.colors.panel_primary
                            radius: 4
                            border.width: root.theme.lines.thin
                            border.color: root.theme.colors.divider_subtle
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: parent.width * 0.41
                                radius: 4
                                color: root.theme.colors.accent_advisory
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 8
                            color: root.theme.colors.panel_primary
                            radius: 4
                            border.width: root.theme.lines.thin
                            border.color: root.theme.colors.divider_subtle
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: parent.width * 0.29
                                radius: 4
                                color: root.theme.colors.text_secondary
                            }
                        }
                    }
                }

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Control Surface"
                    subtitle: "Bounded viability machine slice."

                    MonoBlock {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        content: root.controlText
                    }
                }
            }
        }
    }
}
