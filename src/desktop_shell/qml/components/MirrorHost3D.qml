import QtQuick
import QtQuick.Controls
import QtQuick3D

Rectangle {
    id: root
    required property var theme
    required property var bridge
    property bool active: true
    opacity: active ? 1.0 : 0.0
    y: active ? 0 : root.phaseShiftDistance()
    color: root.theme.colors.panel_secondary
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle

    property var currentOrientation: Qt.quaternion(1, 0, 0, 0)
    property var targetOrientation: Qt.quaternion(1, 0, 0, 0)
    property var driftAxis: Qt.vector3d(0.0, 1.0, 0.0)
    property real precessionPhase: 0.0
    property real semanticPhase: 0.0
    property real orbitPhase: 0.0
    property double nextTargetMs: 0.0
    property double lastTickMs: 0.0

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
    property real targetStructuralAsymmetry: 0.0
    property real targetDensityLevel: 0.0
    property real targetEchoLevel: 0.0
    property real targetCenterOffsetX: 0.0
    property real targetCenterOffsetY: 0.0
    property real targetOrbitalActivity: 0.0
    property real targetSpeedScalar: 1.0
    property real targetDriftIrregularity: 0.0
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

    function approach(currentValue, targetValue, dt, durationMs) {
        var sec = Math.max(0.01, durationMs / 1000.0)
        var alpha = 1.0 - Math.exp(-dt / sec)
        return currentValue + (targetValue - currentValue) * alpha
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

    function qSlerp(a, b, t) {
        var qa = qNormalize(a)
        var qb = qNormalize(b)
        var dot = qDot(qa, qb)
        if (dot < 0.0) {
            qb = Qt.quaternion(-qb.scalar, -qb.x, -qb.y, -qb.z)
            dot = -dot
        }
        dot = clamp(dot, -1.0, 1.0)

        if (dot > 0.9995) {
            var lerped = Qt.quaternion(
                qa.scalar + (qb.scalar - qa.scalar) * t,
                qa.x + (qb.x - qa.x) * t,
                qa.y + (qb.y - qa.y) * t,
                qa.z + (qb.z - qa.z) * t
            )
            return qNormalize(lerped)
        }

        var theta0 = Math.acos(dot)
        var theta = theta0 * t
        var sinTheta = Math.sin(theta)
        var sinTheta0 = Math.sin(theta0)
        var s0 = Math.cos(theta) - dot * sinTheta / sinTheta0
        var s1 = sinTheta / sinTheta0
        return qNormalize(Qt.quaternion(
            qa.scalar * s0 + qb.scalar * s1,
            qa.x * s0 + qb.x * s1,
            qa.y * s0 + qb.y * s1,
            qa.z * s0 + qb.z * s1
        ))
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

        targetStructuralAsymmetry = clamp(
            c * root.theme.mirror_semantics.symmetry_conflict_influence
            - r * root.theme.mirror_semantics.symmetry_recovery_restore,
            0.0,
            0.36
        )

        targetDensityLevel = clamp(
            p * root.theme.mirror_semantics.density_pressure_scale
            + c * root.theme.mirror_semantics.density_conflict_scale
            - r * 0.24,
            0.0,
            1.0
        )

        targetEchoLevel = clamp(
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
        targetCenterOffsetX = clamp(driftAxis.x, -1.0, 1.0) * offsetMagnitude * 0.66
        targetCenterOffsetY = clamp(driftAxis.z, -1.0, 1.0) * offsetMagnitude * 0.5

        targetOrbitalActivity = clamp(
            (p * 0.64 + c * 0.52 + (1.0 - u) * 0.18)
            * root.theme.mirror_semantics.orbital_activity_scale
            - r * 0.26,
            0.0,
            0.9
        )

        targetSpeedScalar = clamp(
            1.0
            + p * root.theme.mirror_semantics.motion_pressure_speedup
            + c * root.theme.mirror_semantics.motion_conflict_irregularity * 0.52
            - r * root.theme.mirror_semantics.motion_recovery_calm
            + u * 0.1,
            0.58,
            1.72
        )

        targetDriftIrregularity = clamp(
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
            - targetDriftIrregularity * 0.18
            + semanticRecovery * 0.25,
            0.72,
            1.46
        )
    }

    function scheduleNextTarget(nowMs) {
        var low = root.theme.mirror.min_target_interval_s * intervalScale() * semanticIntervalMultiplier()
        var high = root.theme.mirror.max_target_interval_s * intervalScale() * semanticIntervalMultiplier()
        if (high <= low + 0.35) {
            high = low + 0.35
        }
        nextTargetMs = nowMs + randomBetween(low, high) * 1000.0
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

    function composeDisplayOrientation() {
        var precessionAxis = vNormalize(Qt.vector3d(0.19, 1.0, 0.11))
        var precessionAmplitude = root.theme.mirror.precession_max_deg
            * root.theme.mirror.precession_intensity
            * motionScale()
            * clamp(1.0 + semanticPressure * 0.26 + driftIrregularity * 0.24 - semanticRecovery * 0.18, 0.64, 1.44)
        var precessionDeg = Math.sin(precessionPhase) * precessionAmplitude
        var precessionQ = qFromAxisAngle(precessionAxis, precessionDeg)
        return qNormalize(qMul(precessionQ, currentOrientation))
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
        return index * (360.0 / 4.0) + orbitPhase * 57.2958
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

    function tick(nowMs) {
        var dt = clamp((nowMs - lastTickMs) / 1000.0, 0.0, 0.2)
        lastTickMs = nowMs

        structuralAsymmetry = approach(structuralAsymmetry, targetStructuralAsymmetry, dt, motionDuration("shear_drift_ms"))
        densityLevel = approach(densityLevel, targetDensityLevel, dt, motionDuration("line_reveal_ms"))
        echoLevel = approach(echoLevel, targetEchoLevel, dt, motionDuration("ghost_echo_ms"))
        centerOffsetX = approach(centerOffsetX, targetCenterOffsetX, dt, motionDuration("shear_drift_ms"))
        centerOffsetY = approach(centerOffsetY, targetCenterOffsetY, dt, motionDuration("shear_drift_ms"))
        orbitalActivity = approach(orbitalActivity, targetOrbitalActivity, dt, motionDuration("phase_shift_ms"))
        speedScalar = approach(speedScalar, targetSpeedScalar, dt, motionDuration("convergence_ms"))
        driftIrregularity = approach(driftIrregularity, targetDriftIrregularity, dt, motionDuration("convergence_ms"))

        if (nowMs >= nextTargetMs) {
            targetOrientation = buildNextTargetOrientation()
            scheduleNextTarget(nowMs)
            recomputeSemanticCarrier()
        }

        var response = root.theme.mirror.slerp_response * motionScale() * speedScalar
        var blend = 1.0 - Math.exp(-response * dt)
        blend = clamp(blend * (1.0 + Math.sin(semanticPhase * 0.71) * driftIrregularity * 0.08), 0.0, 0.22)
        currentOrientation = qSlerp(currentOrientation, targetOrientation, blend)

        var frequency = root.theme.mirror.precession_frequency_hz * clamp(
            1.0 + semanticPressure * 0.4 + driftIrregularity * 0.24 - semanticRecovery * 0.26,
            0.62,
            1.42
        )
        precessionPhase += dt * (Math.PI * 2.0) * frequency
        semanticPhase += dt * (0.32 + speedScalar * 0.14)
        orbitPhase += dt * (0.22 + speedScalar * 0.58)
        mirrorNode.rotation = composeDisplayOrientation()
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

            Node {
                id: mirrorNode

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
                                materials: PrincipledMaterial {
                                    baseColor: root.mainLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.mainLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.secondaryLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: 0.78
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.secondaryLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: 0.78
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.secondaryLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: 0.66
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.secondaryLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: 0.66
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.mainLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: 0.74
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.secondaryLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: 0.5 + root.secondaryDetailOpacity * 0.3
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.accentLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: root.secondaryDetailOpacity
                                }
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
                                materials: PrincipledMaterial {
                                    baseColor: root.mainLineColor
                                    metalness: 0.0
                                    roughness: 1.0
                                    opacity: 0.82
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
                            materials: PrincipledMaterial {
                                baseColor: root.secondaryLineColor
                                metalness: 0.0
                                roughness: 1.0
                                opacity: 0.5
                            }
                        }
                    }
                }

                Node {
                    visible: root.orbitalActivity > 0.08
                    Repeater3D {
                        model: 4
                        delegate: Node {
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
                                    opacity: root.orbitalOpacity(index)
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
        id: ticker
        interval: root.reducedMotion() ? 42 : 24
        repeat: true
        running: root.active && root.visible
        onTriggered: root.tick(Date.now())
    }

    Connections {
        target: root.bridge
        function onMirrorSemanticInputChanged() {
            root.syncSemanticInput()
        }
    }

    Component.onCompleted: {
        syncSemanticInput()
        var now = Date.now()
        lastTickMs = now
        currentOrientation = Qt.quaternion(1, 0, 0, 0)
        targetOrientation = buildNextTargetOrientation()
        scheduleNextTarget(now)
        mirrorNode.rotation = composeDisplayOrientation()
    }

    onActiveChanged: {
        if (active) {
            lastTickMs = Date.now()
        }
    }
}
