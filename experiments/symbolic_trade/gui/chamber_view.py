from __future__ import annotations

from typing import Any

from .presentation_trace import ChamberEvent, PresentationFrame


def create_chamber_view_class(qt: dict[str, Any]):
    QWidget = qt["QWidget"]
    QColor = qt["QColor"]
    QFont = qt["QFont"]
    QPainter = qt["QPainter"]
    QPen = qt["QPen"]
    QRectF = qt["QRectF"]
    Qt = qt["Qt"]

    class ChamberView(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._frame: PresentationFrame | None = None
            self.setMinimumHeight(520)
            self.setMinimumWidth(760)

        def set_frame(self, frame: PresentationFrame | None) -> None:
            self._frame = frame
            self.update()

        def paintEvent(self, _event: Any) -> None:  # noqa: N802 - Qt API
            painter = QPainter(self)
            antialiasing = QPainter.RenderHint.Antialiasing if hasattr(QPainter, "RenderHint") else QPainter.Antialiasing
            painter.setRenderHint(antialiasing)
            rect = self.rect()
            painter.fillRect(rect, QColor("#f7f1e6"))

            if self._frame is None:
                painter.setPen(QPen(QColor("#4a4034"), 2))
                painter.drawText(rect, Qt.AlignCenter, "Сценарий ещё не запущен")
                return

            frame = self._frame
            state = frame.chamber_state
            w = max(760, rect.width())
            h = max(520, rect.height())
            margin = 34
            actor_w = int(w * 0.27)
            actor_h = int(h * 0.46)
            actor_y = int(h * 0.21)
            a_x = margin
            b_x = w - margin - actor_w
            wall_x = int(w * 0.49)
            wall_w = int(w * 0.045)

            self._draw_title(painter, frame, w)
            self._draw_actor(painter, a_x, actor_y, actor_w, actor_h, state.actor_a, "#d9edf7")
            self._draw_actor(painter, b_x, actor_y, actor_w, actor_h, state.actor_b, "#fff2cc")
            self._draw_wall(painter, wall_x, int(h * 0.16), wall_w, int(h * 0.56), state.aperture_open, state.aperture_status)
            self._draw_events(painter, frame.chamber_state.events, a_x, b_x, actor_y, actor_w, actor_h, wall_x, wall_w)
            self._draw_status_strip(painter, frame, w, h)
            self._draw_public_boundary(painter, w, h)

        def _draw_title(self, painter: Any, frame: PresentationFrame, width: int) -> None:
            painter.setPen(QPen(QColor("#2f2a24"), 1))
            painter.setFont(QFont("Segoe UI", 15, QFont.Bold))
            painter.drawText(QRectF(26, 18, width - 52, 34), Qt.AlignLeft | Qt.AlignVCenter, frame.title_ru)
            painter.setFont(QFont("Segoe UI", 10))
            painter.setPen(QPen(QColor("#5d5248"), 1))
            painter.drawText(QRectF(26, 52, width - 52, 46), Qt.TextWordWrap, frame.explanation_ru)

        def _draw_actor(self, painter: Any, x: int, y: int, width: int, height: int, actor: Any, color: str) -> None:
            painter.setPen(QPen(QColor("#5b554f"), 2))
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRectF(x, y, width, height), 16, 16)
            painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
            painter.setPen(QPen(QColor("#263238"), 1))
            painter.drawText(QRectF(x + 16, y + 12, width - 32, 34), Qt.AlignLeft | Qt.AlignVCenter, actor.label_ru)

            painter.setFont(QFont("Segoe UI", 10))
            line_y = y + 58
            if not actor.resources:
                painter.setPen(QPen(QColor("#7a7066"), 1))
                painter.drawText(QRectF(x + 16, line_y, width - 32, 28), Qt.AlignLeft, "ресурсы на этом кадре не раскрыты")
                line_y += 30
            for resource in actor.resources:
                fill = QColor("#76b7e5") if resource.resource_kind == "water" else QColor("#f2b35d")
                painter.setBrush(fill)
                painter.setPen(QPen(QColor("#4f4a44"), 1))
                painter.drawEllipse(QRectF(x + 18, line_y + 3, 18, 18))
                painter.setPen(QPen(QColor("#2f2a24"), 1))
                claim_suffix = " / claim" if resource.is_claim else ""
                painter.drawText(
                    QRectF(x + 44, line_y, width - 60, 26),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    f"{resource.resource_kind}: {resource.level_ru}{claim_suffix}",
                )
                line_y += 30
            painter.setPen(QPen(QColor("#6b6157"), 1))
            for note in actor.notes_ru:
                painter.drawText(QRectF(x + 16, line_y, width - 32, 26), Qt.TextWordWrap, f"• {note}")
                line_y += 28

        def _draw_wall(self, painter: Any, x: int, y: int, width: int, height: int, open_: bool, status: str) -> None:
            painter.setPen(QPen(QColor("#6e6258"), 2))
            painter.setBrush(QColor("#cfc6bc"))
            painter.drawRoundedRect(QRectF(x, y, width, height), 8, 8)
            aperture_h = int(height * 0.22)
            aperture_y = y + int(height * 0.39)
            painter.setBrush(QColor("#8bc34a") if open_ else QColor("#d45b55"))
            painter.drawRoundedRect(QRectF(x - 8, aperture_y, width + 16, aperture_h), 8, 8)
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.setPen(QPen(QColor("#2f2a24"), 1))
            painter.drawText(QRectF(x - 60, y + height + 10, width + 120, 28), Qt.AlignCenter, f"апертура: {status}")

        def _event_color(self, event: ChamberEvent) -> Any:
            mapping = {
                "claim": "#1e88e5",
                "offer_candidate": "#43a047",
                "affordance_selection": "#7b1fa2",
                "invocation_request": "#fb8c00",
                "world_actuator_invocation": "#e65100",
                "transfer_result": "#00897b",
                "completion_verification": "#2e7d32",
            }
            if event.causal_status in {"not_verified", "request_not_execution", "selection_not_invocation"}:
                return QColor(mapping.get(event.event_kind, "#6d6d6d"))
            return QColor(mapping.get(event.event_kind, "#455a64"))

        def _draw_arrow(self, painter: Any, x1: int, y1: int, x2: int, y2: int, color: Any, dashed: bool = False) -> None:
            pen = QPen(color, 4)
            if dashed:
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)
            direction = 1 if x2 >= x1 else -1
            painter.drawLine(x2, y2, x2 - direction * 14, y2 - 8)
            painter.drawLine(x2, y2, x2 - direction * 14, y2 + 8)

        def _draw_events(
            self,
            painter: Any,
            events: tuple[ChamberEvent, ...],
            a_x: int,
            b_x: int,
            actor_y: int,
            actor_w: int,
            actor_h: int,
            wall_x: int,
            wall_w: int,
        ) -> None:
            base_y = actor_y + actor_h + 34
            a_right = a_x + actor_w
            b_left = b_x
            row = 0
            for event in events:
                if not event.active:
                    continue
                color = self._event_color(event)
                y = base_y + row * 36
                dashed = event.causal_status in {"claim_not_fact", "passive_observation", "пассивное наблюдение"}
                if event.source_actor == "B":
                    self._draw_arrow(painter, b_left, y, a_right, y, color, dashed=dashed)
                    text_x = a_right + 16
                elif event.source_actor == "world_actuator":
                    self._draw_arrow(painter, wall_x + wall_w + 20, y, b_left - 18, y, color, dashed=False)
                    text_x = wall_x + wall_w + 30
                else:
                    self._draw_arrow(painter, a_right, y, b_left, y, color, dashed=dashed)
                    text_x = a_right + 20
                painter.setBrush(QColor("#ffffff"))
                painter.setPen(QPen(color, 2))
                painter.drawRoundedRect(QRectF(text_x, y - 15, 310, 30), 10, 10)
                painter.setFont(QFont("Segoe UI", 9))
                painter.setPen(QPen(QColor("#2f2a24"), 1))
                painter.drawText(QRectF(text_x + 10, y - 14, 292, 28), Qt.AlignLeft | Qt.AlignVCenter, event.label_ru)
                row += 1

        def _draw_badge(self, painter: Any, x: int, y: int, width: int, text: str, ok: bool | None) -> None:
            color = "#dff0d8" if ok is True else ("#f2dede" if ok is False else "#eeeeee")
            border = "#3c763d" if ok is True else ("#a94442" if ok is False else "#777777")
            painter.setBrush(QColor(color))
            painter.setPen(QPen(QColor(border), 1))
            painter.drawRoundedRect(QRectF(x, y, width, 30), 8, 8)
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QPen(QColor("#2f2a24"), 1))
            painter.drawText(QRectF(x + 10, y + 3, width - 18, 24), Qt.AlignLeft | Qt.AlignVCenter, text)

        def _draw_status_strip(self, painter: Any, frame: PresentationFrame, width: int, height: int) -> None:
            state = frame.chamber_state
            y = height - 88
            badge_w = max(132, int((width - 80) / 5))
            x = 28
            self._draw_badge(painter, x, y, badge_w, f"Пассивные: {state.passive_packet_ref_count}", None)
            x += badge_w + 6
            self._draw_badge(painter, x, y, badge_w, f"Каузальные: {state.causal_post_invocation_ref_count}", state.causal_post_invocation_ref_count > 0)
            x += badge_w + 6
            self._draw_badge(painter, x, y, badge_w, f"Actuator: {'да' if state.actuator_invoked_visible else 'нет'}", state.actuator_invoked_visible)
            x += badge_w + 6
            self._draw_badge(painter, x, y, badge_w, f"Результат: {state.transfer_result}", None)
            x += badge_w + 6
            self._draw_badge(painter, x, y, badge_w, f"Completion: {'да' if state.completion_claim else 'нет'}", state.completion_claim)

        def _draw_public_boundary(self, painter: Any, width: int, height: int) -> None:
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QPen(QColor("#5d5248"), 1))
            text = "Символическая сцена: не физическая симуляция, не motor-control proof, не автономная торговля."
            painter.drawText(QRectF(28, height - 44, width - 56, 24), Qt.AlignLeft | Qt.AlignVCenter, text)

    return ChamberView
