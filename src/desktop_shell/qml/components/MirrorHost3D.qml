pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Shapes

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
    property real lineWidth: Math.max(1.4, root.theme.lines.thin * 1.8)
    property real outerRotation: 0.0
    property real innerRotation: 0.0
    property real apertureRotation: 0.0
    property real phaseSkew: 0.0
    property real anomalyPulse: 0.0
    property real coreScaleX: 1.0
    property real coreScaleY: 1.0
    property real ghostOpacity: 0.0
    property real detailOpacity: 0.58
    property real centerOffsetPxX: centerOffsetX * (reducedMotion() ? 0.36 : 0.72)
    property real centerOffsetPxY: centerOffsetY * (reducedMotion() ? 0.36 : 0.72)
    property real driftAxisX: 0.42
    property real driftAxisY: -0.2
    property real breathingPhase: 0.0
    property double lastMotionTickMs: 0.0

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
        var semanticCompression = clamp(1.14 - (speedScalar - 1.0) * 0.24, 0.84, 1.16)
        return Math.max(2200, Math.round(randomBetween(low, high) * 1000.0 * semanticCompression))
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

        detailOpacity = clamp(0.44 + densityLevel * 0.42, 0.44, 0.88)
        ghostOpacity = clamp(echoLevel * (reducedMotion() ? 0.12 : 0.28), 0.0, reducedMotion() ? 0.12 : 0.28)
        coreScaleX = 1.0 + structuralAsymmetry * 0.045 + semanticConflict * 0.02
        coreScaleY = 1.0 - structuralAsymmetry * 0.04 + semanticRecovery * 0.015

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
        var phaseAmp = clamp(semanticUncertainty * 8.0 + semanticConflict * 12.0 + semanticWarning * 7.0, 0.0, 16.0) * anomalyScale
        var pulseAmp = clamp(semanticConflict * 0.42 + semanticWarning * 0.36 + semanticUncertainty * 0.22, 0.0, 0.74) * anomalyScale

        phaseSkew = randomBetween(-phaseAmp, phaseAmp)
        anomalyPulse = randomBetween(0.04, pulseAmp)
        driftAxisX = clamp(randomBetween(-0.86, 0.86), -0.86, 0.86)
        driftAxisY = clamp(randomBetween(-0.74, 0.74), -0.74, 0.74)
        recomputeSemanticCarrier()
    }

    function advanceMotion(nowMs) {
        if (lastMotionTickMs <= 0) {
            lastMotionTickMs = nowMs
            return
        }

        var dt = clamp((nowMs - lastMotionTickMs) / 1000.0, 0.0, 0.08)
        lastMotionTickMs = nowMs

        var motionGate = reducedMotion() ? 0.58 : 1.0
        var semanticVelocity = clamp(0.9 + (speedScalar - 1.0) * 0.3, 0.72, 1.18)
        var outerDegPerSecond = 360.0 / (reducedMotion() ? 196.0 : 132.0)
        var innerDegPerSecond = 360.0 / (reducedMotion() ? 248.0 : 168.0)
        var apertureDegPerSecond = 360.0 / (reducedMotion() ? 308.0 : 224.0)
        var driftGain = 1.0 + driftIrregularity * 0.18

        outerRotation = (outerRotation + dt * outerDegPerSecond * semanticVelocity * driftGain * motionGate) % 360.0
        innerRotation = (innerRotation - dt * innerDegPerSecond * (0.96 + densityLevel * 0.12) * motionGate) % 360.0
        apertureRotation = (apertureRotation + dt * apertureDegPerSecond * (0.94 + semanticUncertainty * 0.08) * motionGate) % 360.0
        breathingPhase = (breathingPhase + dt * (reducedMotion() ? 0.24 : 0.42) * (0.84 + semanticConflict * 0.18)) % (Math.PI * 2.0)
    }

    function startRuntimeEngines() {
        if (!runtimeActive) {
            return
        }
        lastMotionTickMs = Date.now()
        motionTimer.start()
        driftTimer.interval = nextDriftIntervalMs()
        driftTimer.restart()
        retargetAnomaly()
    }

    function stopRuntimeEngines() {
        motionTimer.stop()
        driftTimer.stop()
        lastMotionTickMs = 0.0
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
    Behavior on phaseSkew {
        NumberAnimation { duration: Math.max(1200, Math.round(root.motionDuration("shear_drift_ms") * 2.5)); easing.type: root.easingForClass(root.theme.motion.easing_slow_settle) }
    }
    Behavior on anomalyPulse {
        NumberAnimation { duration: Math.max(1100, Math.round(root.motionDuration("ghost_echo_ms") * 1.7)); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
    }
    Behavior on coreScaleX {
        NumberAnimation { duration: root.motionDuration("shear_drift_ms"); easing.type: root.easingForClass(root.theme.motion.easing_slow_settle) }
    }
    Behavior on coreScaleY {
        NumberAnimation { duration: root.motionDuration("shear_drift_ms"); easing.type: root.easingForClass(root.theme.motion.easing_slow_settle) }
    }
    Behavior on detailOpacity {
        NumberAnimation { duration: root.motionDuration("fade_ms"); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
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

            property real cx: width * 0.5
            property real cy: height * 0.5
            property real radius: width * 0.5
            property real outerRadius: radius * 0.92
            property real innerFrameRadius: radius * 0.74
            property real glyphRadius: radius * 0.80
            property real apertureBreath: 1.0 + (root.reducedMotion() ? 0.005 : 0.014)
                                               * (0.35 + root.semanticPressure * 0.38 + root.anomalyPulse * 0.46)
                                               * Math.sin(root.breathingPhase)
            property real echoShiftX: root.ghostOpacity * radius * (0.03 + root.anomalyPulse * 0.02) * root.driftAxisX
            property real echoShiftY: root.ghostOpacity * radius * (0.03 + root.anomalyPulse * 0.02) * root.driftAxisY

            function pointAt(radiusNorm, degrees) {
                var rad = degrees * Math.PI / 180.0
                var r = radius * radiusNorm
                return {
                    x: cx + Math.cos(rad) * r,
                    y: cy + Math.sin(rad) * r
                }
            }

            Component {
                id: masterSectorComponent

                Item {
                    id: sectorMaster
                    anchors.fill: parent
                    property real strokeMain: root.lineWidth
                    property real strokeMinor: root.lineWidth * 0.9
                    property real strokeDense: root.lineWidth * 0.78

                    function pointAt(radiusNorm, degrees) {
                        var rad = degrees * Math.PI / 180.0
                        var r = Math.min(width, height) * 0.5 * radiusNorm
                        return {
                            x: width * 0.5 + Math.cos(rad) * r,
                            y: height * 0.5 + Math.sin(rad) * r
                        }
                    }

                    property var nA: pointAt(0.17, 0)
                    property var nB: pointAt(0.28, 0)
                    property var nC: pointAt(0.42, 0)
                    property var nD: pointAt(0.60, 0)
                    property var nE: pointAt(0.31, -13.5)
                    property var nF: pointAt(0.46, -17.0)
                    property var nG: pointAt(0.31, 13.5)
                    property var nH: pointAt(0.46, 17.0)
                    property var nI: pointAt(0.66, -18.0)
                    property var nJ: pointAt(0.66, 18.0)
                    property var nK: pointAt(0.52, -6.6)
                    property var nL: pointAt(0.52, 6.6)
                    property var nM: pointAt(0.23, -10.0)
                    property var nN: pointAt(0.23, 10.0)
                    property var nO: pointAt(0.55, 0)

                    Shape {
                        anchors.fill: parent
                        antialiasing: true
                        opacity: 0.84 + root.detailOpacity * 0.16

                        ShapePath {
                            strokeWidth: sectorMaster.strokeMain
                            strokeColor: root.mainLineColor
                            fillColor: "transparent"
                            capStyle: ShapePath.FlatCap
                            joinStyle: ShapePath.MiterJoin
                            startX: sectorMaster.nA.x
                            startY: sectorMaster.nA.y
                            PathLine { x: sectorMaster.nB.x; y: sectorMaster.nB.y }
                            PathLine { x: sectorMaster.nC.x; y: sectorMaster.nC.y }
                            PathLine { x: sectorMaster.nD.x; y: sectorMaster.nD.y }
                        }

                        ShapePath {
                            strokeWidth: sectorMaster.strokeMinor
                            strokeColor: root.secondaryLineColor
                            fillColor: "transparent"
                            capStyle: ShapePath.FlatCap
                            joinStyle: ShapePath.MiterJoin
                            startX: sectorMaster.nB.x
                            startY: sectorMaster.nB.y
                            PathLine { x: sectorMaster.nE.x; y: sectorMaster.nE.y }
                            PathLine { x: sectorMaster.nF.x; y: sectorMaster.nF.y }
                            PathLine { x: sectorMaster.nI.x; y: sectorMaster.nI.y }
                            PathLine { x: sectorMaster.nD.x; y: sectorMaster.nD.y }
                        }

                        ShapePath {
                            strokeWidth: sectorMaster.strokeMinor
                            strokeColor: root.secondaryLineColor
                            fillColor: "transparent"
                            capStyle: ShapePath.FlatCap
                            joinStyle: ShapePath.MiterJoin
                            startX: sectorMaster.nB.x
                            startY: sectorMaster.nB.y
                            PathLine { x: sectorMaster.nG.x; y: sectorMaster.nG.y }
                            PathLine { x: sectorMaster.nH.x; y: sectorMaster.nH.y }
                            PathLine { x: sectorMaster.nJ.x; y: sectorMaster.nJ.y }
                            PathLine { x: sectorMaster.nD.x; y: sectorMaster.nD.y }
                        }

                        ShapePath {
                            strokeWidth: sectorMaster.strokeMinor
                            strokeColor: root.secondaryLineColor
                            fillColor: "transparent"
                            capStyle: ShapePath.FlatCap
                            joinStyle: ShapePath.MiterJoin
                            startX: sectorMaster.nE.x
                            startY: sectorMaster.nE.y
                            PathLine { x: sectorMaster.nC.x; y: sectorMaster.nC.y }
                            PathLine { x: sectorMaster.nG.x; y: sectorMaster.nG.y }
                        }

                        ShapePath {
                            strokeWidth: sectorMaster.strokeMinor
                            strokeColor: root.accentLineColor
                            fillColor: "transparent"
                            capStyle: ShapePath.FlatCap
                            joinStyle: ShapePath.MiterJoin
                            startX: sectorMaster.nF.x
                            startY: sectorMaster.nF.y
                            PathLine { x: sectorMaster.nK.x; y: sectorMaster.nK.y }
                            PathLine { x: sectorMaster.nO.x; y: sectorMaster.nO.y }
                            PathLine { x: sectorMaster.nL.x; y: sectorMaster.nL.y }
                            PathLine { x: sectorMaster.nH.x; y: sectorMaster.nH.y }
                        }
                    }

                    Shape {
                        anchors.fill: parent
                        antialiasing: true
                        visible: root.densityLevel > 0.18
                        opacity: (0.16 + root.densityLevel * 0.42) * (root.reducedMotion() ? 0.92 : 1.0)

                        ShapePath {
                            strokeWidth: sectorMaster.strokeDense
                            strokeColor: root.secondaryLineColor
                            fillColor: "transparent"
                            capStyle: ShapePath.FlatCap
                            joinStyle: ShapePath.MiterJoin
                            startX: sectorMaster.nM.x
                            startY: sectorMaster.nM.y
                            PathLine { x: sectorMaster.nE.x; y: sectorMaster.nE.y }
                            PathLine { x: sectorMaster.nC.x; y: sectorMaster.nC.y }
                            PathLine { x: sectorMaster.nG.x; y: sectorMaster.nG.y }
                            PathLine { x: sectorMaster.nN.x; y: sectorMaster.nN.y }
                        }

                        ShapePath {
                            strokeWidth: sectorMaster.strokeDense
                            strokeColor: root.secondaryLineColor
                            fillColor: "transparent"
                            capStyle: ShapePath.FlatCap
                            joinStyle: ShapePath.MiterJoin
                            startX: sectorMaster.nK.x
                            startY: sectorMaster.nK.y
                            PathLine { x: sectorMaster.nD.x; y: sectorMaster.nD.y }
                            PathLine { x: sectorMaster.nL.x; y: sectorMaster.nL.y }
                        }
                    }
                }
            }

            Item {
                id: outerFrameLayer
                anchors.fill: parent
                rotation: root.outerRotation * 0.11 + root.phaseSkew * 0.12
                opacity: 0.96

                Shape {
                    anchors.fill: parent
                    antialiasing: true
                    opacity: 0.92

                    ShapePath {
                        strokeWidth: root.lineWidth
                        strokeColor: root.mainLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.pointAt(0.92, -11.25).x
                        startY: sigilRoot.pointAt(0.92, -11.25).y
                        PathLine { x: sigilRoot.pointAt(0.86, 0.0).x; y: sigilRoot.pointAt(0.86, 0.0).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 11.25).x; y: sigilRoot.pointAt(0.92, 11.25).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 22.5).x; y: sigilRoot.pointAt(0.86, 22.5).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 33.75).x; y: sigilRoot.pointAt(0.92, 33.75).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 45.0).x; y: sigilRoot.pointAt(0.86, 45.0).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 56.25).x; y: sigilRoot.pointAt(0.92, 56.25).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 67.5).x; y: sigilRoot.pointAt(0.86, 67.5).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 78.75).x; y: sigilRoot.pointAt(0.92, 78.75).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 90.0).x; y: sigilRoot.pointAt(0.86, 90.0).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 101.25).x; y: sigilRoot.pointAt(0.92, 101.25).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 112.5).x; y: sigilRoot.pointAt(0.86, 112.5).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 123.75).x; y: sigilRoot.pointAt(0.92, 123.75).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 135.0).x; y: sigilRoot.pointAt(0.86, 135.0).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 146.25).x; y: sigilRoot.pointAt(0.92, 146.25).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 157.5).x; y: sigilRoot.pointAt(0.86, 157.5).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 168.75).x; y: sigilRoot.pointAt(0.92, 168.75).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 180.0).x; y: sigilRoot.pointAt(0.86, 180.0).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 191.25).x; y: sigilRoot.pointAt(0.92, 191.25).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 202.5).x; y: sigilRoot.pointAt(0.86, 202.5).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 213.75).x; y: sigilRoot.pointAt(0.92, 213.75).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 225.0).x; y: sigilRoot.pointAt(0.86, 225.0).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 236.25).x; y: sigilRoot.pointAt(0.92, 236.25).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 247.5).x; y: sigilRoot.pointAt(0.86, 247.5).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 258.75).x; y: sigilRoot.pointAt(0.92, 258.75).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 270.0).x; y: sigilRoot.pointAt(0.86, 270.0).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 281.25).x; y: sigilRoot.pointAt(0.92, 281.25).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 292.5).x; y: sigilRoot.pointAt(0.86, 292.5).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 303.75).x; y: sigilRoot.pointAt(0.92, 303.75).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 315.0).x; y: sigilRoot.pointAt(0.86, 315.0).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 326.25).x; y: sigilRoot.pointAt(0.92, 326.25).y }
                        PathLine { x: sigilRoot.pointAt(0.86, 337.5).x; y: sigilRoot.pointAt(0.86, 337.5).y }
                        PathLine { x: sigilRoot.pointAt(0.92, 348.75).x; y: sigilRoot.pointAt(0.92, 348.75).y }
                        PathLine { x: sigilRoot.pointAt(0.92, -11.25).x; y: sigilRoot.pointAt(0.92, -11.25).y }
                    }

                    ShapePath {
                        strokeWidth: root.lineWidth * 0.92
                        strokeColor: root.secondaryLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.pointAt(0.74, -10.0).x
                        startY: sigilRoot.pointAt(0.74, -10.0).y
                        PathLine { x: sigilRoot.pointAt(0.68, 0.0).x; y: sigilRoot.pointAt(0.68, 0.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 10.0).x; y: sigilRoot.pointAt(0.74, 10.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 22.5).x; y: sigilRoot.pointAt(0.68, 22.5).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 35.0).x; y: sigilRoot.pointAt(0.74, 35.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 45.0).x; y: sigilRoot.pointAt(0.68, 45.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 55.0).x; y: sigilRoot.pointAt(0.74, 55.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 67.5).x; y: sigilRoot.pointAt(0.68, 67.5).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 80.0).x; y: sigilRoot.pointAt(0.74, 80.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 90.0).x; y: sigilRoot.pointAt(0.68, 90.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 100.0).x; y: sigilRoot.pointAt(0.74, 100.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 112.5).x; y: sigilRoot.pointAt(0.68, 112.5).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 125.0).x; y: sigilRoot.pointAt(0.74, 125.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 135.0).x; y: sigilRoot.pointAt(0.68, 135.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 145.0).x; y: sigilRoot.pointAt(0.74, 145.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 157.5).x; y: sigilRoot.pointAt(0.68, 157.5).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 170.0).x; y: sigilRoot.pointAt(0.74, 170.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 180.0).x; y: sigilRoot.pointAt(0.68, 180.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 190.0).x; y: sigilRoot.pointAt(0.74, 190.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 202.5).x; y: sigilRoot.pointAt(0.68, 202.5).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 215.0).x; y: sigilRoot.pointAt(0.74, 215.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 225.0).x; y: sigilRoot.pointAt(0.68, 225.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 235.0).x; y: sigilRoot.pointAt(0.74, 235.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 247.5).x; y: sigilRoot.pointAt(0.68, 247.5).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 260.0).x; y: sigilRoot.pointAt(0.74, 260.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 270.0).x; y: sigilRoot.pointAt(0.68, 270.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 280.0).x; y: sigilRoot.pointAt(0.74, 280.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 292.5).x; y: sigilRoot.pointAt(0.68, 292.5).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 305.0).x; y: sigilRoot.pointAt(0.74, 305.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 315.0).x; y: sigilRoot.pointAt(0.68, 315.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 325.0).x; y: sigilRoot.pointAt(0.74, 325.0).y }
                        PathLine { x: sigilRoot.pointAt(0.68, 337.5).x; y: sigilRoot.pointAt(0.68, 337.5).y }
                        PathLine { x: sigilRoot.pointAt(0.74, 350.0).x; y: sigilRoot.pointAt(0.74, 350.0).y }
                        PathLine { x: sigilRoot.pointAt(0.74, -10.0).x; y: sigilRoot.pointAt(0.74, -10.0).y }
                    }
                }

                Repeater {
                    model: root.sectorCount
                    delegate: Item {
                        required property int index
                        anchors.fill: parent
                        rotation: index * (360 / root.sectorCount)

                        Shape {
                            anchors.fill: parent
                            antialiasing: true
                            opacity: 0.32 + root.orbitalActivity * 0.18 + (root.semanticBand >= 2 ? 0.05 : 0.0)

                            ShapePath {
                                strokeWidth: root.lineWidth * 0.76
                                strokeColor: root.accentLineColor
                                fillColor: "transparent"
                                capStyle: ShapePath.FlatCap
                                joinStyle: ShapePath.MiterJoin
                                startX: sigilRoot.pointAt(0.76, -4.0).x
                                startY: sigilRoot.pointAt(0.76, -4.0).y
                                PathLine { x: sigilRoot.pointAt(0.82, -4.0).x; y: sigilRoot.pointAt(0.82, -4.0).y }
                                PathLine { x: sigilRoot.pointAt(0.84, 0.0).x; y: sigilRoot.pointAt(0.84, 0.0).y }
                                PathLine { x: sigilRoot.pointAt(0.82, 4.0).x; y: sigilRoot.pointAt(0.82, 4.0).y }
                            }
                        }
                    }
                }
            }

            Item {
                id: sectorGlyphLayer
                anchors.fill: parent
                rotation: root.outerRotation
                opacity: 0.78 + root.detailOpacity * 0.18

                Repeater {
                    model: root.sectorCount
                    delegate: Item {
                        id: sectorGlyphHost
                        required property int index
                        property bool mirrored: (index % 2) === 1
                        anchors.fill: parent
                        rotation: index * (360 / root.sectorCount)
                                  + (mirrored ? -root.phaseSkew : root.phaseSkew) * 0.58
                                  + root.anomalyPulse * (mirrored ? -1.0 : 1.0) * 1.9
                        transform: Scale {
                            origin.x: sectorGlyphHost.width / 2
                            origin.y: sectorGlyphHost.height / 2
                            xScale: 1.0 + root.structuralAsymmetry * 0.018
                            yScale: sectorGlyphHost.mirrored ? -1.0 : 1.0
                        }

                        Loader {
                            anchors.fill: parent
                            sourceComponent: masterSectorComponent
                        }
                    }
                }
            }

            Item {
                id: apertureLayer
                anchors.fill: parent
                rotation: root.innerRotation * 0.16 + root.apertureRotation * 0.26
                transform: [
                    Translate {
                        x: root.phaseSkew * 0.06 + root.anomalyPulse * sigilRoot.radius * 0.01 * root.driftAxisX
                        y: -root.phaseSkew * 0.025 + root.anomalyPulse * sigilRoot.radius * 0.01 * root.driftAxisY
                    },
                    Scale {
                        origin.x: apertureLayer.width / 2
                        origin.y: apertureLayer.height / 2
                        xScale: root.coreScaleX
                        yScale: root.coreScaleY * sigilRoot.apertureBreath
                    }
                ]

                Shape {
                    anchors.fill: parent
                    antialiasing: true
                    opacity: 0.94

                    ShapePath {
                        strokeWidth: root.lineWidth
                        strokeColor: root.mainLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.cx
                        startY: sigilRoot.cy - sigilRoot.radius * 0.165
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.09; y: sigilRoot.cy - sigilRoot.radius * 0.112 }
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.114; y: sigilRoot.cy - sigilRoot.radius * 0.04 }
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.114; y: sigilRoot.cy + sigilRoot.radius * 0.04 }
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.09; y: sigilRoot.cy + sigilRoot.radius * 0.112 }
                        PathLine { x: sigilRoot.cx; y: sigilRoot.cy + sigilRoot.radius * 0.165 }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.09; y: sigilRoot.cy + sigilRoot.radius * 0.112 }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.114; y: sigilRoot.cy + sigilRoot.radius * 0.04 }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.114; y: sigilRoot.cy - sigilRoot.radius * 0.04 }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.09; y: sigilRoot.cy - sigilRoot.radius * 0.112 }
                        PathLine { x: sigilRoot.cx; y: sigilRoot.cy - sigilRoot.radius * 0.165 }
                    }

                    ShapePath {
                        strokeWidth: root.lineWidth * 0.92
                        strokeColor: root.secondaryLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.cx
                        startY: sigilRoot.cy - sigilRoot.radius * 0.105
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.038; y: sigilRoot.cy - sigilRoot.radius * 0.073 }
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.048; y: sigilRoot.cy - sigilRoot.radius * 0.018 }
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.048; y: sigilRoot.cy + sigilRoot.radius * 0.018 }
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.038; y: sigilRoot.cy + sigilRoot.radius * 0.073 }
                        PathLine { x: sigilRoot.cx; y: sigilRoot.cy + sigilRoot.radius * 0.105 }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.038; y: sigilRoot.cy + sigilRoot.radius * 0.073 }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.048; y: sigilRoot.cy + sigilRoot.radius * 0.018 }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.048; y: sigilRoot.cy - sigilRoot.radius * 0.018 }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.038; y: sigilRoot.cy - sigilRoot.radius * 0.073 }
                        PathLine { x: sigilRoot.cx; y: sigilRoot.cy - sigilRoot.radius * 0.105 }
                    }

                    ShapePath {
                        strokeWidth: root.lineWidth * 0.88
                        strokeColor: root.accentLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.cx - sigilRoot.radius * 0.136
                        startY: sigilRoot.cy
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.09; y: sigilRoot.cy }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.066; y: sigilRoot.cy - sigilRoot.radius * 0.026 }
                    }

                    ShapePath {
                        strokeWidth: root.lineWidth * 0.88
                        strokeColor: root.accentLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.cx - sigilRoot.radius * 0.136
                        startY: sigilRoot.cy
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.09; y: sigilRoot.cy }
                        PathLine { x: sigilRoot.cx - sigilRoot.radius * 0.066; y: sigilRoot.cy + sigilRoot.radius * 0.026 }
                    }

                    ShapePath {
                        strokeWidth: root.lineWidth * 0.88
                        strokeColor: root.accentLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.cx + sigilRoot.radius * 0.136
                        startY: sigilRoot.cy
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.09; y: sigilRoot.cy }
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.066; y: sigilRoot.cy - sigilRoot.radius * 0.026 }
                    }

                    ShapePath {
                        strokeWidth: root.lineWidth * 0.88
                        strokeColor: root.accentLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.cx + sigilRoot.radius * 0.136
                        startY: sigilRoot.cy
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.09; y: sigilRoot.cy }
                        PathLine { x: sigilRoot.cx + sigilRoot.radius * 0.066; y: sigilRoot.cy + sigilRoot.radius * 0.026 }
                    }

                    ShapePath {
                        strokeWidth: root.lineWidth * 0.86
                        strokeColor: root.secondaryLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.cx
                        startY: sigilRoot.cy - sigilRoot.radius * 0.22
                        PathLine { x: sigilRoot.cx; y: sigilRoot.cy - sigilRoot.radius * 0.165 }
                    }

                    ShapePath {
                        strokeWidth: root.lineWidth * 0.86
                        strokeColor: root.secondaryLineColor
                        fillColor: "transparent"
                        capStyle: ShapePath.FlatCap
                        joinStyle: ShapePath.MiterJoin
                        startX: sigilRoot.cx
                        startY: sigilRoot.cy + sigilRoot.radius * 0.165
                        PathLine { x: sigilRoot.cx; y: sigilRoot.cy + sigilRoot.radius * 0.22 }
                    }
                }
            }

            Item {
                id: optionalEchoLayer
                anchors.fill: parent
                visible: root.ghostOpacity > 0.01
                opacity: root.ghostOpacity
                x: sigilRoot.echoShiftX
                y: sigilRoot.echoShiftY
                rotation: root.innerRotation * -0.14 + root.phaseSkew * 0.35
                scale: 1.002 + root.anomalyPulse * 0.012

                Repeater {
                    model: root.sectorCount
                    delegate: Item {
                        id: echoSectorHost
                        required property int index
                        property bool mirrored: (index % 2) === 1
                        anchors.fill: parent
                        rotation: index * (360 / root.sectorCount)
                                  + (mirrored ? root.phaseSkew : -root.phaseSkew) * 0.4
                        transform: Scale {
                            origin.x: echoSectorHost.width / 2
                            origin.y: echoSectorHost.height / 2
                            yScale: echoSectorHost.mirrored ? -1.0 : 1.0
                        }

                        Loader {
                            anchors.fill: parent
                            sourceComponent: masterSectorComponent
                        }
                    }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: root.theme.spacing.sm
            text: "octagonal mirror lattice / aperture-aligned monolith"
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

    Timer {
        id: motionTimer
        interval: root.reducedMotion() ? 33 : 16
        repeat: true
        running: false
        onTriggered: root.advanceMotion(Date.now())
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
}
