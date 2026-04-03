pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window

Rectangle {
    id: root
    required property var theme
    required property var bridge
    property bool active: true
    property bool runtimeActive: root.active && root.visible && (!Window.window || Window.window.active)
    opacity: active ? 1.0 : 0.0
    y: active ? 0 : root.phaseShiftDistance()
    color: root.theme.colors.panel_secondary
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle

    property real semanticPressure: 0.12
    property real semanticUncertainty: 0.10
    property real semanticConflict: 0.08
    property real semanticRecovery: 0.76
    property real semanticWarning: 0.0

    property real structuralAsymmetry: 0.0
    property real densityLevel: 0.0
    property real echoLevel: 0.0
    property real centerOffsetX: 0.0
    property real centerOffsetY: 0.0
    property real orbitalActivity: 0.0
    property real speedScalar: 1.0
    property real driftIrregularity: 0.0
    property int semanticBand: 0
    property bool warningActive: false

    property color mainLineColor: root.theme.colors.geometry_white
    property color secondaryLineColor: root.theme.colors.text_secondary
    property color accentLineColor: root.theme.colors.geometry_white

    property int sectorCount: 8
    property real lineWidth: 1.28
    property real outerRotation: 0.0
    property real innerRotation: 0.0
    property real seamRotation: 0.0
    property real phaseSkew: 0.0
    property real anomalyPulse: 0.0
    property real targetPhaseSkew: 0.0
    property real targetAnomalyPulse: 0.0
    property int orbitalNodeCount: 0
    property real coreScaleX: 1.0
    property real coreScaleY: 1.0
    property real ghostOpacity: 0.0
    property real detailOpacity: 0.58
    property real centerOffsetPxX: centerOffsetX * (reducedMotion() ? 0.36 : 0.72)
    property real centerOffsetPxY: centerOffsetY * (reducedMotion() ? 0.36 : 0.72)
    property real driftAxisX: 0.42
    property real driftAxisY: -0.2

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
        if (className === root.theme.motion.easing_sharp_warning) {
            return Easing.OutCubic
        }
        if (className === root.theme.motion.easing_slow_settle) {
            return Easing.InOutQuad
        }
        return Easing.InOutSine
    }

    function semanticScale() {
        return reducedMotion() ? root.theme.mirror_semantics.reduced_semantic_scale : 1.0
    }

    function intervalScale() {
        return reducedMotion() ? root.theme.mirror.reduced_interval_scale : 1.0
    }

    function clamp(v, lo, hi) {
        return Math.max(lo, Math.min(hi, v))
    }

    function randomBetween(minValue, maxValue) {
        return minValue + (maxValue - minValue) * Math.random()
    }

    function levelFromInput(payload, key, fallback) {
        if (!payload || payload[key] === undefined || payload[key] === null) {
            return fallback
        }
        return clamp(Number(payload[key]), 0.0, 1.0)
    }

    function nextDriftIntervalMs() {
        var low = root.theme.mirror.min_target_interval_s * intervalScale()
        var high = root.theme.mirror.max_target_interval_s * intervalScale()
        if (high <= low + 0.35) {
            high = low + 0.35
        }
        return Math.max(2200, Math.round(randomBetween(low, high) * 1000.0))
    }

    function outerDurationMs() {
        var base = reducedMotion() ? 196000 : 106000
        return Math.max(36000, Math.round(base / clamp(speedScalar, 0.62, 1.85)))
    }

    function innerDurationMs() {
        var base = reducedMotion() ? 248000 : 132000
        return Math.max(42000, Math.round(base / clamp(speedScalar, 0.62, 1.85)))
    }

    function seamDurationMs() {
        var base = reducedMotion() ? 310000 : 172000
        return Math.max(58000, Math.round(base / clamp(speedScalar, 0.62, 1.85)))
    }

    function syncSemanticInput() {
        var payload = root.bridge.mirrorSemanticInput
        semanticPressure = levelFromInput(payload, "pressure_level", semanticPressure)
        semanticUncertainty = levelFromInput(payload, "uncertainty_level", semanticUncertainty)
        semanticConflict = levelFromInput(payload, "conflict_level", semanticConflict)
        semanticRecovery = levelFromInput(payload, "recovery_level", semanticRecovery)
        semanticWarning = levelFromInput(payload, "warning_level", semanticWarning)
        recomputeSemanticCarrier()
    }

    function recomputeSemanticCarrier() {
        var sScale = semanticScale()
        var p = clamp(semanticPressure * sScale, 0.0, 1.0)
        var u = clamp(semanticUncertainty * sScale, 0.0, 1.0)
        var c = clamp(semanticConflict * sScale, 0.0, 1.0)
        var r = semanticRecovery
        var w = semanticWarning

        structuralAsymmetry = clamp(
            c * root.theme.mirror_semantics.symmetry_conflict_influence
            - r * root.theme.mirror_semantics.symmetry_recovery_restore,
            0.0,
            0.34
        )

        densityLevel = clamp(
            p * root.theme.mirror_semantics.density_pressure_scale
            + c * root.theme.mirror_semantics.density_conflict_scale
            - r * 0.22,
            0.0,
            1.0
        )

        echoLevel = clamp(
            u * root.theme.mirror_semantics.echo_uncertainty_scale
            - r * root.theme.mirror_semantics.echo_recovery_damp,
            0.0,
            1.0
        )

        var offsetMagnitude = clamp(
            c * root.theme.mirror_semantics.center_offset_conflict_scale
            + p * root.theme.mirror_semantics.center_offset_pressure_scale
            - r * root.theme.mirror_semantics.center_offset_recovery_damp * 10.0,
            0.0,
            14.0
        )
        centerOffsetX = driftAxisX * offsetMagnitude
        centerOffsetY = driftAxisY * offsetMagnitude

        orbitalActivity = clamp(
            (p * 0.62 + c * 0.5 + (1.0 - u) * 0.16) * root.theme.mirror_semantics.orbital_activity_scale - r * 0.24,
            0.0,
            0.9
        )
        orbitalNodeCount = Math.max(0, Math.min(4, Math.round(orbitalActivity * 4.0)))

        speedScalar = clamp(
            1.0
                + p * root.theme.mirror_semantics.motion_pressure_speedup
                + c * root.theme.mirror_semantics.motion_conflict_irregularity * 0.5
                - r * root.theme.mirror_semantics.motion_recovery_calm
                + u * 0.08,
            0.6,
            1.78
        )

        driftIrregularity = clamp(
            c * root.theme.mirror_semantics.motion_conflict_irregularity
                + u * root.theme.mirror_semantics.motion_uncertainty_drift
                - r * 0.1,
            0.0,
            0.42
        )

        detailOpacity = clamp(0.38 + densityLevel * 0.52, 0.38, 0.9)
        ghostOpacity = clamp(echoLevel * (reducedMotion() ? 0.2 : 0.42), 0.0, reducedMotion() ? 0.2 : 0.42)
        coreScaleX = 1.0 + structuralAsymmetry * 0.06
        coreScaleY = 1.0 - structuralAsymmetry * 0.05

        var severity = clamp(p * 0.56 + c * 0.56 + u * 0.33 - r * 0.28 + w * 0.72, 0.0, 1.0)
        warningActive = (severity >= root.theme.mirror_semantics.warning_gate && (p + c) > 1.18 && r < 0.32) || w > 0.88

        if (warningActive) {
            semanticBand = 3
            secondaryLineColor = root.theme.colors.accent_warning
            accentLineColor = root.theme.colors.accent_warning
        } else if (severity >= root.theme.mirror_semantics.caution_gate) {
            semanticBand = 2
            secondaryLineColor = root.theme.colors.accent_caution
            accentLineColor = root.theme.colors.accent_caution
        } else if (severity >= root.theme.mirror_semantics.advisory_gate) {
            semanticBand = 1
            secondaryLineColor = root.theme.colors.accent_advisory
            accentLineColor = root.theme.colors.accent_advisory
        } else {
            semanticBand = 0
            secondaryLineColor = root.theme.colors.text_secondary
            accentLineColor = root.theme.colors.geometry_white
        }

        mainLineColor = root.theme.colors.geometry_white
    }

    function retargetAnomaly() {
        var anomalyScale = reducedMotion() ? 0.34 : 1.0
        var phaseAmp = clamp(semanticUncertainty * 16.0 + semanticConflict * 22.0 + semanticWarning * 14.0, 0.0, 28.0) * anomalyScale
        var pulseAmp = clamp(semanticConflict * 0.58 + semanticWarning * 0.62 + semanticUncertainty * 0.22, 0.0, 0.92) * anomalyScale

        targetPhaseSkew = randomBetween(-phaseAmp, phaseAmp)
        targetAnomalyPulse = randomBetween(0.0, pulseAmp)
        driftAxisX = clamp(randomBetween(-0.86, 0.86), -0.86, 0.86)
        driftAxisY = clamp(randomBetween(-0.74, 0.74), -0.74, 0.74)

        phaseSkewAnim.stop()
        phaseSkewAnim.from = phaseSkew
        phaseSkewAnim.to = targetPhaseSkew
        phaseSkewAnim.duration = Math.max(1200, Math.round(root.motionDuration("shear_drift_ms") * 2.7))
        phaseSkewAnim.start()

        anomalyPulseAnim.stop()
        anomalyPulseAnim.from = anomalyPulse
        anomalyPulseAnim.to = targetAnomalyPulse
        anomalyPulseAnim.duration = Math.max(900, Math.round(root.motionDuration("ghost_echo_ms") * 1.8))
        anomalyPulseAnim.start()

        if (runtimeActive) {
            outerSpin.stop()
            outerSpin.duration = outerDurationMs()
            outerSpin.start()
            innerSpin.stop()
            innerSpin.duration = innerDurationMs()
            innerSpin.start()
            if (orbitalActivity > 0.08) {
                seamSpin.stop()
                seamSpin.duration = seamDurationMs()
                seamSpin.start()
            }
        }
    }

    function startRuntimeEngines() {
        if (!runtimeActive) {
            return
        }
        driftTimer.interval = nextDriftIntervalMs()
        driftTimer.restart()

        outerSpin.stop()
        outerSpin.duration = outerDurationMs()
        outerSpin.start()
        innerSpin.stop()
        innerSpin.duration = innerDurationMs()
        innerSpin.start()
        if (orbitalActivity > 0.08) {
            seamSpin.stop()
            seamSpin.duration = seamDurationMs()
            seamSpin.start()
        } else {
            seamSpin.stop()
        }
        retargetAnomaly()
    }

    function stopRuntimeEngines() {
        driftTimer.stop()
        outerSpin.stop()
        innerSpin.stop()
        seamSpin.stop()
        phaseSkewAnim.stop()
        anomalyPulseAnim.stop()
    }

    Behavior on opacity {
        NumberAnimation { duration: root.motionDuration("fade_ms"); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
    }
    Behavior on y {
        NumberAnimation { duration: root.motionDuration("phase_shift_ms"); easing.type: root.easingForClass(root.theme.motion.easing_slow_settle) }
    }
    Behavior on secondaryLineColor {
        ColorAnimation { duration: root.motionDuration("fade_ms"); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
    }
    Behavior on accentLineColor {
        ColorAnimation { duration: root.motionDuration("fade_ms"); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
    }
    Behavior on centerOffsetX {
        NumberAnimation { duration: root.motionDuration("shear_drift_ms"); easing.type: root.easingForClass(root.theme.motion.easing_slow_settle) }
    }
    Behavior on centerOffsetY {
        NumberAnimation { duration: root.motionDuration("shear_drift_ms"); easing.type: root.easingForClass(root.theme.motion.easing_slow_settle) }
    }
    Behavior on ghostOpacity {
        NumberAnimation { duration: root.motionDuration("ghost_echo_ms"); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
    }

    Text {
        id: title
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.leftMargin: root.theme.spacing.lg
        anchors.topMargin: root.theme.spacing.lg
        text: "Mirror"
        color: root.theme.colors.text_primary
        font.family: root.theme.typography.section_title.families[0]
        font.pixelSize: root.theme.typography.section_title.size
        font.weight: root.fontWeight("section_title")
    }

    Rectangle {
        id: mirrorField
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: title.bottom
        anchors.bottom: parent.bottom
        anchors.margins: root.theme.spacing.lg
        color: root.theme.colors.input_background
        border.width: root.theme.lines.thin
        border.color: root.theme.colors.divider_subtle
        clip: true

        Item {
            id: sigilRoot
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height) * 0.84
            height: width
            x: root.centerOffsetPxX
            y: root.centerOffsetPxY

            Item {
                id: hexBoundaryLayer
                anchors.fill: parent
                rotation: root.outerRotation * 0.08
                opacity: 0.94

                Repeater {
                    model: 6
                    delegate: Item {
                        required property int index
                        anchors.fill: parent
                        rotation: index * 60
                        Rectangle {
                            width: parent.width * 0.5
                            height: root.lineWidth
                            color: root.mainLineColor
                            x: (parent.width - width) / 2
                            y: parent.height * 0.08
                        }
                        Rectangle {
                            width: parent.width * 0.072
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            x: parent.width * 0.695
                            y: parent.height * 0.158
                            rotation: 31
                            transformOrigin: Item.Left
                            opacity: 0.76
                        }
                    }
                }

                Repeater {
                    model: 12
                    delegate: Item {
                        required property int index
                        anchors.fill: parent
                        rotation: index * 30
                        Rectangle {
                            width: parent.width * 0.16
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            x: (parent.width - width) / 2
                            y: parent.height * 0.23
                            opacity: 0.58 + root.detailOpacity * 0.18
                        }
                    }
                }
            }

            Item {
                id: seamLayer
                anchors.fill: parent
                rotation: root.seamRotation * 0.24
                opacity: 0.4 + root.detailOpacity * 0.24

                Repeater {
                    model: root.sectorCount
                    delegate: Item {
                        required property int index
                        anchors.fill: parent
                        rotation: index * (360 / root.sectorCount)
                        Rectangle {
                            width: parent.width * 0.18
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            x: parent.width * 0.61
                            y: parent.height * 0.5 - root.lineWidth / 2
                            opacity: 0.54
                        }
                        Rectangle {
                            width: parent.width * 0.056
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            x: parent.width * 0.57
                            y: parent.height * 0.5 - root.lineWidth / 2
                            rotation: 27
                            transformOrigin: Item.Left
                            opacity: 0.46
                        }
                    }
                }
            }

            Item {
                id: sectorWebOuter
                anchors.fill: parent
                rotation: root.outerRotation
                opacity: 0.74 + root.detailOpacity * 0.22

                Repeater {
                    model: root.sectorCount
                    delegate: Item {
                        id: outerSector
                        required property int index
                        property bool mirrored: (index % 2) === 1
                        anchors.fill: parent
                        rotation: index * (360 / root.sectorCount)
                                  + (mirrored ? -root.phaseSkew : root.phaseSkew) * 0.72
                                  + root.anomalyPulse * (mirrored ? -1.0 : 1.0) * 0.44
                        transform: Scale {
                            origin.x: outerSector.width / 2
                            origin.y: outerSector.height / 2
                            xScale: outerSector.mirrored ? -1 : 1
                            yScale: 1
                        }

                        Rectangle {
                            x: parent.width * 0.55
                            y: parent.height * 0.5 - root.lineWidth / 2
                            width: parent.width * 0.22
                            height: root.lineWidth
                            color: root.mainLineColor
                            opacity: 0.9
                        }
                        Rectangle {
                            x: parent.width * 0.57
                            y: parent.height * 0.5 - root.lineWidth / 2
                            width: parent.width * 0.18
                            height: root.lineWidth
                            rotation: 23
                            transformOrigin: Item.Left
                            color: root.secondaryLineColor
                            opacity: 0.86
                        }
                        Rectangle {
                            x: parent.width * 0.57
                            y: parent.height * 0.5 - root.lineWidth / 2
                            width: parent.width * 0.18
                            height: root.lineWidth
                            rotation: -23
                            transformOrigin: Item.Left
                            color: root.secondaryLineColor
                            opacity: 0.84
                        }
                        Rectangle {
                            x: parent.width * 0.62
                            y: parent.height * 0.466
                            width: parent.width * 0.084
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            opacity: 0.8
                        }
                        Rectangle {
                            x: parent.width * 0.62
                            y: parent.height * 0.534
                            width: parent.width * 0.084
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            opacity: 0.8
                        }
                        Rectangle {
                            x: parent.width * 0.664
                            y: parent.height * 0.474
                            width: root.lineWidth
                            height: parent.height * 0.052
                            color: root.secondaryLineColor
                            opacity: 0.74
                        }
                        Rectangle {
                            x: parent.width * 0.7
                            y: parent.height * 0.5 - root.lineWidth / 2
                            width: parent.width * 0.104
                            height: root.lineWidth
                            color: root.accentLineColor
                            opacity: 0.72 + root.detailOpacity * 0.16
                        }
                        Rectangle {
                            visible: root.densityLevel > 0.3
                            x: parent.width * 0.674
                            y: parent.height * 0.448
                            width: parent.width * 0.068
                            height: root.lineWidth
                            rotation: -32
                            transformOrigin: Item.Left
                            color: root.secondaryLineColor
                            opacity: 0.62
                        }
                        Rectangle {
                            visible: root.densityLevel > 0.3
                            x: parent.width * 0.674
                            y: parent.height * 0.552
                            width: parent.width * 0.068
                            height: root.lineWidth
                            rotation: 32
                            transformOrigin: Item.Left
                            color: root.secondaryLineColor
                            opacity: 0.62
                        }
                    }
                }
            }

            Item {
                id: sectorWebInner
                anchors.fill: parent
                rotation: root.innerRotation
                opacity: 0.56 + root.detailOpacity * 0.3

                Repeater {
                    model: root.sectorCount
                    delegate: Item {
                        id: innerSector
                        required property int index
                        property bool mirrored: (index % 2) === 1
                        anchors.fill: parent
                        rotation: index * (360 / root.sectorCount)
                                  + (mirrored ? root.phaseSkew : -root.phaseSkew) * 0.56
                                  + root.anomalyPulse * (mirrored ? 1.0 : -1.0) * 0.28
                        transform: Scale {
                            origin.x: innerSector.width / 2
                            origin.y: innerSector.height / 2
                            xScale: innerSector.mirrored ? -1 : 1
                            yScale: 1
                        }

                        Rectangle {
                            x: parent.width * 0.53
                            y: parent.height * 0.5 - root.lineWidth / 2
                            width: parent.width * 0.118
                            height: root.lineWidth
                            color: root.accentLineColor
                            opacity: 0.86
                        }
                        Rectangle {
                            x: parent.width * 0.556
                            y: parent.height * 0.5 - root.lineWidth / 2
                            width: parent.width * 0.104
                            height: root.lineWidth
                            rotation: 28
                            transformOrigin: Item.Left
                            color: root.secondaryLineColor
                            opacity: 0.8
                        }
                        Rectangle {
                            x: parent.width * 0.556
                            y: parent.height * 0.5 - root.lineWidth / 2
                            width: parent.width * 0.104
                            height: root.lineWidth
                            rotation: -28
                            transformOrigin: Item.Left
                            color: root.secondaryLineColor
                            opacity: 0.78
                        }
                        Rectangle {
                            x: parent.width * 0.595
                            y: parent.height * 0.468
                            width: parent.width * 0.06
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            opacity: 0.74
                        }
                        Rectangle {
                            x: parent.width * 0.595
                            y: parent.height * 0.532
                            width: parent.width * 0.06
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            opacity: 0.74
                        }
                        Rectangle {
                            visible: root.densityLevel > 0.46
                            x: parent.width * 0.608
                            y: parent.height * 0.478
                            width: root.lineWidth
                            height: parent.height * 0.045
                            color: root.secondaryLineColor
                            opacity: 0.66
                        }
                    }
                }
            }

            Item {
                id: coreApertureLayer
                anchors.fill: parent
                rotation: root.outerRotation * 0.05
                transform: Scale {
                    origin.x: coreApertureLayer.width / 2
                    origin.y: coreApertureLayer.height / 2
                    xScale: root.coreScaleX
                    yScale: root.coreScaleY
                }

                Repeater {
                    model: 6
                    delegate: Item {
                        required property int index
                        anchors.fill: parent
                        rotation: index * 60 + root.phaseSkew * 0.16
                        Rectangle {
                            width: parent.width * 0.17
                            height: root.lineWidth
                            color: root.mainLineColor
                            x: (parent.width - width) / 2
                            y: parent.height * 0.352
                            opacity: 0.92
                        }
                    }
                }

                Repeater {
                    model: 6
                    delegate: Item {
                        required property int index
                        anchors.fill: parent
                        rotation: index * 60 - root.phaseSkew * 0.14
                        Rectangle {
                            width: parent.width * 0.098
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            x: (parent.width - width) / 2
                            y: parent.height * 0.412
                            opacity: 0.74
                        }
                        Rectangle {
                            width: root.lineWidth
                            height: parent.height * 0.045
                            color: root.secondaryLineColor
                            x: parent.width * 0.5 - width / 2
                            y: parent.height * 0.385
                            opacity: 0.7
                        }
                    }
                }

                Rectangle {
                    width: parent.width * 0.18
                    height: width
                    radius: width / 2
                    color: mirrorField.color
                    border.width: root.lineWidth
                    border.color: root.secondaryLineColor
                    opacity: 0.92
                    anchors.centerIn: parent
                }
            }

            Item {
                id: ghostLayer
                anchors.fill: parent
                visible: root.ghostOpacity > 0.01
                opacity: root.ghostOpacity
                rotation: root.outerRotation * -0.22 + root.phaseSkew * 0.22
                scale: 1.005 + root.anomalyPulse * 0.02

                Repeater {
                    model: root.sectorCount
                    delegate: Item {
                        required property int index
                        anchors.fill: parent
                        rotation: index * (360 / root.sectorCount) + (index % 2 ? -1 : 1) * root.phaseSkew * 0.22
                        Rectangle {
                            width: parent.width * 0.13
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            x: parent.width * 0.61
                            y: parent.height * 0.5 - root.lineWidth / 2
                            opacity: 0.68
                        }
                        Rectangle {
                            width: parent.width * 0.07
                            height: root.lineWidth
                            color: root.secondaryLineColor
                            x: parent.width * 0.58
                            y: parent.height * 0.5 - root.lineWidth / 2
                            rotation: 29
                            transformOrigin: Item.Left
                            opacity: 0.56
                        }
                    }
                }
            }

            Item {
                id: orbitalLayer
                anchors.fill: parent
                visible: root.orbitalActivity > 0.08
                opacity: 0.24 + root.orbitalActivity * 0.52
                rotation: root.seamRotation

                Rectangle {
                    visible: root.orbitalNodeCount >= 1
                    width: 4
                    height: 4
                    radius: 2
                    color: root.semanticBand >= 2 ? root.accentLineColor : root.secondaryLineColor
                    x: parent.width * 0.5 + parent.width * 0.39
                    y: parent.height * 0.5 - height / 2
                }
                Rectangle {
                    visible: root.orbitalNodeCount >= 2
                    width: 4
                    height: 4
                    radius: 2
                    color: root.semanticBand >= 2 ? root.accentLineColor : root.secondaryLineColor
                    x: parent.width * 0.5 - parent.width * 0.39
                    y: parent.height * 0.5 - height / 2
                }
                Rectangle {
                    visible: root.orbitalNodeCount >= 3
                    width: 4
                    height: 4
                    radius: 2
                    color: root.semanticBand >= 2 ? root.accentLineColor : root.secondaryLineColor
                    x: parent.width * 0.5 - width / 2
                    y: parent.height * 0.5 - parent.height * 0.39
                }
                Rectangle {
                    visible: root.orbitalNodeCount >= 4
                    width: 4
                    height: 4
                    radius: 2
                    color: root.semanticBand >= 2 ? root.accentLineColor : root.secondaryLineColor
                    x: parent.width * 0.5 - width / 2
                    y: parent.height * 0.5 + parent.height * 0.39
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: root.theme.spacing.sm
            text: "semantic mirror v1 / 2d kaleidoscopic hex-web"
            color: root.theme.colors.text_secondary
            font.family: root.theme.typography.secondary_text.families[0]
            font.pixelSize: root.theme.typography.secondary_text.size
            font.weight: root.fontWeight("secondary_text")
        }
    }

    Timer {
        id: driftTimer
        interval: 10000
        repeat: true
        running: false
        onTriggered: {
            root.retargetAnomaly()
            interval = root.nextDriftIntervalMs()
        }
    }

    NumberAnimation {
        id: outerSpin
        target: root
        property: "outerRotation"
        from: 0
        to: 360
        duration: 106000
        loops: Animation.Infinite
        easing.type: Easing.Linear
    }

    NumberAnimation {
        id: innerSpin
        target: root
        property: "innerRotation"
        from: 0
        to: -360
        duration: 132000
        loops: Animation.Infinite
        easing.type: Easing.Linear
    }

    NumberAnimation {
        id: seamSpin
        target: root
        property: "seamRotation"
        from: 0
        to: 360
        duration: 172000
        loops: Animation.Infinite
        easing.type: Easing.Linear
    }

    NumberAnimation {
        id: phaseSkewAnim
        target: root
        property: "phaseSkew"
        duration: 1500
        easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
    }

    NumberAnimation {
        id: anomalyPulseAnim
        target: root
        property: "anomalyPulse"
        duration: 1300
        easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
    }

    Connections {
        target: root.bridge
        function onMirrorSemanticInputChanged() {
            root.syncSemanticInput()
            if (root.runtimeActive) {
                root.retargetAnomaly()
            }
        }
    }

    Component.onCompleted: {
        syncSemanticInput()
        if (runtimeActive) {
            startRuntimeEngines()
        }
    }

    onRuntimeActiveChanged: {
        if (runtimeActive) {
            startRuntimeEngines()
        } else {
            stopRuntimeEngines()
        }
    }

    onOrbitalActivityChanged: {
        if (!runtimeActive) {
            return
        }
        if (orbitalActivity > 0.08) {
            seamSpin.stop()
            seamSpin.duration = seamDurationMs()
            seamSpin.start()
        } else {
            seamSpin.stop()
        }
    }
}
