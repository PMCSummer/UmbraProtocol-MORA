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

    property var interpretationSummary: [
        {"label": "Active Dictum Window", "value": "candidate-only", "tone": "advisory"},
        {"label": "Lexical Basis", "value": "lexicon-backed + capped", "mono": true},
        {"label": "Reference Status", "value": "partially unresolved"},
        {"label": "Bounded Confidence", "value": "0.44", "mono": true}
    ]

    property var ambiguityMarkers: [
        {"title": "polysemy: \"charge\"", "state": "open", "tone": "caution", "meta": "sense family unresolved"},
        {"title": "referent: \"it\"", "state": "deferred", "meta": "context insufficient"},
        {"title": "scope: negation cluster", "state": "bounded", "meta": "no final collapse"},
        {"title": "fallback provenance", "state": "explicit", "meta": "heuristic_capped=true"}
    ]

    property var decompositionLayers: [
        {"name": "surface spans", "level": 0.84},
        {"name": "morphosyntax candidates", "level": 0.68},
        {"name": "lexical grounding", "level": 0.58},
        {"name": "dictum candidates", "level": 0.47}
    ]

    readonly property string boundednessText:
        "no_final_resolution=true\n"
        + "unknown_preserved=true\n"
        + "partial_hypothesis_visible=true\n"
        + "fallback_no_strong_claim=true\n"
        + "dictum_candidates_only=true"

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
                text: "Language"
                color: root.theme.colors.text_primary
                font.family: root.theme.typography.display_title.families[0]
                font.pixelSize: root.theme.typography.display_title.size
                font.weight: root.fontWeight("display_title")
            }

            Text {
                text: "Layered reading of interpretation and bounded ambiguity."
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
                Layout.preferredWidth: parent.width * 0.55
                spacing: root.theme.spacing.md

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 180
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Interpretation Summary"
                    subtitle: "Current language contour posture."
                    StatusBlock {
                        Layout.fillWidth: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        entries: root.interpretationSummary
                    }
                }

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Active Ambiguity Markers"
                    subtitle: "Unresolved branches retained explicitly."
                    CausalList {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        items: root.ambiguityMarkers
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.45
                spacing: root.theme.spacing.md

                SectionPanel {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 208
                    theme: root.theme
                    bridge: root.bridge
                    active: root.active
                    title: "Decomposition Stack"
                    subtitle: "Miniature layered representation."

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: root.theme.spacing.sm
                        Repeater {
                            model: root.decompositionLayers
                            delegate: ColumnLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: root.theme.spacing.xxs

                                Text {
                                    text: modelData.name
                                    color: root.theme.colors.text_secondary
                                    font.family: root.theme.typography.status_label.families[0]
                                    font.pixelSize: root.theme.typography.status_label.size
                                    font.weight: root.fontWeight("status_label")
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 6
                                    color: root.theme.colors.panel_primary
                                    radius: 3
                                    border.width: root.theme.lines.thin
                                    border.color: root.theme.colors.divider_subtle

                                    Rectangle {
                                        anchors.left: parent.left
                                        anchors.top: parent.top
                                        anchors.bottom: parent.bottom
                                        width: parent.width * modelData.level
                                        color: modelData.level > 0.7
                                               ? root.theme.colors.accent_advisory
                                               : root.theme.colors.text_secondary
                                        radius: 3
                                        opacity: root.active ? 0.8 : 0.0
                                        Behavior on width {
                                            NumberAnimation {
                                                duration: root.motionDuration("line_reveal_ms")
                                                easing.type: Easing.InOutQuad
                                            }
                                        }
                                    }
                                }
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
                    title: "Boundedness"
                    subtitle: "No hidden overclaim in language path."

                    MonoBlock {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        bridge: root.bridge
                        active: root.active
                        content: root.boundednessText
                    }
                }
            }
        }
    }
}
