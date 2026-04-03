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

    function fontWeight(roleName) {
        return root.theme.typography[roleName].weight === "bold" ? Font.DemiBold : Font.Normal
    }

    Text {
        id: title
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.leftMargin: root.theme.spacing.lg
        anchors.topMargin: root.theme.spacing.lg
        text: "Mirror Host"
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
                id: camera
                z: 420
                y: 10
            }

            DirectionalLight {
                eulerRotation.x: -25
                eulerRotation.y: 35
                brightness: 0.55
                ambientColor: root.theme.colors.geometry_white
            }

            Node {
                id: mirrorNode
                eulerRotation.y: 16
                Model {
                    source: "#Sphere"
                    scale: Qt.vector3d(1.4, 1.4, 1.4)
                    materials: PrincipledMaterial {
                        baseColor: root.theme.colors.geometry_white
                        metalness: 0.0
                        roughness: 0.96
                        opacity: 0.06
                    }
                }
                Model {
                    source: "#Cube"
                    scale: Qt.vector3d(1.9, 0.015, 0.015)
                    materials: PrincipledMaterial {
                        baseColor: root.theme.colors.geometry_white
                        metalness: 0.0
                        roughness: 1.0
                    }
                }
                Model {
                    source: "#Cube"
                    scale: Qt.vector3d(0.015, 1.9, 0.015)
                    materials: PrincipledMaterial {
                        baseColor: root.theme.colors.geometry_white
                        metalness: 0.0
                        roughness: 1.0
                    }
                }
                Model {
                    source: "#Cone"
                    y: -62
                    scale: Qt.vector3d(1.1, 0.7, 1.1)
                    eulerRotation.x: 180
                    materials: PrincipledMaterial {
                        baseColor: root.theme.colors.text_secondary
                        metalness: 0.0
                        roughness: 1.0
                        opacity: 0.4
                    }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: root.theme.spacing.sm
            text: "Qt Quick 3D foundation host"
            color: root.theme.colors.text_secondary
            font.family: root.theme.typography.secondary_text.families[0]
            font.pixelSize: root.theme.typography.secondary_text.size
            font.weight: root.fontWeight("secondary_text")
        }
    }

    NumberAnimation {
        id: ambientTurn
        target: mirrorNode
        property: "eulerRotation.y"
        from: 12
        to: 20
        duration: root.theme.timing.slow_settle_ms * 80
        loops: Animation.Infinite
        running: !root.bridge.reducedMotionPreferred()
        easing.type: Easing.InOutSine
    }
}
