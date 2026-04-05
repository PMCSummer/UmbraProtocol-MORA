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
    property real phaseSkewTarget: 0.0
    property real anomalyPulseTarget: 0.0
    property real driftAxisTargetX: 0.42
    property real driftAxisTargetY: -0.2
    property real phaseSkew: phaseSkewTarget
    property real anomalyPulse: anomalyPulseTarget
    property real coreScaleX: 1.0
    property real coreScaleY: 1.0
    property real ghostOpacity: 0.0
    property real detailOpacity: 0.58
    property real offsetMagnitude: 0.0
    property real centerOffsetX: driftAxisX * offsetMagnitude
    property real centerOffsetY: driftAxisY * offsetMagnitude
    property real centerOffsetPxX: centerOffsetX * (reducedMotion() ? 0.36 : 0.72)
    property real centerOffsetPxY: centerOffsetY * (reducedMotion() ? 0.36 : 0.72)
    property real driftAxisX: driftAxisTargetX
    property real driftAxisY: driftAxisTargetY
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
        var reflectionCompression = reducedMotion() ? 0.84 : 0.58
        return Math.max(2200, Math.round(randomBetween(low, high) * 1000.0 * semanticCompression * reflectionCompression))
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

        offsetMagnitude = clamp(
            c * root.theme.mirror_semantics.center_offset_conflict_scale
            + p * root.theme.mirror_semantics.center_offset_pressure_scale
            - r * root.theme.mirror_semantics.center_offset_recovery_damp * 10.0,
            0.0,
            14.0
        )

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
        var anomalyScale = reducedMotion() ? 0.30 : 1.0
        var phaseAmp = clamp(semanticUncertainty * 8.0 + semanticConflict * 11.0 + semanticWarning * 6.5, 0.0, 13.0) * anomalyScale
        var pulseAmp = clamp(semanticConflict * 0.56 + semanticWarning * 0.42 + semanticUncertainty * 0.34, 0.12, 0.88) * anomalyScale
        var phaseTarget = randomBetween(-phaseAmp, phaseAmp)
        var pulseTarget = randomBetween(0.08 * anomalyScale, Math.max(0.08 * anomalyScale, pulseAmp))
        var axisTargetX = clamp(randomBetween(-0.86, 0.86), -0.86, 0.86)
        var axisTargetY = clamp(randomBetween(-0.74, 0.74), -0.74, 0.74)

        phaseSkewTarget = phaseSkew * 0.76 + phaseTarget * 0.24
        anomalyPulseTarget = anomalyPulse * 0.72 + pulseTarget * 0.28
        var nextAxisX = driftAxisX * 0.84 + axisTargetX * 0.16
        var nextAxisY = driftAxisY * 0.84 + axisTargetY * 0.16
        var axisLen = Math.sqrt(nextAxisX * nextAxisX + nextAxisY * nextAxisY)
        if (axisLen < 0.12) {
            nextAxisX = 0.42
            nextAxisY = -0.20
            axisLen = Math.sqrt(nextAxisX * nextAxisX + nextAxisY * nextAxisY)
        }
        driftAxisTargetX = clamp(nextAxisX / axisLen, -0.86, 0.86)
        driftAxisTargetY = clamp(nextAxisY / axisLen, -0.74, 0.74)
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
        var outerDegPerSecond = 360.0 / (reducedMotion() ? 176.0 : 92.0)
        var innerDegPerSecond = 360.0 / (reducedMotion() ? 222.0 : 124.0)
        var apertureDegPerSecond = 360.0 / (reducedMotion() ? 268.0 : 156.0)
        var driftGain = 1.0 + driftIrregularity * 0.34

        outerRotation = (outerRotation + dt * outerDegPerSecond * semanticVelocity * driftGain * motionGate) % 360.0
        innerRotation = (innerRotation + dt * innerDegPerSecond * (0.98 + densityLevel * 0.16) * motionGate) % 360.0
        apertureRotation = (apertureRotation + dt * apertureDegPerSecond * (0.98 + semanticUncertainty * 0.12 + orbitalActivity * 0.10) * motionGate) % 360.0
        breathingPhase = (breathingPhase + dt * (reducedMotion() ? 0.28 : 0.64) * (0.86 + semanticConflict * 0.24)) % (Math.PI * 2.0)
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
        SmoothedAnimation {
            velocity: root.reducedMotion() ? 6 : 14
            reversingMode: SmoothedAnimation.Eased
            maximumEasingTime: Math.max(240, Math.round(root.motionDuration("shear_drift_ms") * 0.72))
        }
    }
    Behavior on centerOffsetY {
        SmoothedAnimation {
            velocity: root.reducedMotion() ? 6 : 14
            reversingMode: SmoothedAnimation.Eased
            maximumEasingTime: Math.max(240, Math.round(root.motionDuration("shear_drift_ms") * 0.72))
        }
    }
    Behavior on driftAxisX {
        SmoothedAnimation {
            velocity: root.reducedMotion() ? 0.55 : 1.05
            reversingMode: SmoothedAnimation.Eased
            maximumEasingTime: Math.max(520, Math.round(root.motionDuration("shear_drift_ms") * 1.12))
        }
    }
    Behavior on driftAxisY {
        SmoothedAnimation {
            velocity: root.reducedMotion() ? 0.55 : 1.05
            reversingMode: SmoothedAnimation.Eased
            maximumEasingTime: Math.max(520, Math.round(root.motionDuration("shear_drift_ms") * 1.12))
        }
    }
    Behavior on ghostOpacity {
        NumberAnimation { duration: root.motionDuration("ghost_echo_ms"); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
    }
    Behavior on phaseSkew {
        SmoothedAnimation {
            velocity: root.reducedMotion() ? 2.2 : 4.6
            reversingMode: SmoothedAnimation.Eased
            maximumEasingTime: Math.max(900, Math.round(root.motionDuration("shear_drift_ms") * 1.9))
        }
    }
    Behavior on anomalyPulse {
        SmoothedAnimation {
            velocity: root.reducedMotion() ? 0.18 : 0.34
            reversingMode: SmoothedAnimation.Eased
            maximumEasingTime: Math.max(760, Math.round(root.motionDuration("ghost_echo_ms") * 1.34))
        }
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
            width: Math.min(parent.width, parent.height) * 0.92
            height: width
            x: root.centerOffsetPxX
            y: root.centerOffsetPxY

            property real cx: width * 0.5
            property real cy: height * 0.5
            property real radius: width * 0.5
            property int frontSeamCount: 6
            property int deepSeamCount: 8
            property real frontStep: 360 / frontSeamCount
            property real deepStep: 360 / deepSeamCount
            property real seamStroke: root.lineWidth * 1.54
            property real frameStroke: root.lineWidth * 1.20
            property real supportStroke: root.lineWidth * 0.96
            property real webStroke: root.lineWidth * 0.74
            property real phantomStroke: root.lineWidth * 0.60
            property real blindCoreRadius: radius * (0.118 + root.semanticConflict * 0.014 + root.anomalyPulse * 0.010)
            property real seamFlux: Math.sin(root.breathingPhase * 1.42 + root.apertureRotation * 0.031) * (1.0 + root.driftIrregularity * 0.74)
            property real reflectionShear: root.phaseSkew * 0.15 + seamFlux * (0.86 + root.anomalyPulse * 2.1)
            property int activeFrontDefectIndex: Math.floor((((root.outerRotation * 0.84 + root.apertureRotation * 0.62) % 360.0) + 360.0) / frontStep) % frontSeamCount
            property int activeDeepDefectIndex: Math.floor((((180.0 + root.innerRotation * 0.62 + root.apertureRotation * 0.48) % 360.0) + 360.0) / deepStep) % deepSeamCount
            property real frontPhase: root.outerRotation * 0.034 + root.apertureRotation * 0.014 + root.phaseSkew * 0.34 + seamFlux * 1.8
            property real deepPhase: 13 + root.innerRotation * 0.040 + root.apertureRotation * 0.014 - root.phaseSkew * 0.16 + seamFlux * 0.8
            property real frontSourcePhase: root.outerRotation * 1.20 + root.innerRotation * 0.24 + root.apertureRotation * 0.24 + root.phaseSkew * 0.42
            property real deepSourcePhase: 7 + root.innerRotation * 1.08 + root.outerRotation * 0.22 + root.apertureRotation * 0.18 - root.phaseSkew * 0.20
            property real webPhase: root.outerRotation * 0.10 + root.innerRotation * 0.18 + root.apertureRotation * 0.22
            property real localWarp: Math.sin(root.breathingPhase * 1.16) * 0.050 + seamFlux * 0.022 + root.anomalyPulse * 0.098
            property real echoShiftX: root.ghostOpacity * radius * (0.030 + root.anomalyPulse * 0.020) * root.driftAxisX
            property real echoShiftY: root.ghostOpacity * radius * (0.030 + root.anomalyPulse * 0.020) * root.driftAxisY
            property real frontScale: 1.04 + root.structuralAsymmetry * 0.018 + root.densityLevel * 0.010
            property real deepScale: 0.92 + root.densityLevel * 0.044 + root.echoLevel * 0.016
            property real centerFractureBias: root.phaseSkew * 0.22 + reflectionShear * 0.22 + root.anomalyPulse * radius * 0.008

            function pointAt(radiusNorm, degrees) {
                var rad = degrees * Math.PI / 180.0
                var r = radius * radiusNorm
                return {
                    x: cx + Math.cos(rad) * r,
                    y: cy + Math.sin(rad) * r
                }
            }

            function frontBias(index) {
                if (index === activeFrontDefectIndex) {
                    return 1.8 + root.structuralAsymmetry * 8.2 + root.anomalyPulse * 7.2
                }
                if (index === 4) {
                    return -1.2 - root.structuralAsymmetry * 4.6
                }
                if (index === 5) {
                    return 0.7 + root.semanticConflict * 2.8
                }
                return ((index % 2) === 0 ? 1 : -1) * (root.phaseSkew * 0.035 + seamFlux * 0.16)
            }

            function deepBias(index) {
                if (index === 2) {
                    return 2.4 + root.echoLevel * 8.0
                }
                if (index === activeDeepDefectIndex) {
                    return -1.7 - root.anomalyPulse * 7.0
                }
                if (index === 0) {
                    return 0.9 + root.phaseSkew * 0.16
                }
                return ((index % 2) === 0 ? 0.55 : -0.55) * (root.phaseSkew * 0.12 + seamFlux * 0.22)
            }

            function frontAngle(index) {
                return frontPhase + index * frontStep + frontBias(index)
            }

            function deepAngle(index) {
                return deepPhase + index * deepStep + deepBias(index)
            }

            function frontSpread(index) {
                if (index === activeFrontDefectIndex) {
                    return 20.4 + root.structuralAsymmetry * 5.0 + Math.abs(seamFlux) * 1.4 + root.anomalyPulse * 2.6
                }
                if (index === 4) {
                    return 24.8
                }
                return 24.0 + (index === 2 ? 1.5 : 0.0) + Math.abs(seamFlux) * 0.55
            }

            function deepSpread(index) {
                if (index === activeDeepDefectIndex) {
                    return 14.0 + root.echoLevel * 4.4 + Math.abs(seamFlux) * 0.8 + root.anomalyPulse * 2.2
                }
                if (index === 2) {
                    return 16.6 + root.anomalyPulse * 2.2
                }
                return 15.0 + Math.abs(seamFlux) * 0.45
            }

            function seamLength(index) {
                if (index === activeFrontDefectIndex) {
                    return 0.86
                }
                return index === 4 ? 0.91 : 0.94
            }

            function requestAllPaints() {
                seamCanvas.requestPaint()
                frontMirrorCanvas.requestPaint()
                deepMirrorCanvas.requestPaint()
                webCanvas.requestPaint()
                coreCanvas.requestPaint()
                phantomCanvas.requestPaint()
            }

            Canvas {
                id: seamCanvas
                anchors.fill: parent
                antialiasing: true
                opacity: 0.98
                renderStrategy: Canvas.Cooperative

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.setTransform(1, 0, 0, 1, 0, 0)
                    ctx.clearRect(0, 0, width, height)
                    ctx.lineCap = "butt"
                    ctx.lineJoin = "miter"

                    function drawRadial(angleDeg, r0, r1, lineWidth, color, alpha) {
                        var p0 = sigilRoot.pointAt(r0, angleDeg)
                        var p1 = sigilRoot.pointAt(r1, angleDeg)
                        ctx.globalAlpha = alpha
                        ctx.strokeStyle = color
                        ctx.lineWidth = lineWidth
                        ctx.beginPath()
                        ctx.moveTo(p0.x, p0.y)
                        ctx.lineTo(p1.x, p1.y)
                        ctx.stroke()
                    }

                    function drawArcSegment(rNorm, a0, a1, lineWidth, color, alpha) {
                        var rr = sigilRoot.radius * rNorm
                        ctx.globalAlpha = alpha
                        ctx.strokeStyle = color
                        ctx.lineWidth = lineWidth
                        ctx.beginPath()
                        ctx.arc(sigilRoot.cx, sigilRoot.cy, rr, a0 * Math.PI / 180.0, a1 * Math.PI / 180.0, false)
                        ctx.stroke()
                    }

                    for (var i = 0; i < sigilRoot.frontSeamCount; ++i) {
                        var axis = sigilRoot.frontAngle(i)
                        var alpha = i === sigilRoot.activeFrontDefectIndex ? 0.56 : 0.88
                        drawRadial(axis, 0.18, sigilRoot.seamLength(i), sigilRoot.seamStroke, root.mainLineColor, alpha)
                        if (i === sigilRoot.activeFrontDefectIndex) {
                            drawRadial(axis + 1.8, 0.30, 0.78, sigilRoot.supportStroke, root.secondaryLineColor, 0.28)
                        }
                    }

                    for (var j = 0; j < sigilRoot.frontSeamCount; ++j) {
                        var left = sigilRoot.frontAngle(j) + sigilRoot.frontSpread(j) * 0.72
                        var right = sigilRoot.frontAngle((j + 1) % sigilRoot.frontSeamCount) - sigilRoot.frontSpread((j + 1) % sigilRoot.frontSeamCount) * 0.72
                        if (j === sigilRoot.activeFrontDefectIndex) {
                            right -= 5.0
                        }
                        drawArcSegment(0.92, left, right, sigilRoot.frameStroke, root.mainLineColor, 0.88)
                    }

                    for (var k = 0; k < sigilRoot.deepSeamCount; ++k) {
                        var deepAxis = sigilRoot.deepAngle(k)
                        drawRadial(deepAxis, 0.23, 0.74, sigilRoot.supportStroke, root.secondaryLineColor, k === sigilRoot.activeDeepDefectIndex ? 0.26 : 0.34)
                    }

                    drawArcSegment(0.28, sigilRoot.frontAngle(0) - 18, sigilRoot.frontAngle(2) + 11, sigilRoot.supportStroke, root.secondaryLineColor, 0.30)
                    drawArcSegment(0.28, sigilRoot.frontAngle(3) - 12, sigilRoot.frontAngle(5) + 8, sigilRoot.supportStroke, root.secondaryLineColor, 0.24)
                }
            }

            Canvas {
                id: frontMirrorCanvas
                anchors.fill: parent
                antialiasing: true
                opacity: 0.96
                scale: sigilRoot.frontScale
                rotation: root.outerRotation * 0.018
                renderStrategy: Canvas.Cooperative

                function mirrorClip(ctx, innerNorm, outerNorm, spreadDeg) {
                    var rr0 = sigilRoot.radius * innerNorm
                    var rr1 = sigilRoot.radius * outerNorm
                    var s = spreadDeg * Math.PI / 180.0
                    ctx.beginPath()
                    ctx.moveTo(rr0 * Math.cos(-s), rr0 * Math.sin(-s))
                    ctx.lineTo(rr1 * Math.cos(-s), rr1 * Math.sin(-s))
                    ctx.arc(0, 0, rr1, -s, s, false)
                    ctx.lineTo(rr0 * Math.cos(s), rr0 * Math.sin(s))
                    ctx.arc(0, 0, rr0, s, -s, true)
                    ctx.closePath()
                    ctx.clip()
                }

                function strokeChain(ctx, points, color, lineWidth, alpha) {
                    ctx.globalAlpha = alpha
                    ctx.strokeStyle = color
                    ctx.lineWidth = lineWidth
                    ctx.beginPath()
                    ctx.moveTo(points[0][0], points[0][1])
                    for (var p = 1; p < points.length; ++p) {
                        ctx.lineTo(points[p][0], points[p][1])
                    }
                    ctx.stroke()
                }

                function drawBundle(ctx, index, layerPhase) {
                    var rr = sigilRoot.radius
                    var t = layerPhase * Math.PI / 180.0
                    var w1 = Math.sin(t + index * 0.68) * rr * (0.030 + sigilRoot.localWarp * 0.18)
                    var w2 = Math.sin(t * 0.9 + index * 1.14 + 0.6) * rr * (0.038 + sigilRoot.localWarp * 0.16)
                    var w3 = Math.sin(t * 1.2 + index * 0.49 + 1.4) * rr * (0.026 + root.anomalyPulse * 0.20)
                    var w4 = Math.sin(t * 0.62 + index * 0.77 + 2.2) * rr * (0.020 + root.structuralAsymmetry * 0.10 + root.anomalyPulse * 0.06)

                    strokeChain(ctx, [
                        [rr * 0.18, -rr * 0.012],
                        [rr * 0.32, -rr * 0.11 - w1],
                        [rr * 0.50, -rr * 0.19 - w2],
                        [rr * 0.72, -rr * 0.12 - w3],
                        [rr * 0.93, -rr * 0.05 - w4]
                    ], root.mainLineColor, sigilRoot.frameStroke, 0.96)

                    strokeChain(ctx, [
                        [rr * 0.33, -rr * 0.12 - w1 * 0.2],
                        [rr * 0.45, -rr * 0.26 - w2 * 0.4],
                        [rr * 0.61, -rr * 0.33 - w3 * 0.3],
                        [rr * 0.82, -rr * 0.28 - w4 * 0.5]
                    ], root.secondaryLineColor, sigilRoot.supportStroke, 0.82)

                    strokeChain(ctx, [
                        [rr * 0.23, -rr * 0.018],
                        [rr * 0.28, -rr * 0.17 - w2 * 0.35],
                        [rr * 0.34, -rr * 0.27 - w3 * 0.28]
                    ], root.secondaryLineColor, sigilRoot.webStroke, 0.72)

                    strokeChain(ctx, [
                        [rr * 0.58, -rr * 0.19 - w1 * 0.22],
                        [rr * 0.68, -rr * 0.08 - w2 * 0.2],
                        [rr * 0.86, -rr * 0.028 - w3 * 0.18]
                    ], root.accentLineColor, sigilRoot.webStroke, 0.62)
                }

                function drawMirroredWedge(ctx, index, axisDeg, spreadDeg) {
                    ctx.save()
                    ctx.translate(sigilRoot.cx, sigilRoot.cy)
                    ctx.rotate(axisDeg * Math.PI / 180.0)
                    mirrorClip(ctx, 0.16, 1.02, spreadDeg + 1.6)

                    drawBundle(ctx, index, sigilRoot.frontSourcePhase + index * 11.0)

                    ctx.save()
                    if (index === sigilRoot.activeFrontDefectIndex) {
                        ctx.translate(sigilRoot.radius * 0.010, -sigilRoot.radius * 0.003)
                        ctx.rotate((1.6 + root.structuralAsymmetry * 2.2) * Math.PI / 180.0)
                    }
                    ctx.scale(1, -1)
                    drawBundle(ctx, index, sigilRoot.frontSourcePhase + index * 11.0 + 14.0)
                    ctx.restore()

                    if (!root.reducedMotion()) {
                        ctx.save()
                        var frontEchoKick = sigilRoot.radius * (0.004 + root.anomalyPulse * 0.016 + root.echoLevel * 0.008)
                        ctx.translate(frontEchoKick, -frontEchoKick * 0.64)
                        ctx.rotate((sigilRoot.reflectionShear * 0.9 + index * 0.24) * Math.PI / 180.0)
                        ctx.scale(-1, -1)
                        drawBundle(ctx, index, sigilRoot.frontSourcePhase + index * 11.0 + 22.0)
                        ctx.restore()
                    }

                    if (index === sigilRoot.activeFrontDefectIndex) {
                        ctx.globalAlpha = 0.18 + root.anomalyPulse * 0.10
                        ctx.strokeStyle = root.accentLineColor
                        ctx.lineWidth = sigilRoot.phantomStroke
                        ctx.beginPath()
                        ctx.moveTo(sigilRoot.radius * 0.30, -sigilRoot.radius * 0.008)
                        ctx.lineTo(sigilRoot.radius * 0.44, sigilRoot.radius * 0.018)
                        ctx.lineTo(sigilRoot.radius * 0.58, sigilRoot.radius * 0.010)
                        ctx.stroke()
                    }

                    ctx.restore()
                }

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.setTransform(1, 0, 0, 1, 0, 0)
                    ctx.clearRect(0, 0, width, height)
                    ctx.lineCap = "butt"
                    ctx.lineJoin = "miter"

                    for (var i = 0; i < sigilRoot.frontSeamCount; ++i) {
                        drawMirroredWedge(ctx, i, sigilRoot.frontAngle(i), sigilRoot.frontSpread(i))
                    }
                }
            }

            Canvas {
                id: deepMirrorCanvas
                anchors.fill: parent
                antialiasing: true
                opacity: 0.58 + root.detailOpacity * 0.12
                scale: sigilRoot.deepScale
                rotation: root.innerRotation * 0.016
                renderStrategy: Canvas.Cooperative

                function mirrorClip(ctx, innerNorm, outerNorm, spreadDeg) {
                    var rr0 = sigilRoot.radius * innerNorm
                    var rr1 = sigilRoot.radius * outerNorm
                    var s = spreadDeg * Math.PI / 180.0
                    ctx.beginPath()
                    ctx.moveTo(rr0 * Math.cos(-s), rr0 * Math.sin(-s))
                    ctx.lineTo(rr1 * Math.cos(-s), rr1 * Math.sin(-s))
                    ctx.arc(0, 0, rr1, -s, s, false)
                    ctx.lineTo(rr0 * Math.cos(s), rr0 * Math.sin(s))
                    ctx.arc(0, 0, rr0, s, -s, true)
                    ctx.closePath()
                    ctx.clip()
                }

                function strokeChain(ctx, points, color, lineWidth, alpha) {
                    ctx.globalAlpha = alpha
                    ctx.strokeStyle = color
                    ctx.lineWidth = lineWidth
                    ctx.beginPath()
                    ctx.moveTo(points[0][0], points[0][1])
                    for (var p = 1; p < points.length; ++p) {
                        ctx.lineTo(points[p][0], points[p][1])
                    }
                    ctx.stroke()
                }

                function drawBundle(ctx, index, layerPhase) {
                    var rr = sigilRoot.radius
                    var t = layerPhase * Math.PI / 180.0
                    var w1 = Math.sin(t * 0.84 + index * 0.73) * rr * (0.024 + root.echoLevel * 0.040)
                    var w2 = Math.sin(t * 1.28 + index * 0.53 + 1.1) * rr * (0.032 + sigilRoot.localWarp * 0.10)
                    var w3 = Math.sin(t * 0.58 + index * 1.27 + 0.7) * rr * (0.022 + root.anomalyPulse * 0.26)

                    strokeChain(ctx, [
                        [rr * 0.24, -rr * 0.010],
                        [rr * 0.36, -rr * 0.092 - w1],
                        [rr * 0.50, -rr * 0.16 - w2],
                        [rr * 0.66, -rr * 0.12 - w3],
                        [rr * 0.80, -rr * 0.038]
                    ], root.secondaryLineColor, sigilRoot.supportStroke, 0.56)

                    strokeChain(ctx, [
                        [rr * 0.30, -rr * 0.10],
                        [rr * 0.44, -rr * 0.21 - w1 * 0.3],
                        [rr * 0.58, -rr * 0.26 - w2 * 0.36],
                        [rr * 0.70, -rr * 0.21 - w3 * 0.28]
                    ], root.accentLineColor, sigilRoot.webStroke, 0.34)
                }

                function drawMirroredWedge(ctx, index, axisDeg, spreadDeg) {
                    ctx.save()
                    ctx.translate(sigilRoot.cx, sigilRoot.cy)
                    ctx.rotate(axisDeg * Math.PI / 180.0)
                    mirrorClip(ctx, 0.22, 0.82, spreadDeg + 1.2)

                    drawBundle(ctx, index, sigilRoot.deepSourcePhase + index * 16.0)

                    ctx.save()
                    if (index === sigilRoot.activeDeepDefectIndex) {
                        ctx.translate(-sigilRoot.radius * 0.006, sigilRoot.radius * 0.005)
                        ctx.rotate((-2.1 - root.echoLevel * 3.0) * Math.PI / 180.0)
                    }
                    ctx.scale(1, -1)
                    drawBundle(ctx, index, sigilRoot.deepSourcePhase + index * 16.0 + 19.0)
                    ctx.restore()

                    if (!root.reducedMotion()) {
                        ctx.save()
                        var deepEchoKick = sigilRoot.radius * (0.003 + root.anomalyPulse * 0.014 + root.echoLevel * 0.010)
                        ctx.translate(-deepEchoKick * 0.58, deepEchoKick)
                        ctx.rotate((-sigilRoot.reflectionShear * 0.68 - index * 0.18) * Math.PI / 180.0)
                        ctx.scale(-1, -1)
                        drawBundle(ctx, index, sigilRoot.deepSourcePhase + index * 16.0 + 28.0)
                        ctx.restore()
                    }

                    ctx.restore()
                }

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.setTransform(1, 0, 0, 1, 0, 0)
                    ctx.clearRect(0, 0, width, height)
                    ctx.lineCap = "butt"
                    ctx.lineJoin = "miter"

                    for (var i = 0; i < sigilRoot.deepSeamCount; ++i) {
                        drawMirroredWedge(ctx, i, sigilRoot.deepAngle(i), sigilRoot.deepSpread(i))
                    }
                }
            }

            Canvas {
                id: webCanvas
                anchors.fill: parent
                antialiasing: true
                opacity: root.detailOpacity * 0.82
                renderStrategy: Canvas.Cooperative

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.setTransform(1, 0, 0, 1, 0, 0)
                    ctx.clearRect(0, 0, width, height)
                    ctx.lineCap = "butt"
                    ctx.lineJoin = "miter"

                    function strokePoly(points, lineWidth, color, alpha) {
                        ctx.globalAlpha = alpha
                        ctx.strokeStyle = color
                        ctx.lineWidth = lineWidth
                        ctx.beginPath()
                        ctx.moveTo(points[0].x, points[0].y)
                        for (var a = 1; a < points.length; ++a) {
                            ctx.lineTo(points[a].x, points[a].y)
                        }
                        ctx.stroke()
                    }

                    for (var i = 0; i < sigilRoot.frontSeamCount; ++i) {
                        var a0 = sigilRoot.frontAngle(i) + 6 + Math.sin(sigilRoot.webPhase * Math.PI / 180.0 + i) * 2.4
                        var a1 = sigilRoot.deepAngle((i + 1) % sigilRoot.deepSeamCount) - 5
                        var a2 = sigilRoot.frontAngle((i + 1) % sigilRoot.frontSeamCount) - 6
                        strokePoly([
                            sigilRoot.pointAt(0.34, a0),
                            sigilRoot.pointAt(0.48, a1),
                            sigilRoot.pointAt(0.62, a2)
                        ], sigilRoot.webStroke, root.secondaryLineColor, i === sigilRoot.activeFrontDefectIndex ? 0.20 : 0.34)
                    }

                    for (var j = 0; j < sigilRoot.deepSeamCount; ++j) {
                        var left = sigilRoot.pointAt(0.46, sigilRoot.deepAngle(j) + 6)
                        var mid = sigilRoot.pointAt(0.56, sigilRoot.deepAngle(j) + 11 + Math.sin(sigilRoot.webPhase * 0.9 + j * 0.4) * 3.0)
                        var right = sigilRoot.pointAt(0.64, sigilRoot.deepAngle((j + 2) % sigilRoot.deepSeamCount) - 8)
                        if (j !== sigilRoot.activeDeepDefectIndex) {
                            strokePoly([left, mid, right], sigilRoot.webStroke, root.accentLineColor, 0.16 + root.anomalyPulse * 0.08)
                        }
                    }
                }
            }

            Rectangle {
                id: blindCore
                width: sigilRoot.blindCoreRadius * 2
                height: width
                radius: width / 2
                anchors.centerIn: parent
                color: mirrorField.color
                border.width: 0
                opacity: 1.0
            }

            Canvas {
                id: coreCanvas
                anchors.fill: parent
                antialiasing: true
                opacity: 0.96
                renderStrategy: Canvas.Cooperative

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.setTransform(1, 0, 0, 1, 0, 0)
                    ctx.clearRect(0, 0, width, height)
                    ctx.lineCap = "butt"
                    ctx.lineJoin = "miter"

                    function strokePoly(points, lineWidth, color, alpha) {
                        ctx.globalAlpha = alpha
                        ctx.strokeStyle = color
                        ctx.lineWidth = lineWidth
                        ctx.beginPath()
                        ctx.moveTo(points[0].x, points[0].y)
                        for (var i = 1; i < points.length; ++i) {
                            ctx.lineTo(points[i].x, points[i].y)
                        }
                        ctx.stroke()
                    }

                    var knot = [
                        sigilRoot.pointAt(0.17, sigilRoot.frontAngle(0) - 5),
                        sigilRoot.pointAt(0.21, sigilRoot.frontAngle(1) + 3),
                        sigilRoot.pointAt(0.19, sigilRoot.frontAngle(2) + 7),
                        sigilRoot.pointAt(0.16, sigilRoot.frontAngle(3) - 4),
                        sigilRoot.pointAt(0.18, sigilRoot.frontAngle(4) + 5)
                    ]
                    strokePoly(knot, sigilRoot.frameStroke, root.mainLineColor, 0.86)

                    strokePoly([
                        { x: sigilRoot.cx - sigilRoot.radius * 0.084 + sigilRoot.centerFractureBias, y: sigilRoot.cy - sigilRoot.radius * 0.038 },
                        { x: sigilRoot.cx - sigilRoot.radius * 0.020 + sigilRoot.centerFractureBias * 0.52, y: sigilRoot.cy - sigilRoot.radius * 0.012 },
                        { x: sigilRoot.cx + sigilRoot.radius * 0.014 + sigilRoot.centerFractureBias * 0.16, y: sigilRoot.cy + sigilRoot.radius * 0.010 },
                        { x: sigilRoot.cx + sigilRoot.radius * 0.052 - sigilRoot.centerFractureBias * 0.16, y: sigilRoot.cy + sigilRoot.radius * 0.032 },
                        { x: sigilRoot.cx + sigilRoot.radius * 0.082 - sigilRoot.centerFractureBias * 0.34, y: sigilRoot.cy + sigilRoot.radius * 0.058 }
                    ], sigilRoot.supportStroke, root.secondaryLineColor, 0.72)

                    strokePoly([
                        { x: sigilRoot.cx - sigilRoot.radius * 0.108, y: sigilRoot.cy + sigilRoot.radius * 0.006 },
                        { x: sigilRoot.cx - sigilRoot.radius * 0.078, y: sigilRoot.cy + sigilRoot.radius * 0.006 },
                        { x: sigilRoot.cx - sigilRoot.radius * 0.054, y: sigilRoot.cy - sigilRoot.radius * 0.015 }
                    ], sigilRoot.webStroke, root.accentLineColor, 0.58)

                    strokePoly([
                        { x: sigilRoot.cx + sigilRoot.radius * 0.110, y: sigilRoot.cy - sigilRoot.radius * 0.010 },
                        { x: sigilRoot.cx + sigilRoot.radius * 0.076, y: sigilRoot.cy - sigilRoot.radius * 0.010 },
                        { x: sigilRoot.cx + sigilRoot.radius * 0.049, y: sigilRoot.cy + sigilRoot.radius * 0.014 }
                    ], sigilRoot.webStroke, root.accentLineColor, 0.58)
                }
            }

            Canvas {
                id: phantomCanvas
                anchors.fill: parent
                antialiasing: true
                visible: root.ghostOpacity > 0.01 || root.anomalyPulse > 0.03
                opacity: root.ghostOpacity * 0.74 + root.anomalyPulse * 0.18
                x: sigilRoot.echoShiftX
                y: sigilRoot.echoShiftY
                rotation: sigilRoot.deepPhase * 0.022 + sigilRoot.frontPhase * 0.032
                scale: 0.995 + root.anomalyPulse * 0.016
                renderStrategy: Canvas.Cooperative

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.setTransform(1, 0, 0, 1, 0, 0)
                    ctx.clearRect(0, 0, width, height)
                    ctx.lineCap = "butt"
                    ctx.lineJoin = "miter"

                    function strokePoly(points, lineWidth, color, alpha) {
                        ctx.globalAlpha = alpha
                        ctx.strokeStyle = color
                        ctx.lineWidth = lineWidth
                        ctx.beginPath()
                        ctx.moveTo(points[0].x, points[0].y)
                        for (var i = 1; i < points.length; ++i) {
                            ctx.lineTo(points[i].x, points[i].y)
                        }
                        ctx.stroke()
                    }

                    strokePoly([
                        sigilRoot.pointAt(0.30, sigilRoot.deepAngle(2) - 10),
                        sigilRoot.pointAt(0.46, sigilRoot.deepAngle(2) + 2),
                        sigilRoot.pointAt(0.67, sigilRoot.deepAngle(2) + 4)
                    ], sigilRoot.phantomStroke, root.accentLineColor, 0.24)

                    strokePoly([
                        sigilRoot.pointAt(0.46, sigilRoot.frontAngle(4) + 16),
                        sigilRoot.pointAt(0.62, sigilRoot.frontAngle(4) + 12),
                        sigilRoot.pointAt(0.74, sigilRoot.frontAngle(4) + 7)
                    ], sigilRoot.phantomStroke, root.secondaryLineColor, 0.20)
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: root.theme.spacing.sm
            text: "stratified mirror lattice / sealed blind core"
            color: root.theme.colors.text_secondary
            font.family: root.theme.typography.secondary_text.families[0]
            font.pixelSize: root.theme.typography.secondary_text.size
            font.weight: root.fontWeight("secondary_text")
        }
    }

    Timer {
        id: driftTimer
        interval: 4200
        repeat: true
        running: false
        onTriggered: {
            root.retargetAnomaly()
            interval = root.nextDriftIntervalMs()
            sigilRoot.requestAllPaints()
        }
    }

    Timer {
        id: motionTimer
        interval: root.reducedMotion() ? 33 : 16
        repeat: true
        running: false
        onTriggered: {
            root.advanceMotion(Date.now())
            sigilRoot.requestAllPaints()
        }
    }

    Connections {
        target: root.bridge
        function onMirrorSemanticInputChanged() {
            root.syncSemanticInput()
            if (root.runtimeActive) {
                root.retargetAnomaly()
            }
            sigilRoot.requestAllPaints()
        }
    }

    Component.onCompleted: {
        syncSemanticInput()
        sigilRoot.requestAllPaints()
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
