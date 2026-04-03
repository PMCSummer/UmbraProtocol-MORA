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

    property var traceSummary: [
        {"label": "Current Transition", "value": "tr:observe->align", "mono": true},
        {"label": "Stage Edge", "value": "L03 -> L04", "mono": true},
        {"label": "Continuity", "value": "stable", "tone": "advisory"},
        {"label": "Trace Density", "value": "bounded"}
    ]

    property var traceEvents: [
        {"title": "Lexicon gate produced capped ambiguity markers", "state": "accepted", "tone": "advisory", "meta": "ev:000183 · gate:bounded"},
        {"title": "L03 grounding retained unresolved reference branch", "state": "kept", "tone": "advisory", "meta": "ev:000184 · branch:pending"},
        {"title": "L04 dictum candidates emitted with bounded confidence", "state": "emitted", "meta": "ev:000185 · conf:0.44"},
        {"title": "Regulation pressure updated without escalation", "state": "steady", "meta": "ev:000186 · p:0.41"}
    ]

    readonly property string provenanceText:
        "trace_head=ev:000186\n"
        + "chain=ev:000183->ev:000184->ev:000185->ev:000186\n"
        + "source=f01.transition_log\n"
        + "lineage=l02:lattice/lexicon:l3/l4\n"
        + "integrity=bounded-preserved"

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
                text: "Trace"
                color: root.theme.colors.text_primary
                font.family: root.theme.typography.display_title.families[0]
                font.pixelSize: root.theme.typography.display_title.size
                font.weight: root.fontWeight("display_title")
            }

            Text {
                text: "Transition and provenance reading surface."
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
                Layout.preferredWidth: parent.width * 0.58
                spacing: root.theme.spacing.md

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 170
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Trace Summary"
                    subtitle: "Current transition posture and continuity markers."
                    StatusBlock {
                        Layout.fillWidth: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        entries: root.traceSummary
                    }
                }

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Recent Transitions"
                    subtitle: "Chronological chain without raw log clutter."
                    CausalList {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        items: root.traceEvents
                        monoMeta: true
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.42
                spacing: root.theme.spacing.md

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 180
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Transition Chain"
                    subtitle: "Miniature edge-strip for causal sequencing."

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        property int nodeCount: 7
                        Repeater {
                            model: nodeCount
                            delegate: Rectangle {
                                required property int index
                                readonly property real spacingStep: (parent.width - root.theme.spacing.md * 2) / (nodeCount - 1)
                                width: 10
                                height: 10
                                radius: 5
                                x: root.theme.spacing.sm + index * spacingStep - width / 2
                                y: parent.height * 0.45
                                color: index >= nodeCount - 2 ? root.theme.colors.accent_advisory : root.theme.colors.geometry_white
                                opacity: root.active ? 1.0 : 0.0
                                Behavior on opacity {
                                    NumberAnimation {
                                        duration: root.motionDuration("line_reveal_ms")
                                        easing.type: Easing.InOutQuad
                                    }
                                }
                            }
                        }

                        Repeater {
                            model: nodeCount - 1
                            delegate: Rectangle {
                                required property int index
                                readonly property real spacingStep: (parent.width - root.theme.spacing.md * 2) / (nodeCount - 1)
                                width: spacingStep - 8
                                height: 1
                                x: root.theme.spacing.sm + index * spacingStep + 5
                                y: parent.height * 0.45 + 4
                                color: root.theme.colors.divider_subtle
                                opacity: root.active ? 0.9 : 0.0
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
                    title: "Provenance Slice"
                    subtitle: "Compact machine-facing trace lineage."

                    MonoBlock {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        content: root.provenanceText
                    }
                }
            }
        }
    }
}
