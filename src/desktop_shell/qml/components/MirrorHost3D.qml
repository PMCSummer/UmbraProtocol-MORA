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
    clip: true

    property real semanticPressure: 0.12
    property real semanticUncertainty: 0.10
    property real semanticConflict: 0.08
    property real semanticRecovery: 0.76
    property real semanticWarning: 0.0

    property real densityLevel: 0.0
    property real echoLevel: 0.0
    property real orbitalActivity: 0.0
    property real speedScalar: 1.0
    property int semanticBand: 0
    property bool warningActive: false

    property color mainLineColor: root.theme.colors.geometry_white
    property color secondaryLineColor: root.theme.colors.text_secondary
    property color accentLineColor: root.theme.colors.geometry_white

    property int sectorCount: 8
    property real lineWidth: Math.max(1.35, root.theme.lines.thin * 1.72)
    property real baseSpinSpeed: 8.5
    property real baseWedgeSpinSpeed: 2.0
    property real sourceScale: 1.08
    property int detailLevel: 8
    property real sectorPhaseOffsetDeg: -90.0

    property bool layer2Enabled: true
    property real layer2BaseScale: 0.84
    property real layer2OpacityBase: 0.42
    property real layer2SpinMultiplier: -0.8
    property real layer2WedgeMultiplier: 1.32
    property real layer2DetailMultiplier: 0.44

    property bool layer3Enabled: false

    property real outerRotation: 0.0
    property real wedgeRotation: 0.0
    property real breathingPhase: 0.0
    property double lastMotionTickMs: 0.0

    property real overallScale: 1.0
    property real layer2Scale: layer2BaseScale
    property real layer2Opacity: layer2OpacityBase
    property real detailOpacity: 0.68
    property real haloOpacity: 0.24
    property real haloRadiusScale: 0.80
    property real centerOffsetXTarget: 0.0
    property real centerOffsetYTarget: 0.0
    property real centerOffsetX: centerOffsetXTarget
    property real centerOffsetY: centerOffsetYTarget

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

    function clamp(v, lo, hi) {
        return Math.max(lo, Math.min(hi, v))
    }

    function levelFromInput(payload, key, fallback) {
        if (!payload || payload[key] === undefined || payload[key] === null) {
            return fallback
        }
        return clamp(Number(payload[key]), 0.0, 1.0)
    }

    function withAlpha(colorValue, alphaValue) {
        return Qt.rgba(colorValue.r, colorValue.g, colorValue.b, clamp(alphaValue, 0.0, 1.0))
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

        densityLevel = clamp(
            p * root.theme.mirror_semantics.density_pressure_scale * 0.66
            + c * root.theme.mirror_semantics.density_conflict_scale * 0.32
            - r * 0.14,
            0.18,
            1.0
        )

        echoLevel = clamp(
            u * root.theme.mirror_semantics.echo_uncertainty_scale * 0.28
            + c * 0.05
            - r * root.theme.mirror_semantics.echo_recovery_damp * 0.18,
            0.0,
            0.42
        )

        orbitalActivity = clamp(
            (p * 0.46 + c * 0.28 + u * 0.24) * root.theme.mirror_semantics.orbital_activity_scale * 0.72
            - r * 0.14,
            0.0,
            0.64
        )

        speedScalar = clamp(
            1.0
            + p * root.theme.mirror_semantics.motion_pressure_speedup * 0.32
            + c * root.theme.mirror_semantics.motion_conflict_irregularity * 0.16
            + u * 0.05
            - r * root.theme.mirror_semantics.motion_recovery_calm * 0.28,
            0.82,
            1.34
        )

        detailOpacity = clamp(0.58 + densityLevel * 0.18 + echoLevel * 0.04, 0.56, 0.84)
        layer2Opacity = clamp(layer2OpacityBase + echoLevel * 0.18 + c * 0.04 - r * 0.05, 0.28, 0.58)
        layer2Scale = clamp(layer2BaseScale + r * 0.016 - c * 0.014 + u * 0.004, 0.78, 0.90)
        overallScale = clamp(1.0 + r * 0.016 - c * 0.010 + p * 0.006, 0.98, 1.04)
        haloOpacity = clamp(0.16 + r * 0.10 + u * 0.04 + w * 0.08, 0.12, 0.34)
        haloRadiusScale = clamp(0.78 + r * 0.03 - c * 0.02 + u * 0.01, 0.75, 0.84)

        var driftAmplitude = clamp((c * 0.52 + u * 0.34 + p * 0.10 - r * 0.24) * (reducedMotion() ? 4.0 : 8.0), 0.0, reducedMotion() ? 2.4 : 5.4)
        var driftAngle = (p * 54 + u * 188 + c * 302 + w * 40 - r * 74) * Math.PI / 180.0
        centerOffsetXTarget = Math.cos(driftAngle) * driftAmplitude
        centerOffsetYTarget = Math.sin(driftAngle) * driftAmplitude * 0.76

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

    function advanceMotion(nowMs) {
        if (lastMotionTickMs <= 0) {
            lastMotionTickMs = nowMs
            return
        }

        var dt = clamp((nowMs - lastMotionTickMs) / 1000.0, 0.0, 0.08)
        lastMotionTickMs = nowMs

        var motionGate = reducedMotion() ? 0.58 : 1.0
        outerRotation = (outerRotation + dt * baseSpinSpeed * speedScalar * motionGate) % 360.0
        wedgeRotation = (wedgeRotation + dt * baseWedgeSpinSpeed * (0.94 + orbitalActivity * 0.14 + semanticUncertainty * 0.08) * motionGate) % 360.0
        breathingPhase = (breathingPhase + dt * (reducedMotion() ? 0.24 : 0.52) * (0.92 + semanticPressure * 0.10 + semanticRecovery * 0.12)) % (Math.PI * 2.0)
    }

    function startRuntimeEngines() {
        if (!runtimeActive) {
            return
        }
        lastMotionTickMs = Date.now()
        motionTimer.start()
    }

    function stopRuntimeEngines() {
        motionTimer.stop()
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
            velocity: root.reducedMotion() ? 3.5 : 7.0
            reversingMode: SmoothedAnimation.Eased
            maximumEasingTime: Math.max(280, Math.round(root.motionDuration("shear_drift_ms") * 0.70))
        }
    }
    Behavior on centerOffsetY {
        SmoothedAnimation {
            velocity: root.reducedMotion() ? 3.5 : 7.0
            reversingMode: SmoothedAnimation.Eased
            maximumEasingTime: Math.max(280, Math.round(root.motionDuration("shear_drift_ms") * 0.70))
        }
    }
    Behavior on layer2Opacity {
        NumberAnimation { duration: root.motionDuration("ghost_echo_ms"); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
    }
    Behavior on layer2Scale {
        NumberAnimation { duration: root.motionDuration("shear_drift_ms"); easing.type: root.easingForClass(root.theme.motion.easing_slow_settle) }
    }
    Behavior on overallScale {
        NumberAnimation { duration: root.motionDuration("shear_drift_ms"); easing.type: root.easingForClass(root.theme.motion.easing_slow_settle) }
    }
    Behavior on haloOpacity {
        NumberAnimation { duration: root.motionDuration("fade_ms"); easing.type: root.easingForClass(root.theme.motion.easing_soft_standard) }
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
            width: Math.min(parent.width, parent.height) * 0.90
            height: width
            x: root.centerOffsetX
            y: root.centerOffsetY

            property real radius: width * 0.455
            property real breath: 1.0 + Math.sin(root.breathingPhase) * (root.reducedMotion() ? 0.003 : 0.006)
            property real frontHaloRadius: radius * root.haloRadiusScale
            property real deepHaloRadius: radius * (0.12 + root.echoLevel * 0.05)

            function requestAllPaints() {
                mirrorCanvas.requestPaint()
            }

            Canvas {
                id: mirrorCanvas
                anchors.fill: parent
                antialiasing: true
                renderStrategy: Canvas.Cooperative

                function p(x, y) {
                    return { x: x, y: y }
                }

                function drawPolyline(ctx, points, closed) {
                    if (!points || points.length === 0) {
                        return
                    }
                    ctx.beginPath()
                    ctx.moveTo(points[0].x, points[0].y)
                    for (var i = 1; i < points.length; ++i) {
                        ctx.lineTo(points[i].x, points[i].y)
                    }
                    if (closed) {
                        ctx.closePath()
                    }
                    ctx.stroke()
                }

                function octagonPoints(halfExtent, cutRatio) {
                    var cut = halfExtent * root.clamp(cutRatio, 0.05, 0.45)
                    var h = halfExtent
                    return [
                        p(-h + cut, -h),
                        p(h - cut, -h),
                        p(h, -h + cut),
                        p(h, h - cut),
                        p(h - cut, h),
                        p(-h + cut, h),
                        p(-h, h - cut),
                        p(-h, -h + cut)
                    ]
                }

                function drawMarkerSquare(ctx, x, y, halfSize) {
                    ctx.strokeRect(x - halfSize, y - halfSize, halfSize * 2.0, halfSize * 2.0)
                }

                function beginWedgeClip(ctx, radiusValue, sectorAngleDeg) {
                    var halfA = sectorAngleDeg * Math.PI / 360.0
                    ctx.beginPath()
                    ctx.moveTo(0, 0)
                    ctx.arc(0, 0, radiusValue, -halfA, halfA, false)
                    ctx.closePath()
                    ctx.clip()
                }

                function drawRitualSource(ctx, radiusValue, detailMul, layerOpacity, accentStrength) {
                    var detail = Math.max(4, Math.round(root.detailLevel * detailMul))
                    var outer = radiusValue * 0.74
                    var frameGap = 0.165
                    var gateHalfWidth = 0.175
                    var gateHalfHeight = 0.465
                    var gateCorner = 0.105
                    var corridorHalfWidth = 0.100
                    var sideInnerX = 0.44
                    var sideOuterX = 0.67
                    var sideHalfHeight = 0.21
                    var sideCut = 0.075
                    var connectorDrop = 0.22
                    var markerSize = 0.028

                    var mainStroke = root.lineWidth * (1.00 + detailMul * 0.05)
                    var supportStroke = Math.max(1.0, root.lineWidth * 0.86)
                    var webStroke = Math.max(1.0, root.lineWidth * 0.68)
                    var fineStroke = Math.max(1.0, root.lineWidth * 0.56)
                    var frameCount = Math.max(3, Math.min(5, 3 + Math.floor(detail / 7)))

                    var mainColor = root.withAlpha(root.mainLineColor, layerOpacity)
                    var secondColor = root.withAlpha(root.secondaryLineColor, layerOpacity * (0.52 + accentStrength * 0.18))
                    var accentColor = root.withAlpha(root.accentLineColor, layerOpacity * (0.38 + accentStrength * 0.22))

                    ctx.lineCap = "butt"
                    ctx.lineJoin = "miter"

                    for (var i = 0; i < frameCount; ++i) {
                        var extent = outer - i * outer * frameGap
                        ctx.strokeStyle = i === 0 ? mainColor : secondColor
                        ctx.lineWidth = i === 0 ? mainStroke * 1.08 : supportStroke
                        drawPolyline(ctx, octagonPoints(extent, 0.285), true)
                    }

                    var gateW = outer * gateHalfWidth
                    var gateH = outer * gateHalfHeight
                    var gateC = outer * gateCorner
                    ctx.strokeStyle = mainColor
                    ctx.lineWidth = mainStroke * 1.04
                    drawPolyline(ctx, [
                        p(-gateW + gateC, -gateH),
                        p(gateW - gateC, -gateH),
                        p(gateW, -gateH + gateC),
                        p(gateW, gateH - gateC),
                        p(gateW - gateC, gateH),
                        p(-gateW + gateC, gateH),
                        p(-gateW, gateH - gateC),
                        p(-gateW, -gateH + gateC)
                    ], true)

                    var innerTop = -(outer - outer * frameGap * 1.18)
                    var innerBottom = -innerTop
                    var corridorW = outer * corridorHalfWidth
                    ctx.strokeStyle = mainColor
                    ctx.lineWidth = supportStroke
                    ctx.beginPath()
                    ctx.moveTo(-corridorW, innerTop)
                    ctx.lineTo(-corridorW, -gateH)
                    ctx.moveTo(corridorW, innerTop)
                    ctx.lineTo(corridorW, -gateH)
                    ctx.moveTo(-corridorW, gateH)
                    ctx.lineTo(-corridorW, innerBottom)
                    ctx.moveTo(corridorW, gateH)
                    ctx.lineTo(corridorW, innerBottom)
                    ctx.stroke()

                    var rungCount = Math.max(2, 2 + Math.floor(detail / 6))
                    ctx.strokeStyle = secondColor
                    ctx.lineWidth = fineStroke
                    for (var r = 1; r <= rungCount; ++r) {
                        var t = r / (rungCount + 1)
                        var yTop = innerTop + (-gateH - innerTop) * t
                        var yBottom = gateH + (innerBottom - gateH) * t
                        ctx.beginPath()
                        ctx.moveTo(-corridorW, yTop)
                        ctx.lineTo(corridorW, yTop)
                        ctx.moveTo(-corridorW, yBottom)
                        ctx.lineTo(corridorW, yBottom)
                        ctx.stroke()
                    }

                    var sideInner = outer * sideInnerX
                    var sideOuter = outer * sideOuterX
                    var sideH = outer * sideHalfHeight
                    var sideC = outer * sideCut
                    var sideAttachY = gateH * 0.54
                    var drop = outer * connectorDrop

                    ctx.strokeStyle = mainColor
                    ctx.lineWidth = supportStroke
                    drawPolyline(ctx, [
                        p(-sideOuter, -sideH + sideC),
                        p(-sideOuter + sideC, -sideH),
                        p(-sideInner, -sideH),
                        p(-gateW, -sideAttachY),
                        p(-gateW, sideAttachY),
                        p(-sideInner, sideH),
                        p(-sideOuter + sideC, sideH),
                        p(-sideOuter, sideH - sideC)
                    ], true)
                    drawPolyline(ctx, [
                        p(sideOuter, -sideH + sideC),
                        p(sideOuter - sideC, -sideH),
                        p(sideInner, -sideH),
                        p(gateW, -sideAttachY),
                        p(gateW, sideAttachY),
                        p(sideInner, sideH),
                        p(sideOuter - sideC, sideH),
                        p(sideOuter, sideH - sideC)
                    ], true)

                    ctx.strokeStyle = secondColor
                    ctx.lineWidth = fineStroke
                    ctx.beginPath()
                    ctx.moveTo(-sideOuter + sideC * 0.8, 0)
                    ctx.lineTo(-gateW, 0)
                    ctx.moveTo(sideOuter - sideC * 0.8, 0)
                    ctx.lineTo(gateW, 0)
                    ctx.moveTo(-sideInner, -sideH)
                    ctx.lineTo(-gateW, -drop)
                    ctx.moveTo(-sideInner, sideH)
                    ctx.lineTo(-gateW, drop)
                    ctx.moveTo(sideInner, -sideH)
                    ctx.lineTo(gateW, -drop)
                    ctx.moveTo(sideInner, sideH)
                    ctx.lineTo(gateW, drop)
                    ctx.stroke()

                    var diamondRX = outer * 0.048
                    var diamondRY = outer * 0.035
                    ctx.strokeStyle = accentColor
                    ctx.lineWidth = webStroke
                    drawPolyline(ctx, [
                        p(-sideOuter * 0.82, -diamondRY),
                        p(-sideOuter * 0.82 + diamondRX, 0),
                        p(-sideOuter * 0.82, diamondRY),
                        p(-sideOuter * 0.82 - diamondRX, 0)
                    ], true)
                    drawPolyline(ctx, [
                        p(sideOuter * 0.82, -diamondRY),
                        p(sideOuter * 0.82 + diamondRX, 0),
                        p(sideOuter * 0.82, diamondRY),
                        p(sideOuter * 0.82 - diamondRX, 0)
                    ], true)

                    var braceY = outer * 0.26
                    var braceX = outer * 0.58
                    ctx.strokeStyle = secondColor
                    ctx.lineWidth = fineStroke
                    ctx.beginPath()
                    ctx.moveTo(-braceX, -braceY)
                    ctx.lineTo(-corridorW, innerTop + outer * 0.11)
                    ctx.moveTo(braceX, -braceY)
                    ctx.lineTo(corridorW, innerTop + outer * 0.11)
                    ctx.moveTo(-braceX, braceY)
                    ctx.lineTo(-corridorW, innerBottom - outer * 0.11)
                    ctx.moveTo(braceX, braceY)
                    ctx.lineTo(corridorW, innerBottom - outer * 0.11)
                    ctx.stroke()

                    var markerHalf = Math.max(1.0, outer * markerSize)
                    var markerDist = outer * 1.11
                    ctx.strokeStyle = mainColor
                    ctx.lineWidth = webStroke
                    drawMarkerSquare(ctx, 0.0, -markerDist, markerHalf)
                    drawMarkerSquare(ctx, markerDist, 0.0, markerHalf)
                    drawMarkerSquare(ctx, 0.0, markerDist, markerHalf)
                    drawMarkerSquare(ctx, -markerDist, 0.0, markerHalf)
                    drawMarkerSquare(ctx, -markerDist * 0.76, -markerDist * 0.76, markerHalf)
                    drawMarkerSquare(ctx, markerDist * 0.76, -markerDist * 0.76, markerHalf)
                    drawMarkerSquare(ctx, markerDist * 0.76, markerDist * 0.76, markerHalf)
                    drawMarkerSquare(ctx, -markerDist * 0.76, markerDist * 0.76, markerHalf)

                    if (detail >= 6) {
                        ctx.strokeStyle = secondColor
                        ctx.lineWidth = fineStroke
                        var ribCount = 2 + Math.floor(detail * 0.22)
                        for (var rib = 0; rib < ribCount; ++rib) {
                            var ribPhase = rib / Math.max(1, ribCount - 1)
                            var ribY = -gateH + (gateH * 2.0) * ribPhase
                            ctx.beginPath()
                            ctx.moveTo(-sideInner + outer * 0.03, ribY * 0.58)
                            ctx.lineTo(-gateW + outer * 0.03, ribY * 0.42)
                            ctx.moveTo(sideInner - outer * 0.03, ribY * 0.58)
                            ctx.lineTo(gateW - outer * 0.03, ribY * 0.42)
                            ctx.stroke()
                        }
                    }
                }

                function drawOverlay(ctx, cx, cy, radiusValue) {
                    ctx.save()
                    ctx.translate(cx, cy)

                    ctx.strokeStyle = root.withAlpha(root.mainLineColor, 0.22 + root.haloOpacity * 0.35)
                    ctx.lineWidth = Math.max(1.0, root.lineWidth * 1.16)
                    drawPolyline(ctx, octagonPoints(radiusValue * 0.90, 0.28), true)

                    ctx.strokeStyle = root.withAlpha(root.secondaryLineColor, 0.18 + root.detailOpacity * 0.18)
                    ctx.lineWidth = Math.max(1.0, root.lineWidth * 0.74)
                    drawPolyline(ctx, octagonPoints(radiusValue * 0.115, 0.30), true)

                    ctx.beginPath()
                    ctx.strokeStyle = root.withAlpha(root.mainLineColor, root.haloOpacity)
                    ctx.lineWidth = Math.max(1.0, root.lineWidth * 0.56)
                    ctx.arc(0, 0, sigilRoot.frontHaloRadius, 0, Math.PI * 2.0, false)
                    ctx.stroke()

                    ctx.beginPath()
                    ctx.strokeStyle = root.withAlpha(root.secondaryLineColor, 0.14 + root.echoLevel * 0.20)
                    ctx.lineWidth = Math.max(1.0, root.lineWidth * 0.50)
                    ctx.arc(0, 0, sigilRoot.deepHaloRadius, 0, Math.PI * 2.0, false)
                    ctx.stroke()

                    ctx.restore()
                }

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.setTransform(1, 0, 0, 1, 0, 0)
                    ctx.clearRect(0, 0, width, height)
                    ctx.lineCap = "butt"
                    ctx.lineJoin = "miter"

                    var cx = width * 0.5
                    var cy = height * 0.5
                    var rr = sigilRoot.radius
                    var sectorAngle = 360.0 / root.sectorCount
                    var baseScale = root.sourceScale * root.overallScale * sigilRoot.breath
                    var layer2ParallaxX = Math.cos((root.outerRotation * 0.75 + root.wedgeRotation * 1.1) * Math.PI / 180.0) * rr * root.echoLevel * 0.018
                    var layer2ParallaxY = Math.sin((root.outerRotation * 0.58 + root.wedgeRotation * 0.92) * Math.PI / 180.0) * rr * root.echoLevel * 0.014
                    var layers = [
                        {
                            scale: 1.0,
                            opacity: 1.0,
                            spin: 1.0,
                            wedge: 1.0,
                            detail: 1.0,
                            ox: 0.0,
                            oy: 0.0,
                            accent: 0.0
                        }
                    ]

                    if (root.layer2Enabled) {
                        layers.push({
                            scale: root.layer2Scale,
                            opacity: root.layer2Opacity,
                            spin: root.layer2SpinMultiplier,
                            wedge: root.layer2WedgeMultiplier,
                            detail: root.layer2DetailMultiplier,
                            ox: layer2ParallaxX,
                            oy: layer2ParallaxY,
                            accent: root.echoLevel
                        })
                    }

                    for (var li = 0; li < layers.length; ++li) {
                        var layer = layers[li]
                        var layerPhase = root.sectorPhaseOffsetDeg + root.wedgeRotation * layer.wedge
                        var layerRotation = root.outerRotation * layer.spin
                        var layerScale = baseScale * layer.scale

                        for (var sector = 0; sector < root.sectorCount; ++sector) {
                            ctx.save()
                            ctx.translate(cx + layer.ox, cy + layer.oy)
                            ctx.rotate((layerPhase + sector * sectorAngle) * Math.PI / 180.0)
                            beginWedgeClip(ctx, rr, sectorAngle)
                            ctx.rotate(layerRotation * Math.PI / 180.0)
                            if ((sector % 2) === 1) {
                                ctx.scale(-1, 1)
                            }
                            ctx.scale(layerScale, layerScale)
                            drawRitualSource(ctx, rr, layer.detail, layer.opacity, layer.accent)
                            ctx.restore()
                        }
                    }

                    drawOverlay(ctx, cx, cy, rr)
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: root.theme.spacing.sm
            text: "octilinear mirror lattice / dual-depth kaleidoscope"
            color: root.theme.colors.text_secondary
            font.family: root.theme.typography.secondary_text.families[0]
            font.pixelSize: root.theme.typography.secondary_text.size
            font.weight: root.fontWeight("secondary_text")
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
