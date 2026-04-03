pragma ComponentBehavior: Bound
import QtQuick
import QtQuick3D
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

    property var currentOrientation: Qt.quaternion(1, 0, 0, 0)
    property var targetOrientation: Qt.quaternion(1, 0, 0, 0)
    property var driftAxis: Qt.vector3d(0.0, 1.0, 0.0)
    property var precessionOrientation: Qt.quaternion(1, 0, 0, 0)
    property real orbitAngleOffset: 0.0

    property real semanticPressure: 0.12
    property real semanticUncertainty: 0.1
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

    property int ringSegments: 8
    property real outerRadius: 116.0
    property real innerRadius: 70.0
    property real depthHalf: 33.0
    property real edgeThickness: 0.022
    property real outerSegmentLength: chordScale(outerRadius) * 0.98
    property real innerSegmentLength: chordScale(innerRadius) * 0.98
    property real radialBridgeLength: Math.max(0.14, ((outerRadius - innerRadius) / 100.0) * 0.96)
    property real depthBridgeLength: ((depthHalf * 2.0) / 100.0) * 0.94

    property real outerYScale: 1.0
    property real innerYScale: 0.9
    property real secondaryDetailOpacity: clamp(0.08 + densityLevel * 0.56, 0.08, 0.72)
    property real ghostOpacity: clamp(0.02 + echoLevel * 0.4, 0.0, 0.44)
    property int orbitalNodeCount: Math.max(0, Math.min(3, Math.round(orbitalActivity * 3.0)))
    property real orbitalRadius: root.theme.mirror_semantics.orbital_radius

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

    function motionScale() {
        return reducedMotion()
            ? root.theme.mirror.reduced_motion_scale
            : root.theme.mirror.base_motion_intensity
    }

    function semanticScale() {
        return reducedMotion()
            ? root.theme.mirror_semantics.reduced_semantic_scale
            : 1.0
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

    function chordScale(radius) {
        return (2.0 * radius * Math.sin(Math.PI / ringSegments)) / 100.0
    }

    function qNormalize(q) {
        var n = Math.sqrt(q.scalar * q.scalar + q.x * q.x + q.y * q.y + q.z * q.z)
        if (n <= 0.0000001) {
            return Qt.quaternion(1, 0, 0, 0)
        }
        return Qt.quaternion(q.scalar / n, q.x / n, q.y / n, q.z / n)
    }

    function qDot(a, b) {
        return a.scalar * b.scalar + a.x * b.x + a.y * b.y + a.z * b.z
    }

    function qMul(a, b) {
        return Qt.quaternion(
            a.scalar * b.scalar - a.x * b.x - a.y * b.y - a.z * b.z,
            a.scalar * b.x + a.x * b.scalar + a.y * b.z - a.z * b.y,
            a.scalar * b.y - a.x * b.z + a.y * b.scalar + a.z * b.x,
            a.scalar * b.z + a.x * b.y - a.y * b.x + a.z * b.scalar
        )
    }

    function vNormalize(v) {
        var n = Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        if (n <= 0.0000001) {
            return Qt.vector3d(0.0, 1.0, 0.0)
        }
        return Qt.vector3d(v.x / n, v.y / n, v.z / n)
    }

    function vLerp(a, b, t) {
        return Qt.vector3d(
            a.x + (b.x - a.x) * t,
            a.y + (b.y - a.y) * t,
            a.z + (b.z - a.z) * t
        )
    }

    function qFromAxisAngle(axis, angleDeg) {
        var na = vNormalize(axis)
        var half = angleDeg * Math.PI / 360.0
        var s = Math.sin(half)
        return qNormalize(Qt.quaternion(Math.cos(half), na.x * s, na.y * s, na.z * s))
    }

    function levelFromInput(payload, key, fallback) {
        if (!payload || payload[key] === undefined || payload[key] === null) {
            return fallback
        }
        return clamp(Number(payload[key]), 0.0, 1.0)
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
            0.36
        )

        densityLevel = clamp(
            p * root.theme.mirror_semantics.density_pressure_scale
            + c * root.theme.mirror_semantics.density_conflict_scale
            - r * 0.24,
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
            22.0
        )
        centerOffsetX = clamp(driftAxis.x, -1.0, 1.0) * offsetMagnitude * 0.66
        centerOffsetY = clamp(driftAxis.z, -1.0, 1.0) * offsetMagnitude * 0.5

        orbitalActivity = clamp(
            (p * 0.64 + c * 0.52 + (1.0 - u) * 0.18)
            * root.theme.mirror_semantics.orbital_activity_scale
            - r * 0.26,
            0.0,
            0.9
        )

        speedScalar = clamp(
            1.0
            + p * root.theme.mirror_semantics.motion_pressure_speedup
            + c * root.theme.mirror_semantics.motion_conflict_irregularity * 0.52
            - r * root.theme.mirror_semantics.motion_recovery_calm
            + u * 0.1,
            0.58,
            1.72
        )

        driftIrregularity = clamp(
            c * root.theme.mirror_semantics.motion_conflict_irregularity
            + u * root.theme.mirror_semantics.motion_uncertainty_drift
            - r * 0.12,
            0.0,
            0.42
        )

        var severity = clamp(p * 0.56 + c * 0.56 + u * 0.33 - r * 0.28 + w * 0.72, 0.0, 1.0)
        warningActive = (severity >= root.theme.mirror_semantics.warning_gate
            && (p + c) > 1.18
            && r < 0.32) || w > 0.88

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

    function semanticIntervalMultiplier() {
        return clamp(
            1.0
            - semanticPressure * 0.24
            - driftIrregularity * 0.18
            + semanticRecovery * 0.25,
            0.72,
            1.46
        )
    }

    function scheduleNextTargetIntervalMs() {
        var low = root.theme.mirror.min_target_interval_s * intervalScale() * semanticIntervalMultiplier()
        var high = root.theme.mirror.max_target_interval_s * intervalScale() * semanticIntervalMultiplier()
        if (high <= low + 0.35) {
            high = low + 0.35
        }
        return Math.max(500, Math.round(randomBetween(low, high) * 1000.0))
    }

    function buildNextTargetOrientation() {
        var randomAxis = vNormalize(Qt.vector3d(
            randomBetween(-1.0, 1.0),
            randomBetween(-0.42, 1.0),
            randomBetween(-1.0, 1.0)
        ))
        var driftMix = clamp(0.24 + semanticPressure * 0.12 + driftIrregularity * 0.22, 0.18, 0.58)
        driftAxis = vNormalize(vLerp(driftAxis, randomAxis, driftMix))

        var sign = Math.random() > 0.5 ? 1.0 : -1.0
        var minDelta = root.theme.mirror.target_delta_min_deg * motionScale() * (1.0 + driftIrregularity * 0.22)
        var maxDelta = root.theme.mirror.target_delta_max_deg * motionScale() * (
            1.0 + driftIrregularity * 0.62 + semanticPressure * 0.2 - semanticRecovery * 0.16
        )
        maxDelta = Math.max(maxDelta, minDelta + 2.0)
        var delta = sign * randomBetween(minDelta, maxDelta)
        var candidate = qNormalize(qMul(qFromAxisAngle(driftAxis, delta), targetOrientation))
        if (Math.abs(qDot(candidate, targetOrientation)) > 0.996) {
            candidate = qNormalize(qMul(qFromAxisAngle(driftAxis, delta * 1.4), targetOrientation))
        }
        return candidate
    }

    function orientationDurationMs() {
        var base = root.motionDuration("convergence_ms")
        var scalar = clamp(1.4 - speedScalar * 0.42 + semanticRecovery * 0.2, 0.66, 1.72)
        return Math.max(180, Math.round(base * scalar))
    }

    function precessionDurationMs() {
        var base = root.motionDuration("phase_shift_ms") * 4
        return Math.max(900, Math.round(base * clamp(1.2 - speedScalar * 0.18, 0.86, 1.4)))
    }

    function precessionMaxDegrees() {
        return root.theme.mirror.precession_max_deg
            * root.theme.mirror.precession_intensity
            * motionScale()
            * clamp(1.0 + semanticPressure * 0.26 + driftIrregularity * 0.24 - semanticRecovery * 0.18, 0.64, 1.44)
    }

    function updatePrecessionTarget() {
        var precessionAxis = vNormalize(Qt.vector3d(0.19, 1.0, 0.11))
        var sign = Math.random() > 0.5 ? 1.0 : -1.0
        var nextDeg = sign * randomBetween(precessionMaxDegrees() * 0.35, precessionMaxDegrees())
        var next = qFromAxisAngle(precessionAxis, nextDeg)
        precessionAnim.stop()
        precessionAnim.from = precessionOrientation
        precessionAnim.to = next
        precessionAnim.duration = precessionDurationMs()
        precessionAnim.start()
    }

    function retargetOrientation() {
        targetOrientation = buildNextTargetOrientation()
        orientationAnim.stop()
        orientationAnim.from = currentOrientation
        orientationAnim.to = targetOrientation
        orientationAnim.duration = orientationDurationMs()
        orientationAnim.start()
    }

    function orbitDurationMs() {
        var base = reducedMotion() ? 76000 : 36000
        return Math.max(18000, Math.round(base / clamp(speedScalar, 0.62, 1.8)))
    }

    function angleRadians(angleDeg) {
        return angleDeg * Math.PI / 180.0
    }

    function ringX(baseRadius, angleDeg) {
        return Math.cos(angleRadians(angleDeg)) * baseRadius
    }

    function ringY(baseRadius, angleDeg, scaleY) {
        return Math.sin(angleRadians(angleDeg)) * baseRadius * scaleY
    }

    function orbitalAngle(index) {
        return index * (360.0 / 4.0) + orbitAngleOffset
    }

    function orbitalVisible(index) {
        return index < orbitalNodeCount && orbitalActivity > 0.08
    }

    function orbitalOpacity(index) {
        if (!orbitalVisible(index)) {
            return 0.0
        }
        var leadBoost = (index === 0 && semanticBand >= 2) ? 0.12 : 0.0
        return clamp(0.2 + orbitalActivity * 0.46 + leadBoost, 0.0, 0.76)
    }

    function startRuntimeEngines() {
        if (!runtimeActive) {
            return
        }
        targetTimer.interval = scheduleNextTargetIntervalMs()
        targetTimer.restart()

        precessionTimer.interval = precessionDurationMs()
        precessionTimer.restart()
        updatePrecessionTarget()

        if (orbitalActivity > 0.08) {
            orbitAnim.duration = orbitDurationMs()
            orbitAnim.start()
        } else {
            orbitAnim.stop()
        }
    }

    function stopRuntimeEngines() {
        targetTimer.stop()
        precessionTimer.stop()
        orientationAnim.stop()
        precessionAnim.stop()
        orbitAnim.stop()
    }

    Behavior on structuralAsymmetry {
        NumberAnimation {
            duration: root.motionDuration("shear_drift_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
        }
    }

    Behavior on densityLevel {
        NumberAnimation {
            duration: root.motionDuration("line_reveal_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
        }
    }

    Behavior on echoLevel {
        NumberAnimation {
            duration: root.motionDuration("ghost_echo_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
        }
    }

    Behavior on centerOffsetX {
        NumberAnimation {
            duration: root.motionDuration("shear_drift_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
        }
    }

    Behavior on centerOffsetY {
        NumberAnimation {
            duration: root.motionDuration("shear_drift_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
        }
    }

    Behavior on orbitalActivity {
        NumberAnimation {
            duration: root.motionDuration("phase_shift_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
        }
    }

    Behavior on speedScalar {
        NumberAnimation {
            duration: root.motionDuration("convergence_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
        }
    }

    Behavior on driftIrregularity {
        NumberAnimation {
            duration: root.motionDuration("convergence_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
        }
    }

    Behavior on secondaryLineColor {
        ColorAnimation {
            duration: root.motionDuration("fade_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
        }
    }

    Behavior on accentLineColor {
        ColorAnimation {
            duration: root.motionDuration("fade_ms")
            easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
        }
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
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: title.bottom
        anchors.bottom: parent.bottom
        anchors.margins: root.theme.spacing.lg
        color: root.theme.colors.input_background
        border.width: root.theme.lines.thin
        border.color: root.theme.colors.divider_subtle

        View3D {
            anchors.fill: parent

            environment: SceneEnvironment {
                backgroundMode: SceneEnvironment.Color
                clearColor: root.theme.colors.input_background
            }

            PerspectiveCamera {
                z: 472
                y: 2
            }

            DirectionalLight {
                eulerRotation.x: -26
                eulerRotation.y: 34
                brightness: 0.44
                ambientColor: root.theme.colors.geometry_white
            }

            DirectionalLight {
                eulerRotation.x: 16
                eulerRotation.y: -48
                brightness: 0.14
                ambientColor: root.theme.colors.text_secondary
            }

            PrincipledMaterial {
                id: matMain
                baseColor: root.mainLineColor
                metalness: 0.0
                roughness: 1.0
            }

            PrincipledMaterial {
                id: matSecondary
                baseColor: root.secondaryLineColor
                metalness: 0.0
                roughness: 1.0
                opacity: 0.78
            }

            PrincipledMaterial {
                id: matSecondaryBridge
                baseColor: root.secondaryLineColor
                metalness: 0.0
                roughness: 1.0
                opacity: 0.66
            }

            PrincipledMaterial {
                id: matMainDepth
                baseColor: root.mainLineColor
                metalness: 0.0
                roughness: 1.0
                opacity: 0.74
            }

            PrincipledMaterial {
                id: matInnerDepth
                baseColor: root.secondaryLineColor
                metalness: 0.0
                roughness: 1.0
                opacity: 0.5 + root.secondaryDetailOpacity * 0.3
            }

            PrincipledMaterial {
                id: matAccent
                baseColor: root.accentLineColor
                metalness: 0.0
                roughness: 1.0
                opacity: root.secondaryDetailOpacity
            }

            PrincipledMaterial {
                id: matCenter
                baseColor: root.mainLineColor
                metalness: 0.0
                roughness: 1.0
                opacity: 0.82
            }

            PrincipledMaterial {
                id: matGhost
                baseColor: root.secondaryLineColor
                metalness: 0.0
                roughness: 1.0
                opacity: 0.5
            }

            Node {
                id: mirrorNode
                rotation: root.currentOrientation

                Node {
                    id: precessionNode
                    rotation: root.precessionOrientation

                    Node {
                        id: artifactCarrier
                        position: Qt.vector3d(root.centerOffsetX, root.centerOffsetY, 0.0)

                        Node {
                            id: artifactBody
                            scale: Qt.vector3d(
                                1.0 + root.structuralAsymmetry * 0.06,
                                1.0 - root.structuralAsymmetry * 0.04,
                                1.0
                            )

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: root.ringX(root.outerRadius, angle)
                                    y: root.ringY(root.outerRadius, angle, root.outerYScale)
                                    z: root.depthHalf
                                    eulerRotation.z: angle + 90.0
                                    scale: Qt.vector3d(root.outerSegmentLength, root.edgeThickness, root.edgeThickness)
                                    materials: [matMain]
                                }
                            }

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: root.ringX(root.outerRadius, angle)
                                    y: root.ringY(root.outerRadius, angle, root.outerYScale)
                                    z: -root.depthHalf
                                    eulerRotation.z: angle + 90.0
                                    scale: Qt.vector3d(root.outerSegmentLength, root.edgeThickness, root.edgeThickness)
                                    materials: [matMain]
                                }
                            }

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: root.ringX(root.innerRadius, angle)
                                    y: root.ringY(root.innerRadius, angle, root.innerYScale)
                                    z: root.depthHalf
                                    eulerRotation.z: angle + 90.0
                                    scale: Qt.vector3d(root.innerSegmentLength, root.edgeThickness, root.edgeThickness)
                                    materials: [matSecondary]
                                }
                            }

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: root.ringX(root.innerRadius, angle)
                                    y: root.ringY(root.innerRadius, angle, root.innerYScale)
                                    z: -root.depthHalf
                                    eulerRotation.z: angle + 90.0
                                    scale: Qt.vector3d(root.innerSegmentLength, root.edgeThickness, root.edgeThickness)
                                    materials: [matSecondary]
                                }
                            }

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: (root.ringX(root.outerRadius, angle) + root.ringX(root.innerRadius, angle)) / 2.0
                                    y: (root.ringY(root.outerRadius, angle, root.outerYScale)
                                        + root.ringY(root.innerRadius, angle, root.innerYScale)) / 2.0
                                    z: root.depthHalf
                                    eulerRotation.z: angle
                                    scale: Qt.vector3d(root.radialBridgeLength, root.edgeThickness, root.edgeThickness)
                                    materials: [matSecondaryBridge]
                                }
                            }

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: (root.ringX(root.outerRadius, angle) + root.ringX(root.innerRadius, angle)) / 2.0
                                    y: (root.ringY(root.outerRadius, angle, root.outerYScale)
                                        + root.ringY(root.innerRadius, angle, root.innerYScale)) / 2.0
                                    z: -root.depthHalf
                                    eulerRotation.z: angle
                                    scale: Qt.vector3d(root.radialBridgeLength, root.edgeThickness, root.edgeThickness)
                                    materials: [matSecondaryBridge]
                                }
                            }

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: root.ringX(root.outerRadius, angle)
                                    y: root.ringY(root.outerRadius, angle, root.outerYScale)
                                    z: 0.0
                                    scale: Qt.vector3d(root.edgeThickness, root.edgeThickness, root.depthBridgeLength)
                                    materials: [matMainDepth]
                                }
                            }

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: root.ringX(root.innerRadius, angle)
                                    y: root.ringY(root.innerRadius, angle, root.innerYScale)
                                    z: 0.0
                                    scale: Qt.vector3d(root.edgeThickness, root.edgeThickness, root.depthBridgeLength * 0.92)
                                    materials: [matInnerDepth]
                                }
                            }

                            Repeater3D {
                                model: root.ringSegments
                                delegate: Model {
                                    required property int index
                                    readonly property real angle: index * (360.0 / root.ringSegments)
                                    source: "#Cube"
                                    x: (root.ringX(root.innerRadius, angle) * 0.6)
                                    y: (root.ringY(root.innerRadius, angle, root.innerYScale) * 0.6)
                                    z: 0.0
                                    eulerRotation.z: angle + 45.0
                                    scale: Qt.vector3d(root.innerSegmentLength * 0.7, root.edgeThickness, root.depthBridgeLength * 0.22)
                                    materials: [matAccent]
                                }
                            }

                            Repeater3D {
                                model: 4
                                delegate: Model {
                                    required property int index
                                    readonly property real ySlot: index < 2 ? (46 + index * 14) : (-46 - (index - 2) * 14)
                                    source: "#Cube"
                                    x: 0.0
                                    y: ySlot
                                    z: 0.0
                                    scale: Qt.vector3d(root.edgeThickness * 2.2, 0.24, root.depthBridgeLength * 0.84)
                                    materials: [matCenter]
                                }
                            }
                        }
                    }
                }

                Node {
                    visible: root.ghostOpacity > 0.02
                    opacity: root.ghostOpacity * 0.62
                    position: Qt.vector3d(root.centerOffsetX * 0.42, root.centerOffsetY * 0.42, 0.0)
                    scale: Qt.vector3d(1.04, 1.04, 1.02)
                    Repeater3D {
                        model: Math.max(4, Math.floor(root.ringSegments / 2))
                        delegate: Model {
                            required property int index
                            readonly property real angle: index * (360.0 / Math.max(4, Math.floor(root.ringSegments / 2)))
                            source: "#Cube"
                            x: root.ringX(root.outerRadius * 1.02, angle)
                            y: root.ringY(root.outerRadius * 1.02, angle, root.outerYScale)
                            z: 0.0
                            eulerRotation.z: angle + 90.0
                            scale: Qt.vector3d(root.outerSegmentLength * 0.98, root.edgeThickness * 0.88, root.depthBridgeLength * 0.8)
                            materials: [matGhost]
                        }
                    }
                }

                Node {
                    visible: root.orbitalActivity > 0.08
                    Repeater3D {
                        model: 4
                        delegate: Node {
                            id: orbitalNode
                            required property int index
                            readonly property real angle: root.orbitalAngle(index)
                            visible: root.orbitalVisible(index)
                            x: Math.cos(root.angleRadians(angle)) * root.orbitalRadius
                            y: Math.sin(root.angleRadians(angle)) * root.orbitalRadius * 0.72
                            z: Math.sin(root.angleRadians(angle * 0.7 + 24.0)) * 18.0
                            Model {
                                source: "#Sphere"
                                scale: Qt.vector3d(0.052, 0.052, 0.052)
                                materials: PrincipledMaterial {
                                    baseColor: root.semanticBand >= 2 ? root.accentLineColor : root.secondaryLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: root.orbitalOpacity(orbitalNode.index)
                                }
                            }
                        }
                    }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: root.theme.spacing.sm
            text: "semantic mirror v1"
            color: root.theme.colors.text_secondary
            font.family: root.theme.typography.secondary_text.families[0]
            font.pixelSize: root.theme.typography.secondary_text.size
            font.weight: root.fontWeight("secondary_text")
        }
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

    Timer {
        id: targetTimer
        interval: 1000
        repeat: false
        running: false
        onTriggered: {
            root.retargetOrientation()
            interval = root.scheduleNextTargetIntervalMs()
            start()
        }
    }

    Timer {
        id: precessionTimer
        interval: 1800
        repeat: true
        running: false
        onTriggered: {
            root.updatePrecessionTarget()
            interval = root.precessionDurationMs()
        }
    }

    QuaternionAnimation {
        id: orientationAnim
        target: root
        property: "currentOrientation"
        duration: root.motionDuration("convergence_ms")
        easing.type: root.easingForClass(root.theme.motion.easing_soft_standard)
    }

    QuaternionAnimation {
        id: precessionAnim
        target: root
        property: "precessionOrientation"
        duration: root.motionDuration("phase_shift_ms")
        easing.type: root.easingForClass(root.theme.motion.easing_slow_settle)
    }

    NumberAnimation {
        id: orbitAnim
        target: root
        property: "orbitAngleOffset"
        from: 0
        to: 360
        duration: 36000
        loops: Animation.Infinite
        easing.type: Easing.Linear
    }

    Connections {
        target: root.bridge
        function onMirrorSemanticInputChanged() {
            root.syncSemanticInput()
            if (root.runtimeActive && root.orbitalActivity > 0.08) {
                orbitAnim.stop()
                orbitAnim.duration = root.orbitDurationMs()
                orbitAnim.start()
            }
        }
    }

    Component.onCompleted: {
        syncSemanticInput()
        currentOrientation = Qt.quaternion(1, 0, 0, 0)
        targetOrientation = buildNextTargetOrientation()
        precessionOrientation = Qt.quaternion(1, 0, 0, 0)
        if (runtimeActive) {
            retargetOrientation()
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

    onSpeedScalarChanged: {
        if (runtimeActive && orbitAnim.running) {
            orbitAnim.stop()
            orbitAnim.duration = orbitDurationMs()
            orbitAnim.start()
        }
    }

    onOrbitalActivityChanged: {
        if (!runtimeActive) {
            return
        }
        if (orbitalActivity > 0.08) {
            orbitAnim.duration = orbitDurationMs()
            orbitAnim.start()
        } else {
            orbitAnim.stop()
        }
    }
}
