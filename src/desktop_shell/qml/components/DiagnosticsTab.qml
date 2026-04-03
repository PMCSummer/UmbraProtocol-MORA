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

    property var runtimeRows: [
        {"label": "runtime_revision", "value": "r:0000", "mono": true},
        {"label": "schema_bundle", "value": "desktop_shell.v1", "mono": true},
        {"label": "qml_stack", "value": "QtQuick+QtQuick3D", "mono": true},
        {"label": "reduced_motion", "value": root.bridge.reducedMotionEnabled ? "true" : "false", "mono": true}
    ]

    property var machineRecords: [
        {"title": "bridge.entity_state", "state": "ok", "meta": "value=subject-speaking"},
        {"title": "mirror.semantic_input", "state": "ok", "meta": "p:0.56 u:0.34 c:0.28 r:0.36"},
        {"title": "lexical.handoff_status", "state": "bounded", "meta": "missing_strong_claim=true"},
        {"title": "dictum.candidate_pipe", "state": "ok", "meta": "candidate_only=true"}
    ]

    readonly property string payloadText:
        "{\n"
        + "  \"surface\": \"entity_shell\",\n"
        + "  \"mode\": \"diagnostics_raw\",\n"
        + "  \"mirror_band\": \"advisory\",\n"
        + "  \"trace_head\": \"ev:000186\",\n"
        + "  \"bounded_claims\": true\n"
        + "}"

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
                text: "Diagnostics"
                color: root.theme.colors.text_primary
                font.family: root.theme.typography.display_title.families[0]
                font.pixelSize: root.theme.typography.display_title.size
                font.weight: root.fontWeight("display_title")
            }

            Text {
                text: "Structured machine-facing surface. Raw, bounded, readable."
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
                Layout.preferredWidth: parent.width * 0.5
                spacing: root.theme.spacing.md

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 180
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Runtime Envelope"
                    subtitle: "Compact machine identifiers."
                    StatusBlock {
                        Layout.fillWidth: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        entries: root.runtimeRows
                    }
                }

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Recent Machine Records"
                    subtitle: "Bounded raw records, no debug landfill."
                    CausalList {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        items: root.machineRecords
                        monoMeta: true
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.5
                spacing: root.theme.spacing.md

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 188
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Signal Presence Matrix"
                    subtitle: "Miniature machine-state grid."

                    GridLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        columns: 6
                        rowSpacing: root.theme.spacing.xs
                        columnSpacing: root.theme.spacing.xs

                        Repeater {
                            model: 24
                            delegate: Rectangle {
                                required property int index
                                Layout.preferredWidth: 14
                                Layout.preferredHeight: 10
                                radius: 2
                                border.width: root.theme.lines.thin
                                border.color: root.theme.colors.divider_subtle
                                color: index % 7 === 0
                                       ? root.theme.colors.accent_advisory
                                       : (index % 11 === 0
                                          ? root.theme.colors.accent_caution
                                          : root.theme.colors.panel_primary)
                                opacity: root.active ? 0.88 : 0.0
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
                    title: "Raw Payload Slice"
                    subtitle: "Structured technical output pane."

                    MonoBlock {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        subtle: true
                        content: root.payloadText
                    }
                }
            }
        }
    }
}
