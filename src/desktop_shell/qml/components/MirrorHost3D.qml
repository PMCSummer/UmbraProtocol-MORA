import QtQuick
import QtQuick.Controls
import QtQuick3D

Rectangle {
    id: root
    required property var theme
    required property var bridge
    color: root.theme.colors.panel_secondary
    border.width: root.theme.lines.thin
    border.color: root.theme.colors.divider_subtle

    property var currentOrientation: Qt.quaternion(1, 0, 0, 0)
    property var targetOrientation: Qt.quaternion(1, 0, 0, 0)
    property var driftAxis: Qt.vector3d(0.0, 1.0, 0.0)
    property real precessionPhase: 0.0
    property double nextTargetMs: 0.0
    property double lastTickMs: 0.0

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    function reducedMotion() {
        return root.bridge.reducedMotionPreferred()
    }

    function motionScale() {
        return reducedMotion()
            ? root.theme.mirror.reduced_motion_scale
            : root.theme.mirror.base_motion_intensity
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
            return Qt.vector3d(0, 1, 0)
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

    function scheduleNextTarget(nowMs) {
        var low = root.theme.mirror.min_target_interval_s * intervalScale()
        var high = root.theme.mirror.max_target_interval_s * intervalScale()
        nextTargetMs = nowMs + randomBetween(low, high) * 1000.0
    }

    function buildNextTargetOrientation() {
        var randomAxis = vNormalize(Qt.vector3d(
            randomBetween(-1.0, 1.0),
            randomBetween(-0.35, 1.0),
            randomBetween(-1.0, 1.0)
        ))
        driftAxis = vNormalize(vLerp(driftAxis, randomAxis, 0.34))
        var sign = Math.random() > 0.5 ? 1.0 : -1.0
        var minDelta = root.theme.mirror.target_delta_min_deg * motionScale()
        var maxDelta = root.theme.mirror.target_delta_max_deg * motionScale()
        var delta = sign * randomBetween(minDelta, maxDelta)
        var deltaRotation = qFromAxisAngle(driftAxis, delta)
        var candidate = qNormalize(qMul(deltaRotation, targetOrientation))
        if (Math.abs(qDot(candidate, targetOrientation)) > 0.996) {
            candidate = qNormalize(qMul(qFromAxisAngle(driftAxis, delta * 1.35), targetOrientation))
        }
        return candidate
    }

    function composeDisplayOrientation() {
        var precessionAxis = vNormalize(Qt.vector3d(0.18, 1.0, 0.09))
        var precessionAmplitude = root.theme.mirror.precession_max_deg
            * root.theme.mirror.precession_intensity
            * motionScale()
        var precessionDeg = Math.sin(precessionPhase) * precessionAmplitude
        var precessionQ = qFromAxisAngle(precessionAxis, precessionDeg)
        return qNormalize(qMul(precessionQ, currentOrientation))
    }

    function tick(nowMs) {
        var dt = clamp((nowMs - lastTickMs) / 1000.0, 0.0, 0.2)
        lastTickMs = nowMs

        if (nowMs >= nextTargetMs) {
            targetOrientation = buildNextTargetOrientation()
            scheduleNextTarget(nowMs)
        }

        var response = root.theme.mirror.slerp_response * motionScale()
        var blend = 1.0 - Math.exp(-response * dt)
        blend = clamp(blend, 0.0, 0.2)
        currentOrientation = qSlerp(currentOrientation, targetOrientation, blend)

        precessionPhase += dt * (Math.PI * 2.0) * root.theme.mirror.precession_frequency_hz * motionScale()
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
                z: 420
                y: 8
            }

            DirectionalLight {
                eulerRotation.x: -24
                eulerRotation.y: 36
                brightness: 0.52
                ambientColor: root.theme.colors.geometry_white
            }

            Node {
                id: mirrorNode
                Model {
                    source: "#Sphere"
                    scale: Qt.vector3d(1.38, 1.38, 1.38)
                    materials: PrincipledMaterial {
                        baseColor: root.theme.colors.geometry_white
                        metalness: 0.0
                        roughness: 0.98
                        opacity: 0.05
                    }
                }

                Model {
                    source: "#Cube"
                    scale: Qt.vector3d(1.94, 0.014, 0.014)
                    materials: PrincipledMaterial {
                        baseColor: root.theme.colors.geometry_white
                        metalness: 0.0
                        roughness: 1.0
                    }
                }

                Model {
                    source: "#Cube"
                    scale: Qt.vector3d(0.014, 1.94, 0.014)
                    materials: PrincipledMaterial {
                        baseColor: root.theme.colors.geometry_white
                        metalness: 0.0
                        roughness: 1.0
                    }
                }

                Model {
                    source: "#Cone"
                    y: -62
                    scale: Qt.vector3d(1.08, 0.68, 1.08)
                    eulerRotation.x: 180
                    materials: PrincipledMaterial {
                        baseColor: root.theme.colors.text_secondary
                        metalness: 0.0
                        roughness: 1.0
                        opacity: 0.34
                    }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: root.theme.spacing.sm
            text: "mirror v1 idle engine"
            color: root.theme.colors.text_secondary
            font.family: root.theme.typography.secondary_text.families[0]
            font.pixelSize: root.theme.typography.secondary_text.size
            font.weight: root.fontWeight("secondary_text")
        }
    }

    Timer {
        id: ticker
        interval: 16
        repeat: true
        running: true
        onTriggered: root.tick(Date.now())
    }

    Component.onCompleted: {
        var now = Date.now()
        lastTickMs = now
        currentOrientation = Qt.quaternion(1, 0, 0, 0)
        targetOrientation = buildNextTargetOrientation()
        scheduleNextTarget(now)
        mirrorNode.rotation = composeDisplayOrientation()
    }
}

