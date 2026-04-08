from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPen, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QDockWidget,
)

try:
    from .model import (
        CLAIM_ROLE_LABELS,
        CLAIM_STATE_LABELS,
        DEFAULT_CLAIM_STATE,
        DEFAULT_EVIDENCE_ROLE,
        DEFAULT_EVIDENCE_STATUS,
        DEFAULT_MATURITY,
        DEFAULT_STATUS,
        EDGE_RELATION_LABELS,
        EVIDENCE_MECHANISTIC_FIELDS,
        EVIDENCE_RELATION_OPTIONS,
        EVIDENCE_ROLE_LABELS,
        EVIDENCE_STATUS_LABELS,
        GRAPH_LAYER_LABELS,
        MATURITY_LABELS,
        NODE_TYPE_LABELS,
        PRIORITY_LABELS,
        STATUS_LABELS,
        TRACK_LABELS,
        VALIDATION_LABELS,
        display_from_map,
        build_mechanistic_payload_from_text_map,
        dedupe_preserve_order,
        evidence_missing_fields,
        extract_extra_mechanistic_payload,
        list_to_textblock,
        mechanistic_payload_to_text_map,
        normalize_code,
        phase_objective_text,
        relation_is_challenging,
        relation_is_supporting,
        reverse_lookup,
        textblock_to_list,
        AlternativeModel,
        EvidenceEntry,
        GraphEdge,
        GraphNode,
        GovernanceGate,
        KnowledgeCard,
        LegacyRoadmapParser,
        Phase,
        RoadmapModel,
    )
except ImportError:
    from model import (
        CLAIM_ROLE_LABELS,
        CLAIM_STATE_LABELS,
        DEFAULT_CLAIM_STATE,
        DEFAULT_EVIDENCE_ROLE,
        DEFAULT_EVIDENCE_STATUS,
        DEFAULT_MATURITY,
        DEFAULT_STATUS,
        EDGE_RELATION_LABELS,
        EVIDENCE_MECHANISTIC_FIELDS,
        EVIDENCE_RELATION_OPTIONS,
        EVIDENCE_ROLE_LABELS,
        EVIDENCE_STATUS_LABELS,
        GRAPH_LAYER_LABELS,
        MATURITY_LABELS,
        NODE_TYPE_LABELS,
        PRIORITY_LABELS,
        STATUS_LABELS,
        TRACK_LABELS,
        VALIDATION_LABELS,
        display_from_map,
        build_mechanistic_payload_from_text_map,
        dedupe_preserve_order,
        evidence_missing_fields,
        extract_extra_mechanistic_payload,
        list_to_textblock,
        mechanistic_payload_to_text_map,
        normalize_code,
        phase_objective_text,
        relation_is_challenging,
        relation_is_supporting,
        reverse_lookup,
        textblock_to_list,
        AlternativeModel,
        EvidenceEntry,
        GraphEdge,
        GraphNode,
        GovernanceGate,
        KnowledgeCard,
        LegacyRoadmapParser,
        Phase,
        RoadmapModel,
    )

UI_FONT_FAMILY = "Exo 2"
DISPLAY_FONT_FAMILY = "Russo One"

STATUS_COLORS = {
    "closed": QColor("#8f949b"),
    "current": QColor("#d7d1c7"),
    "next": QColor("#b89d6a"),
    "later": QColor("#6f7379"),
    "proposed": QColor("#7a4d53"),
}
NODE_TYPE_COLORS = {
    "phase": QColor("#1c2025"),
    "mechanism": QColor("#171d22"),
    "evidence": QColor("#20231f"),
    "validation_protocol": QColor("#231f1b"),
    "failure_mode": QColor("#261819"),
    "constraint": QColor("#191b1f"),
    "capability": QColor("#142126"),
    "biological_process": QColor("#221922"),
    "governance": QColor("#1f1a23"),
}
EDGE_LAYER_COLORS = {
    "causal": QColor("#7d848b"),
    "workflow": QColor("#b8bfc6"),
    "validation": QColor("#9e2f32"),
    "provenance": QColor("#9c8f73"),
}
EDGE_RELATION_COLORS = {
    "requires": QColor("#b8bfc6"),
    "modulates": QColor("#9fa5b0"),
    "gates": QColor("#d4a45c"),
    "invalidates": QColor("#cf5a5d"),
    "arbitrates": QColor("#73a8d9"),
    "observes_only": QColor("#7c8a9b"),
    "requests_revalidation": QColor("#a487d6"),
    "feedback_learns": QColor("#6ebc96"),
    "body_world_couples": QColor("#5aa8a0"),
    "overrides_survival": QColor("#e76f51"),
}


def edge_pen_for_relation_layer(relation: str, layer: str) -> QPen:
    token = (relation or "requires").strip()
    pen = QPen(
        EDGE_RELATION_COLORS.get(token, EDGE_LAYER_COLORS.get(layer, QColor("#7d848b"))),
        1.8,
    )
    if token in {"gates", "requests_revalidation"}:
        pen.setStyle(Qt.DashLine)
    elif token in {"observes_only", "modulates"}:
        pen.setStyle(Qt.DotLine)
    elif token in {"invalidates", "overrides_survival"}:
        pen.setStyle(Qt.SolidLine)
        pen.setWidthF(2.1)
    elif layer == "provenance":
        pen.setStyle(Qt.DotLine)
    return pen

APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #0b0d10;
    color: #d7d1c7;
    font-size: 13px;
}

QToolBar {
    background: #0f1317;
    border: none;
    border-bottom: 1px solid #2d333b;
    spacing: 4px;
    padding: 4px;
}

QStatusBar {
    background: #0f1317;
    color: #9aa2ac;
    border-top: 1px solid #2d333b;
}

QTabWidget::pane {
    border: 1px solid #2d333b;
    background: #11151a;
    margin-top: 4px;
}

QTabBar::tab {
    background: #0f1317;
    border: 1px solid #2d333b;
    padding: 8px 14px;
    margin-right: 2px;
    min-width: 120px;
}

QTabBar::tab:selected {
    background: #171c22;
    border-bottom: 1px solid #6f1418;
    color: #f0ebe3;
}

QLabel {
    color: #c9c3b8;
}

QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QTableWidget {
    background: #0f1317;
    color: #e6e0d5;
    border: 1px solid #353c45;
    border-radius: 0px;
    padding: 6px;
    selection-background-color: #6f1418;
    selection-color: #f5efe6;
}

QTableWidget {
    gridline-color: #252b33;
    alternate-background-color: #11161c;
}

QTableWidget::item {
    padding: 4px;
}

QHeaderView::section {
    background: #151a20;
    color: #b7b0a4;
    border: 0px;
    border-bottom: 1px solid #303741;
    border-right: 1px solid #232a31;
    padding: 7px;
    font-weight: 600;
}

QPushButton {
    background: #151a20;
    color: #ddd7cd;
    border: 1px solid #434a53;
    border-radius: 0px;
    padding: 8px 12px;
}

QPushButton:hover {
    background: #1c232b;
    border-color: #8a8f96;
}

QPushButton:pressed {
    background: #12171d;
}

QComboBox QAbstractItemView {
    background: #11151a;
    color: #e6e0d5;
    selection-background-color: #6f1418;
}

QSplitter::handle {
    background: #232a31;
}

QDockWidget {
    font-weight: 700;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QDockWidget::title {
    background: #11151a;
    text-align: left;
    padding: 6px 8px;
    border-bottom: 1px solid #2d333b;
}

QScrollBar:vertical {
    background: #0d1014;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #313840;
    min-height: 28px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
"""


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent: Optional[QWidget] = None) -> None:
        super().__init__(scene, parent)
        self._min_zoom = 0.18
        self._max_zoom = 3.0
        self._default_scene_rect = QRectF(-50000.0, -50000.0, 100000.0, 100000.0)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setBackgroundBrush(QColor("#090b0e"))
        self.setSceneRect(self._default_scene_rect)

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self._apply_zoom(factor)
            event.accept()
            return
        super().wheelEvent(event)

    def _apply_zoom(self, factor: float) -> None:
        current = self.transform().m11()
        if current <= 0:
            current = 1.0
        target = max(self._min_zoom, min(self._max_zoom, current * factor))
        scale_factor = target / current
        if abs(scale_factor - 1.0) < 1e-6:
            return
        self.scale(scale_factor, scale_factor)

    def reset_zoom(self) -> None:
        self.resetTransform()

    def fit_graph(self) -> None:
        rect = self.scene().itemsBoundingRect()
        if rect.isNull():
            return
        self.fitInView(rect.adjusted(-140.0, -140.0, 140.0, 140.0), Qt.KeepAspectRatio)
class EdgeLabelItem(QGraphicsSimpleTextItem):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        font = QFont(UI_FONT_FAMILY, 9)
        font.setBold(True)
        self.setFont(font)
        self.setBrush(QColor("#a9adb4"))
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setZValue(2)


class GraphEdgeItem(QGraphicsPathItem):
    def __init__(
        self,
        edge: GraphEdge,
        source_item: "GraphNodeItem",
        target_item: "GraphNodeItem",
        path_builder,
        route_meta: Optional[Dict[str, float | str]] = None,
        show_label: bool = False,
    ) -> None:
        super().__init__()
        self.edge = edge
        self.source_item = source_item
        self.target_item = target_item
        self.path_builder = path_builder
        self.route_meta = route_meta or {}
        self.label: Optional[EdgeLabelItem] = None

        pen = edge_pen_for_relation_layer(edge.relation, edge.layer)
        self.setPen(pen)
        self.setZValue(-1)

        if show_label:
            label_text = display_from_map(edge.relation, EDGE_RELATION_LABELS)
            if edge.note:
                label_text = f"{label_text} · {edge.note}"
            self.label = EdgeLabelItem(label_text, self)
        self.update_position()

    def _anchor_points(self) -> tuple[QPointF, QPointF]:
        s = self.source_item.sceneBoundingRect()
        t = self.target_item.sceneBoundingRect()
        source_side = str(self.route_meta.get("source_side", "right"))
        target_side = str(self.route_meta.get("target_side", "left"))
        start_y = s.center().y() + float(self.route_meta.get("start_dy", 0.0))
        end_y = t.center().y() + float(self.route_meta.get("end_dy", 0.0))
        start_x = s.right() if source_side == "right" else s.left()
        end_x = t.left() if target_side == "left" else t.right()
        return QPointF(start_x, start_y), QPointF(end_x, end_y)

    def update_position(self) -> None:
        start, end = self._anchor_points()
        path = self.path_builder(start, end, self.route_meta)
        self.setPath(path)
        if self.label is not None:
            mid = path.pointAtPercent(0.5)
            rect = self.label.boundingRect()
            self.label.setPos(mid.x() - rect.width() / 2, mid.y() - rect.height() - 8)
class GraphNodeItem(QGraphicsRectItem):
    def __init__(self, node: GraphNode, callback, save_position_callback) -> None:
        super().__init__(0, 0, node.width, max(node.height, 124.0))
        self.node = node
        self.callback = callback
        self.save_position_callback = save_position_callback
        self._edges: List[GraphEdgeItem] = []

        self.setBrush(NODE_TYPE_COLORS.get(node.node_type, QColor("#181c21")))
        self.setPen(QPen(QColor("#59616b"), 1.2))
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable
            | QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setPos(node.x, node.y)

        title = QGraphicsSimpleTextItem(node.label, self)
        title_font = QFont(DISPLAY_FONT_FAMILY, 10)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setBrush(QColor("#efe9de"))
        title.setPos(10, 8)

        meta_text = f"{display_from_map(node.node_type, NODE_TYPE_LABELS)} | {display_from_map(node.claim_state, CLAIM_STATE_LABELS)}"
        meta = QGraphicsSimpleTextItem(meta_text, self)
        meta_font = QFont(UI_FONT_FAMILY, 9)
        meta.setFont(meta_font)
        meta.setBrush(QColor("#a8b0b8"))
        meta.setPos(10, 32)

        layer = QGraphicsSimpleTextItem(
            f"{display_from_map(node.layer_hint, GRAPH_LAYER_LABELS)} | {display_from_map(node.maturity, MATURITY_LABELS)}",
            self,
        )
        layer.setFont(meta_font)
        layer.setBrush(QColor("#8f98a2"))
        layer.setPos(10, 54)

        node_code = QGraphicsSimpleTextItem(node.node_id, self)
        node_code.setFont(meta_font)
        node_code.setBrush(QColor("#777f89"))
        node_code.setPos(10, 76)

        summary = (node.summary or "").strip()
        if summary:
            clipped = summary[:68] + ("…" if len(summary) > 68 else "")
            summary_item = QGraphicsSimpleTextItem(clipped, self)
            summary_item.setFont(meta_font)
            summary_item.setBrush(QColor("#bec5cb"))
            summary_item.setPos(10, 94)

    def add_edge(self, edge_item: GraphEdgeItem) -> None:
        self._edges.append(edge_item)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self._edges:
                edge.update_position()
        return super().itemChange(change, value)

    def mousePressEvent(self, event) -> None:
        self.callback(self.node.node_id)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self.save_position_callback(self.node.node_id, self.pos())
class AddNodeDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Node Registration")
        layout = QFormLayout(self)
        self.label_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(list(NODE_TYPE_LABELS.values()))
        self.layer_combo = QComboBox()
        self.layer_combo.addItems(list(GRAPH_LAYER_LABELS.values()))
        self.summary_edit = QPlainTextEdit()
        self.summary_edit.setMinimumHeight(100)
        layout.addRow("Label", self.label_edit)
        layout.addRow("Node class", self.type_combo)
        layout.addRow("Layer", self.layer_combo)
        layout.addRow("Protocol summary", self.summary_edit)
        buttons = QHBoxLayout()
        ok_btn = QPushButton("Register")
        cancel_btn = QPushButton("Abort")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)


class AddEdgeDialog(QDialog):
    def __init__(self, node_ids: List[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Link Registration")
        layout = QFormLayout(self)
        self.source_combo = QComboBox()
        self.source_combo.addItems(node_ids)
        self.target_combo = QComboBox()
        self.target_combo.addItems(node_ids)
        self.relation_combo = QComboBox()
        self.relation_combo.addItems(list(EDGE_RELATION_LABELS.values()))
        self.layer_combo = QComboBox()
        self.layer_combo.addItems(list(GRAPH_LAYER_LABELS.values()))
        self.note_edit = QLineEdit()
        layout.addRow("Source", self.source_combo)
        layout.addRow("Target", self.target_combo)
        layout.addRow("Relation", self.relation_combo)
        layout.addRow("Layer", self.layer_combo)
        layout.addRow("Trace note", self.note_edit)
        buttons = QHBoxLayout()
        ok_btn = QPushButton("Register")
        cancel_btn = QPushButton("Abort")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)


class JsonViewerDialog(QDialog):
    def __init__(
        self,
        title: str,
        text: str,
        parent: Optional[QWidget] = None,
        *,
        apply_callback=None,
        context_title: str = "",
        context_text: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1040, 860)
        self.apply_callback = apply_callback

        layout = QVBoxLayout(self)
        if context_text:
            layout.addWidget(QLabel(context_title or "Attached context"))
            self.context_editor = QPlainTextEdit()
            self.context_editor.setReadOnly(True)
            self.context_editor.setPlainText(context_text)
            self.context_editor.setMinimumHeight(220)
            layout.addWidget(self.context_editor)
        else:
            self.context_editor = None

        layout.addWidget(QLabel("JSON payload"))
        self.editor = QPlainTextEdit()
        mono = QFont("Consolas", 10)
        mono.setStyleHint(QFont.Monospace)
        self.editor.setFont(mono)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.editor.setPlainText(text)
        layout.addWidget(self.editor, 1)

        buttons = QHBoxLayout()
        copy_btn = QPushButton("Copy JSON")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.editor.toPlainText()))
        buttons.addWidget(copy_btn)

        if self.context_editor is not None:
            copy_context_btn = QPushButton("Copy attached context")
            copy_context_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.context_editor.toPlainText()))
            buttons.addWidget(copy_context_btn)

        buttons.addStretch(1)

        if self.apply_callback is not None:
            apply_btn = QPushButton("Apply payload")
            apply_btn.clicked.connect(self._apply_changes)
            buttons.addWidget(apply_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _apply_changes(self) -> None:
        if self.apply_callback is None:
            return
        try:
            self.apply_callback(self.editor.toPlainText())
        except Exception as exc:
            QMessageBox.critical(self, "Payload apply failure", str(exc))
            return
        self.accept()
class GuidedEvidenceDialog(QDialog):
    def __init__(self, entry: EvidenceEntry, phase_choices: List[tuple[str, str]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Evidence Intake")
        self.resize(840, 920)
        self.phase_choices = phase_choices
        self._extra_mechanistic_payload = extract_extra_mechanistic_payload(entry.mechanistic_payload)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit(entry.title)
        self.kind_edit = QLineEdit(entry.kind)

        self.status_combo = QComboBox()
        self.status_combo.addItems(list(EVIDENCE_STATUS_LABELS.values()))
        self.status_combo.setCurrentText(display_from_map(entry.status, EVIDENCE_STATUS_LABELS))

        self.role_combo = QComboBox()
        self.role_combo.addItems(list(EVIDENCE_ROLE_LABELS.values()))
        self.role_combo.setCurrentText(display_from_map(entry.evidence_role, EVIDENCE_ROLE_LABELS))

        self.phase_combo = QComboBox()
        self.phase_combo.addItem("—", "")
        for code, title in phase_choices:
            self.phase_combo.addItem(f"{code} — {title}", code)

        if entry.phase_refs:
            first_code = entry.phase_refs[0].get("code", "")
            idx = self.phase_combo.findData(first_code)
            if idx >= 0:
                self.phase_combo.setCurrentIndex(idx)

        self.relation_combo = QComboBox()
        self.relation_combo.addItems(EVIDENCE_RELATION_OPTIONS)
        current_relation = entry.phase_refs[0].get("relation", "supports") if entry.phase_refs else "supports"
        idx = self.relation_combo.findText(current_relation)
        if idx >= 0:
            self.relation_combo.setCurrentIndex(idx)

        form.addRow("Title", self.title_edit)
        form.addRow("Kind", self.kind_edit)
        form.addRow("Status", self.status_combo)
        form.addRow("Role", self.role_combo)
        form.addRow("Phase", self.phase_combo)
        form.addRow("Relation", self.relation_combo)
        layout.addLayout(form)

        self.summary_edit = QPlainTextEdit(entry.summary)
        self.limitations_edit = QPlainTextEdit(list_to_textblock(entry.limitations))
        self.open_questions_edit = QPlainTextEdit(list_to_textblock(entry.open_questions))
        self.provenance_edit = QPlainTextEdit(entry.provenance)
        self.citation_edit = QLineEdit(entry.citation)
        self.url_edit = QLineEdit(entry.url)
        self.extra_payload_edit = QPlainTextEdit(json.dumps(self._extra_mechanistic_payload, ensure_ascii=False, indent=2))
        self.ready_check = QCheckBox("Mark record READY")
        self.ready_check.setChecked(entry.ready_for_use)

        layout.addWidget(QLabel("Summary"))
        layout.addWidget(self.summary_edit)

        self.mech_widgets: Dict[str, QWidget] = {}
        mech_text = mechanistic_payload_to_text_map(entry.mechanistic_payload)
        for key, label, kind in EVIDENCE_MECHANISTIC_FIELDS:
            widget: QWidget
            if kind == "single":
                line = QLineEdit(mech_text.get(key, ""))
                widget = line
            else:
                edit = QPlainTextEdit(mech_text.get(key, ""))
                widget = edit
            self.mech_widgets[key] = widget
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        for label, widget in [
            ("Limitations", self.limitations_edit),
            ("Open questions", self.open_questions_edit),
            ("Provenance", self.provenance_edit),
            ("Extra mechanism payload (JSON)", self.extra_payload_edit),
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        form2 = QFormLayout()
        form2.addRow("Citation", self.citation_edit)
        form2.addRow("URL", self.url_edit)
        layout.addLayout(form2)
        layout.addWidget(self.ready_check)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Apply intake")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Abort")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _read_extra_payload(self) -> Dict[str, Any]:
        raw = self.extra_payload_edit.toPlainText().strip()
        if not raw:
            return {}
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("Extra mechanistic payload must be a JSON object.")
        return payload

    def _collect_mechanistic_payload(self) -> Dict[str, Any]:
        text_map: Dict[str, str] = {}
        for key, _label, kind in EVIDENCE_MECHANISTIC_FIELDS:
            widget = self.mech_widgets[key]
            if kind == "single":
                text_map[key] = widget.text().strip()  # type: ignore[attr-defined]
            else:
                text_map[key] = widget.toPlainText().strip()  # type: ignore[attr-defined]
        return build_mechanistic_payload_from_text_map(text_map, self._read_extra_payload())

    def apply_to_entry(self, entry: EvidenceEntry) -> None:
        entry.title = self.title_edit.text().strip() or entry.title
        entry.kind = self.kind_edit.text().strip() or entry.kind
        entry.status = reverse_lookup(EVIDENCE_STATUS_LABELS, self.status_combo.currentText(), DEFAULT_EVIDENCE_STATUS)
        entry.evidence_role = reverse_lookup(EVIDENCE_ROLE_LABELS, self.role_combo.currentText(), DEFAULT_EVIDENCE_ROLE)
        entry.summary = self.summary_edit.toPlainText().strip()
        entry.mechanistic_payload = self._collect_mechanistic_payload()
        entry.limitations = textblock_to_list(self.limitations_edit.toPlainText())
        entry.open_questions = textblock_to_list(self.open_questions_edit.toPlainText())
        entry.provenance = self.provenance_edit.toPlainText().strip()
        entry.citation = self.citation_edit.text().strip()
        entry.url = self.url_edit.text().strip()
        entry.ready_for_use = self.ready_check.isChecked()

        phase_code = str(self.phase_combo.currentData() or "").strip()
        relation = self.relation_combo.currentText().strip() or "supports"
        if phase_code:
            phase_title = ""
            for code, title in self.phase_choices:
                if normalize_code(code) == normalize_code(phase_code):
                    phase_title = title
                    break
            entry.phase_refs = [{"code": phase_code, "title": phase_title, "relation": relation}]
            phase_node = f"phase::{normalize_code(phase_code)}"
            if relation_is_supporting(relation):
                if phase_node not in entry.supports:
                    entry.supports = [phase_node] + [x for x in entry.supports if x != phase_node]
                entry.challenges = [x for x in entry.challenges if x != phase_node]
            elif relation_is_challenging(relation):
                if phase_node not in entry.challenges:
                    entry.challenges = [phase_node] + [x for x in entry.challenges if x != phase_node]
                entry.supports = [x for x in entry.supports if x != phase_node]
        normalized = EvidenceEntry.from_dict(entry.to_dict())
        entry.__dict__.update(normalized.__dict__)


class PhaseWorkspaceDialog(QDialog):
    phase_applied = Signal(str)

    def __init__(self, model: RoadmapModel, apply_callback, initial_code: Optional[str] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.model = model
        self.apply_callback = apply_callback
        self.setWindowTitle("Phase Protocol Workspace")
        self.resize(1180, 860)

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Phase"))

        self.phase_combo = QComboBox()
        for phase in self.model.phases:
            self.phase_combo.addItem(f"{phase.code} — {phase.title}", phase.code)
        self.phase_combo.currentIndexChanged.connect(self._refresh_workspace_embedded_preview)
        top.addWidget(self.phase_combo, 1)

        self.load_json_btn = QPushButton("Load JSON")
        self.load_json_btn.clicked.connect(self.load_current_phase_json)
        top.addWidget(self.load_json_btn)

        self.load_todo_btn = QPushButton("Load TODO shell")
        self.load_todo_btn.clicked.connect(self.load_todo_template)
        top.addWidget(self.load_todo_btn)

        self.packet_btn = QPushButton("Context packet")
        self.packet_btn.clicked.connect(self.open_current_execution_packet)
        top.addWidget(self.packet_btn)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.editor.toPlainText()))
        top.addWidget(self.copy_btn)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_changes)
        top.addWidget(self.apply_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        top.addWidget(close_btn)
        layout.addLayout(top)

        info = QLabel("Phase payload is edited here as a full JSON document.")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addWidget(QLabel("Embedded augmentations"))
        self.workspace_embedded_preview = QPlainTextEdit()
        self.workspace_embedded_preview.setReadOnly(True)
        self.workspace_embedded_preview.setMinimumHeight(150)
        self.workspace_embedded_preview.setPlaceholderText("No embedded augmentations for current phase.")
        layout.addWidget(self.workspace_embedded_preview)

        self.editor = QPlainTextEdit()
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        mono = QFont("Consolas", 10)
        mono.setStyleHint(QFont.Monospace)
        self.editor.setFont(mono)
        layout.addWidget(self.editor, 1)

        if initial_code:
            self._set_phase_by_code(initial_code)
        self.load_current_phase_json()

    def _set_phase_by_code(self, code: str) -> None:
        target = normalize_code(code)
        for idx in range(self.phase_combo.count()):
            if normalize_code(str(self.phase_combo.itemData(idx))) == target:
                self.phase_combo.setCurrentIndex(idx)
                return

    def current_phase_code(self) -> Optional[str]:
        data = self.phase_combo.currentData()
        return str(data) if data else None

    def load_current_phase_json(self) -> None:
        code = self.current_phase_code()
        if code:
            self.editor.setPlainText(self.model.phase_to_json_text(code))
            self.workspace_embedded_preview.setPlainText(self.model.phase_embedded_blocks_summary_text(code))

    def _refresh_workspace_embedded_preview(self, *_args) -> None:
        code = self.current_phase_code()
        self.workspace_embedded_preview.setPlainText(self.model.phase_embedded_blocks_summary_text(code))

    def load_todo_template(self) -> None:
        code = self.current_phase_code()
        if code:
            self.editor.setPlainText(self.model.phase_to_todo_text(code))

    def open_current_execution_packet(self) -> None:
        code = self.current_phase_code()
        if not code:
            return
        JsonViewerDialog(
            f"Context assembler — {code}",
            self.model.phase_execution_packet_text(code),
            self,
            context_title="Assembly status",
            context_text=self.model.phase_execution_packet_summary_text(code),
        ).exec()

    def apply_changes(self) -> None:
        code = self.current_phase_code()
        if not code:
            return
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Empty payload", "Editor does not contain JSON.")
            return
        try:
            payload = json.loads(text)
            phase = self.apply_callback(code, payload)
        except Exception as exc:
            QMessageBox.critical(self, "Payload apply failure", f"{exc}")
            return
        self.phase_applied.emit(phase.code)
        QMessageBox.information(self, "Payload sealed", f"Phase {phase.code} updated.")


class MainWindow(QMainWindow):
    def __init__(self, initial_json: Optional[Path] = None) -> None:
        super().__init__()
        self.setWindowTitle("SUBJECT PROTOCOL STATION // Roadmap Monitor")
        self.resize(1720, 1000)
        self.setStyleSheet(APP_STYLESHEET)

        self.model = RoadmapModel()
        self.legacy_parser = LegacyRoadmapParser()
        self.state_path: Optional[Path] = None

        self.phase_display_order: List[int] = []
        self.current_phase_code: Optional[str] = None
        self.current_gate_code: Optional[str] = None
        self.current_node_id: Optional[str] = None
        self.current_evidence_id: Optional[str] = None

        self._build_actions()
        self._build_ui()
        self.statusBar().showMessage("STATION READY")

        if initial_json and initial_json.exists():
            self.load_state_from_path(initial_json)
        else:
            self.refresh_all_views()

    def _build_actions(self) -> None:
        toolbar = QToolBar("COMMAND", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        for title, callback in [
            ("Open archive JSON", self.pick_json),
            ("Import legacy DOCX", self.pick_docx),
            ("Seal state JSON", self.save_state),
            ("Export ledger CSV", self.export_csv),
            ("Resync views", self.refresh_all_views),
            ("Open phase workspace", self.open_phase_workspace),
            ("Open context assembler", self.open_current_phase_execution_packet),
        ]:
            action = QAction(title, self)
            action.triggered.connect(callback)
            toolbar.addAction(action)

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        header = QHBoxLayout()
        self.source_label = QLabel("ARCHIVE // not loaded")
        self.highest_claim_label = QLabel("CLAIM CEILING // —")
        self.highest_claim_label.setStyleSheet("font-weight: 700;")
        self.count_label = QLabel("NO ACTIVE DOSSIER")
        header.addWidget(self.highest_claim_label)
        header.addStretch(1)
        header.addWidget(self.count_label)
        header.addWidget(self.source_label)
        root_layout.addLayout(header)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs, 1)

        self.tab_phases = QWidget()
        self.tab_governance = QWidget()
        self.tab_graph = QWidget()
        self.tab_evidence = QWidget()
        self.tab_claim = QWidget()
        self.tab_summary = QWidget()

        self.tabs.addTab(self.tab_phases, "PHASE INDEX")
        self.tabs.addTab(self.tab_governance, "GATES")
        self.tabs.addTab(self.tab_graph, "SIGNAL MAP")
        self.tabs.addTab(self.tab_evidence, "EVIDENCE ARCHIVE")
        self.tabs.addTab(self.tab_claim, "CLAIM LADDER")
        self.tabs.addTab(self.tab_summary, "SYSTEM SUMMARY")

        self._build_phases_tab()
        self._build_governance_tab()
        self._build_graph_tab()
        self._build_evidence_tab()
        self._build_claim_tab()
        self._build_summary_tab()

        self.setCentralWidget(central)

        self.selection_dock = QDockWidget("OBSERVATION DOSSIER", self)
        self.selection_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.selection_text = QTextEdit()
        self.selection_text.setReadOnly(True)
        self.selection_dock.setWidget(self.selection_text)
        self.addDockWidget(Qt.RightDockWidgetArea, self.selection_dock)

    def _configure_table(self, table: QTableWidget) -> None:
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setWordWrap(False)
        table.setFocusPolicy(Qt.StrongFocus)
        table.setStyleSheet("QTableWidget { border: 1px solid #2d333b; }")

    def _build_phases_tab(self) -> None:
        layout = QVBoxLayout(self.tab_phases)

        filters = QHBoxLayout()
        self.phase_search = QLineEdit()
        self.phase_search.setPlaceholderText("Search by phase, directive, anomaly, evidence, forbidden shortcut…")
        self.phase_search.textChanged.connect(self.refresh_phase_table)
        self.phase_track_filter = QComboBox()
        self.phase_track_filter.addItems(["ALL", *TRACK_LABELS.values()])
        self.phase_track_filter.currentTextChanged.connect(self.refresh_phase_table)
        self.phase_status_filter = QComboBox()
        self.phase_status_filter.addItems(["ALL", *STATUS_LABELS.values()])
        self.phase_status_filter.currentTextChanged.connect(self.refresh_phase_table)
        self.phase_validation_filter = QComboBox()
        self.phase_validation_filter.addItems(["ALL", *VALIDATION_LABELS.values()])
        self.phase_validation_filter.currentTextChanged.connect(self.refresh_phase_table)
        self.phase_claim_role_filter = QComboBox()
        self.phase_claim_role_filter.addItems(["ALL", *CLAIM_ROLE_LABELS.values()])
        self.phase_claim_role_filter.currentTextChanged.connect(self.refresh_phase_table)
        self.phase_priority_filter = QComboBox()
        self.phase_priority_filter.addItems(["ALL", *PRIORITY_LABELS.values()])
        self.phase_priority_filter.currentTextChanged.connect(self.refresh_phase_table)

        for label, widget in [
            ("QUERY", self.phase_search),
            ("TRACK", self.phase_track_filter),
            ("STATE", self.phase_status_filter),
            ("VERIFY", self.phase_validation_filter),
            ("ROLE", self.phase_claim_role_filter),
            ("PRIORITY", self.phase_priority_filter),
        ]:
            filters.addWidget(QLabel(label))
            filters.addWidget(widget)
        layout.addLayout(filters)

        splitter = QSplitter()
        layout.addWidget(splitter, 1)

        self.phase_table = QTableWidget(0, 10)
        self.phase_table.setHorizontalHeaderLabels(
            [
                "CODE",
                "PHASE",
                "TRACK",
                "STATE",
                "VERIFY",
                "ROLE",
                "AUTHORITY",
                "COMPUTE",
                "CLAIM",
                "INTEGRITY",
            ]
        )
        self.phase_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.phase_table.setSelectionMode(QTableWidget.SingleSelection)
        self.phase_table.verticalHeader().setVisible(False)
        self.phase_table.itemSelectionChanged.connect(self.on_phase_selected)
        self._configure_table(self.phase_table)
        splitter.addWidget(self.phase_table)

        detail = QWidget()
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 6)
        detail_layout = QVBoxLayout(detail)

        self.phase_title_label = QLabel("SELECT PHASE")
        self.phase_title_label.setStyleSheet("font-size: 19px; font-weight: 700; color: #f0ebe3; letter-spacing: 1px;")
        self.phase_meta_label = QLabel("")
        self.phase_meta_label.setWordWrap(True)
        detail_layout.addWidget(self.phase_title_label)
        detail_layout.addWidget(self.phase_meta_label)

        top_form = QGridLayout()
        self.phase_status_combo = QComboBox()
        self.phase_status_combo.addItems(list(STATUS_LABELS.values()))
        self.phase_validation_combo = QComboBox()
        self.phase_validation_combo.addItems(list(VALIDATION_LABELS.values()))
        self.phase_claim_state_combo = QComboBox()
        self.phase_claim_state_combo.addItems(list(CLAIM_STATE_LABELS.values()))
        self.phase_maturity_combo = QComboBox()
        self.phase_maturity_combo.addItems(list(MATURITY_LABELS.values()))
        top_form.addWidget(QLabel("STATE"), 0, 0)
        top_form.addWidget(self.phase_status_combo, 0, 1)
        top_form.addWidget(QLabel("VERIFY"), 0, 2)
        top_form.addWidget(self.phase_validation_combo, 0, 3)
        top_form.addWidget(QLabel("CLAIM"), 1, 0)
        top_form.addWidget(self.phase_claim_state_combo, 1, 1)
        top_form.addWidget(QLabel("INTEGRITY"), 1, 2)
        top_form.addWidget(self.phase_maturity_combo, 1, 3)
        detail_layout.addLayout(top_form)

        self.phase_tabs = QTabWidget()
        detail_layout.addWidget(self.phase_tabs, 1)

        overview = QWidget()
        ov_layout = QVBoxLayout(overview)
        self.phase_description_edit = QPlainTextEdit()
        self.phase_notes_edit = QPlainTextEdit()
        ov_layout.addWidget(QLabel("DIRECTIVE"))
        ov_layout.addWidget(self.phase_description_edit, 1)
        ov_layout.addWidget(QLabel("FIELD NOTES"))
        ov_layout.addWidget(self.phase_notes_edit, 1)
        self.phase_tabs.addTab(overview, "DOSSIER")

        knowledge = QWidget()
        k_layout = QGridLayout(knowledge)
        self.k_functional_role = QPlainTextEdit()
        self.k_why_exists = QPlainTextEdit()
        self.k_inputs = QPlainTextEdit()
        self.k_outputs = QPlainTextEdit()
        self.k_authority = QPlainTextEdit()
        self.k_forbidden = QPlainTextEdit()
        self.k_uncertainty = QPlainTextEdit()
        self.k_observables = QPlainTextEdit()
        self.k_failure_modes = QPlainTextEdit()
        self.k_falsifiers = QPlainTextEdit()
        self.k_tests = QPlainTextEdit()
        self.k_bio_analogy = QPlainTextEdit()
        self.k_bio_support = QPlainTextEdit()
        self.k_evidence_strength = QLineEdit()
        self.k_provenance = QPlainTextEdit()
        self.k_disciplines = QPlainTextEdit()
        self.k_evidence_ids = QPlainTextEdit()
        self.k_alternatives = QPlainTextEdit()
        widgets = [
            ("Functional role", self.k_functional_role),
            ("Reason for existence", self.k_why_exists),
            ("Input surface", self.k_inputs),
            ("Output surface", self.k_outputs),
            ("Authority bounds", self.k_authority),
            ("Forbidden shortcuts", self.k_forbidden),
            ("Uncertainty policy", self.k_uncertainty),
            ("Observables", self.k_observables),
            ("Failure modes", self.k_failure_modes),
            ("Falsifiers", self.k_falsifiers),
            ("Verification tests", self.k_tests),
            ("Biological analogue", self.k_bio_analogy),
            ("Biological support", self.k_bio_support),
            ("Evidence strength", self.k_evidence_strength),
            ("Provenance note", self.k_provenance),
            ("Disciplines", self.k_disciplines),
            ("Archive record IDs", self.k_evidence_ids),
            ("Alternative models", self.k_alternatives),
        ]
        for row, (label, widget) in enumerate(widgets):
            k_layout.addWidget(QLabel(label), row, 0)
            k_layout.addWidget(widget, row, 1)
        self.phase_tabs.addTab(knowledge, "MECHANISM DOSSIER")

        buttons = QHBoxLayout()
        save_btn = QPushButton("Commit phase")
        save_btn.clicked.connect(self.save_phase_edits)
        reset_btn = QPushButton("Set LATENT")
        reset_btn.clicked.connect(self.reset_phase_status)
        workspace_btn = QPushButton("Open workspace")
        workspace_btn.clicked.connect(self.open_phase_workspace)
        assembler_btn = QPushButton("Context assembler")
        assembler_btn.clicked.connect(self.open_current_phase_execution_packet)
        add_ev_btn = QPushButton("+ Register evidence")
        add_ev_btn.clicked.connect(self.add_evidence_from_current_phase)
        pack_btn = QPushButton("Evidence pack")
        pack_btn.clicked.connect(self.export_current_phase_evidence_pack)
        json_btn = QPushButton("Evidence JSON")
        json_btn.clicked.connect(self.export_current_phase_evidence_json)

        for widget in [save_btn, reset_btn, workspace_btn, assembler_btn, add_ev_btn, pack_btn, json_btn]:
            buttons.addWidget(widget)
        buttons.addStretch(1)
        detail_layout.addLayout(buttons)

    def _build_governance_tab(self) -> None:
        layout = QVBoxLayout(self.tab_governance)
        splitter = QSplitter()
        layout.addWidget(splitter, 1)

        self.gate_table = QTableWidget(0, 5)
        self.gate_table.setHorizontalHeaderLabels(["CODE", "GATE", "STATE", "CLAIM", "INTEGRITY"])
        self.gate_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.gate_table.setSelectionMode(QTableWidget.SingleSelection)
        self.gate_table.verticalHeader().setVisible(False)
        self.gate_table.itemSelectionChanged.connect(self.on_gate_selected)
        self._configure_table(self.gate_table)
        splitter.addWidget(self.gate_table)

        detail = QWidget()
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        detail_layout = QVBoxLayout(detail)
        self.gate_title_label = QLabel("SELECT GATE")
        self.gate_title_label.setStyleSheet("font-size: 19px; font-weight: 700; color: #f0ebe3; letter-spacing: 1px;")
        detail_layout.addWidget(self.gate_title_label)

        form = QGridLayout()
        self.gate_status_combo = QComboBox()
        self.gate_status_combo.addItems(list(STATUS_LABELS.values()))
        self.gate_claim_state_combo = QComboBox()
        self.gate_claim_state_combo.addItems(list(CLAIM_STATE_LABELS.values()))
        self.gate_maturity_combo = QComboBox()
        self.gate_maturity_combo.addItems(list(MATURITY_LABELS.values()))
        form.addWidget(QLabel("STATE"), 0, 0)
        form.addWidget(self.gate_status_combo, 0, 1)
        form.addWidget(QLabel("CLAIM"), 1, 0)
        form.addWidget(self.gate_claim_state_combo, 1, 1)
        form.addWidget(QLabel("INTEGRITY"), 2, 0)
        form.addWidget(self.gate_maturity_combo, 2, 1)
        detail_layout.addLayout(form)

        self.gate_objective_edit = QPlainTextEdit()
        self.gate_rationale_edit = QPlainTextEdit()
        self.gate_notes_edit = QPlainTextEdit()
        detail_layout.addWidget(QLabel("DIRECTIVE"))
        detail_layout.addWidget(self.gate_objective_edit)
        detail_layout.addWidget(QLabel("RATIONALE"))
        detail_layout.addWidget(self.gate_rationale_edit)
        detail_layout.addWidget(QLabel("FIELD NOTES"))
        detail_layout.addWidget(self.gate_notes_edit)

        save_btn = QPushButton("Commit gate")
        save_btn.clicked.connect(self.save_gate_edits)
        detail_layout.addWidget(save_btn)

    def _build_graph_tab(self) -> None:
        layout = QVBoxLayout(self.tab_graph)
        controls = QHBoxLayout()
        self.graph_layer_filter = QComboBox()
        self.graph_layer_filter.addItems(["ALL", *GRAPH_LAYER_LABELS.values()])
        
        self.graph_type_filter = QComboBox()
        self.graph_type_filter.addItems(["ALL", *NODE_TYPE_LABELS.values()])
        
        self.graph_edge_labels_check = QCheckBox("Show relation tags")
        
        add_node_btn = QPushButton("Register node")
        add_node_btn.clicked.connect(self.add_graph_node)
        add_edge_btn = QPushButton("Register link")
        add_edge_btn.clicked.connect(self.add_graph_edge)
        relayout_btn = QPushButton("Relayout")
        relayout_btn.clicked.connect(self.relayout_graph)
        fit_btn = QPushButton("Fit view")
        
        reset_zoom_btn = QPushButton("100%")
        
        for label, widget in [("LAYER", self.graph_layer_filter), ("NODE CLASS", self.graph_type_filter)]:
            controls.addWidget(QLabel(label))
            controls.addWidget(widget)
        controls.addWidget(self.graph_edge_labels_check)
        controls.addWidget(add_node_btn)
        controls.addWidget(add_edge_btn)
        controls.addWidget(relayout_btn)
        controls.addWidget(fit_btn)
        controls.addWidget(reset_zoom_btn)
        controls.addStretch(1)
        layout.addLayout(controls)

        splitter = QSplitter()
        layout.addWidget(splitter, 1)
        self.graph_scene = QGraphicsScene(self)
        self.graph_view = ZoomableGraphicsView(self.graph_scene)

        self.graph_layer_filter.currentTextChanged.connect(self.refresh_graph_scene)
        self.graph_type_filter.currentTextChanged.connect(self.refresh_graph_scene)
        self.graph_edge_labels_check.toggled.connect(self.refresh_graph_scene)
        fit_btn.clicked.connect(self.graph_view.fit_graph)
        reset_zoom_btn.clicked.connect(self.graph_view.reset_zoom)

        splitter.addWidget(self.graph_view)

        right = QWidget()
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        right_layout = QVBoxLayout(right)
        self.graph_node_title = QLabel("SELECT NODE")
        self.graph_node_title.setStyleSheet("font-size: 19px; font-weight: 700; color: #f0ebe3; letter-spacing: 1px;")
        self.graph_node_meta = QLabel("")
        self.graph_node_meta.setWordWrap(True)
        self.graph_node_details = QTextEdit()
        self.graph_node_details.setReadOnly(True)
        jump_btn = QPushButton("Jump to linked phase")
        jump_btn.clicked.connect(self.jump_to_linked_phase)
        right_layout.addWidget(self.graph_node_title)
        right_layout.addWidget(self.graph_node_meta)
        right_layout.addWidget(self.graph_node_details, 1)
        right_layout.addWidget(jump_btn)

    def _build_evidence_tab(self) -> None:
        layout = QVBoxLayout(self.tab_evidence)

        buttons = QHBoxLayout()
        widgets = [
            ("Register evidence", self.add_evidence),
            ("From selected phase", self.add_evidence_from_current_phase),
            ("Guided intake", self.open_guided_evidence_fill),
            ("Open JSON", self.open_current_evidence_json),
            ("Export pack", self.export_current_phase_evidence_pack),
            ("Export phase JSON", self.export_current_phase_evidence_json),
            ("Commit evidence", self.save_evidence_edits),
            ("Delete evidence", self.remove_evidence),
        ]
        for title, callback in widgets:
            btn = QPushButton(title)
            btn.clicked.connect(callback)
            buttons.addWidget(btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        splitter = QSplitter()
        layout.addWidget(splitter, 1)

        self.evidence_table = QTableWidget(0, 6)
        self.evidence_table.setHorizontalHeaderLabels(["ID", "TITLE", "STATE", "ROLE", "KIND", "ATTACHED"])
        self.evidence_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.evidence_table.setSelectionMode(QTableWidget.SingleSelection)
        self.evidence_table.verticalHeader().setVisible(False)
        self.evidence_table.itemSelectionChanged.connect(self.on_evidence_selected)
        self._configure_table(self.evidence_table)
        splitter.addWidget(self.evidence_table)

        detail = QWidget()
        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        detail_layout = QVBoxLayout(detail)

        core_grid = QGridLayout()
        self.evidence_id_edit = QLineEdit()
        self.evidence_title_edit = QLineEdit()
        self.evidence_kind_edit = QLineEdit()
        self.evidence_status_combo = QComboBox()
        self.evidence_status_combo.addItems(list(EVIDENCE_STATUS_LABELS.values()))
        self.evidence_role_combo = QComboBox()
        self.evidence_role_combo.addItems(list(EVIDENCE_ROLE_LABELS.values()))
        self.evidence_strength_edit = QLineEdit()
        self.evidence_ready_check = QCheckBox("Record READY")

        core_grid.addWidget(QLabel("RECORD ID"), 0, 0)
        core_grid.addWidget(self.evidence_id_edit, 0, 1)
        core_grid.addWidget(QLabel("TITLE"), 1, 0)
        core_grid.addWidget(self.evidence_title_edit, 1, 1)
        core_grid.addWidget(QLabel("KIND"), 2, 0)
        core_grid.addWidget(self.evidence_kind_edit, 2, 1)
        core_grid.addWidget(QLabel("STATE"), 3, 0)
        core_grid.addWidget(self.evidence_status_combo, 3, 1)
        core_grid.addWidget(QLabel("ROLE"), 4, 0)
        core_grid.addWidget(self.evidence_role_combo, 4, 1)
        core_grid.addWidget(QLabel("STRENGTH"), 5, 0)
        core_grid.addWidget(self.evidence_strength_edit, 5, 1)
        core_grid.addWidget(self.evidence_ready_check, 6, 1)
        detail_layout.addLayout(core_grid)

        self.evidence_tabs = QTabWidget()
        detail_layout.addWidget(self.evidence_tabs, 1)

        tab_core = QWidget()
        core_layout = QGridLayout(tab_core)
        self.evidence_citation_edit = QLineEdit()
        self.evidence_url_edit = QLineEdit()
        self.evidence_summary_edit = QPlainTextEdit()
        self.evidence_provenance_edit = QPlainTextEdit()
        self.evidence_updated_edit = QLineEdit()
        for row, (label, widget) in enumerate([
            ("Citation", self.evidence_citation_edit),
            ("URL", self.evidence_url_edit),
            ("Summary", self.evidence_summary_edit),
            ("Provenance", self.evidence_provenance_edit),
            ("Updated at", self.evidence_updated_edit),
        ]):
            core_layout.addWidget(QLabel(label), row, 0)
            core_layout.addWidget(widget, row, 1)
        self.evidence_tabs.addTab(tab_core, "CORE RECORD")

        tab_mech = QWidget()
        mech_layout = QGridLayout(tab_mech)
        self.evidence_mech_editors: Dict[str, QWidget] = {}
        row = 0
        for key, label, kind in EVIDENCE_MECHANISTIC_FIELDS:
            widget: QWidget
            if kind == "single":
                widget = QLineEdit()
            else:
                widget = QPlainTextEdit()
            self.evidence_mech_editors[key] = widget
            mech_layout.addWidget(QLabel(label), row, 0)
            mech_layout.addWidget(widget, row, 1)
            row += 1
        self.evidence_mech_extra_edit = QPlainTextEdit()
        self.evidence_limitations_edit = QPlainTextEdit()
        self.evidence_open_questions_edit = QPlainTextEdit()
        for label, widget in [
            ("Extra mechanism payload (JSON)", self.evidence_mech_extra_edit),
            ("Limitations", self.evidence_limitations_edit),
            ("Open questions", self.evidence_open_questions_edit),
        ]:
            mech_layout.addWidget(QLabel(label), row, 0)
            mech_layout.addWidget(widget, row, 1)
            row += 1
        self.evidence_tabs.addTab(tab_mech, "MECHANISM")

        tab_links = QWidget()
        links_layout = QGridLayout(tab_links)
        self.evidence_phase_refs_edit = QPlainTextEdit()
        self.evidence_phase_refs_edit.setPlaceholderText("CODE | TITLE | RELATION")
        self.evidence_claim_refs_edit = QPlainTextEdit()
        self.evidence_gate_refs_edit = QPlainTextEdit()
        self.evidence_supports_edit = QPlainTextEdit()
        self.evidence_supports_edit.setPlaceholderText("phase::CODE or node_id, one per line")
        self.evidence_challenges_edit = QPlainTextEdit()
        self.evidence_challenges_edit.setPlaceholderText("phase::CODE or node_id, one per line")
        self.evidence_phase_context_edit = QPlainTextEdit()
        self.evidence_phase_context_edit.setReadOnly(True)
        self.evidence_phase_context_edit.setPlaceholderText("Attached phase context appears here")
        for row, (label, widget) in enumerate([
            ("Phase refs", self.evidence_phase_refs_edit),
            ("Claim refs", self.evidence_claim_refs_edit),
            ("Gate refs", self.evidence_gate_refs_edit),
            ("Supports", self.evidence_supports_edit),
            ("Challenges", self.evidence_challenges_edit),
            ("Phase context", self.evidence_phase_context_edit),
        ]):
            links_layout.addWidget(QLabel(label), row, 0)
            links_layout.addWidget(widget, row, 1)
        self.evidence_tabs.addTab(tab_links, "LINKS")

    def _build_claim_tab(self) -> None:
        layout = QVBoxLayout(self.tab_claim)
        self.claim_text = QTextEdit()
        self.claim_text.setReadOnly(True)
        layout.addWidget(self.claim_text)

    def _build_summary_tab(self) -> None:
        layout = QVBoxLayout(self.tab_summary)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)

    # ---------- Load / Save ----------
    def pick_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open archive JSON", str(Path.cwd()), "JSON (*.json)")
        if path:
            self.load_state_from_path(Path(path))

    def load_state_from_path(self, path: Path) -> None:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.model = RoadmapModel.from_json(raw)
        except Exception as exc:
            QMessageBox.critical(self, "Load failure", f"Could not load archive:\n{exc}")
            return
        self.state_path = path
        self.source_label.setText(f"ARCHIVE // JSON {path.name}")
        self.refresh_all_views(select_first=True)
        self.statusBar().showMessage(f"ARCHIVE LOADED // {path.name}")

    def pick_docx(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import legacy DOCX", str(Path.cwd()), "Word document (*.docx)")
        if not path:
            return
        try:
            phases = self.legacy_parser.parse_docx(Path(path))
        except Exception as exc:
            QMessageBox.critical(self, "Import failure", f"Could not import DOCX:\n{exc}")
            return
        imported = RoadmapModel()
        imported.meta = {
            "imported_from": "legacy_docx",
            "original_docx": str(path),
            "roadmap_mode": "legacy_import",
        }
        imported.phases = phases
        imported.ensure_graph_consistency()
        self.model = imported
        self.state_path = None
        self.source_label.setText(f"ARCHIVE // legacy DOCX {Path(path).name}")
        self.refresh_all_views(select_first=True)
        self.statusBar().showMessage(f"LEGACY IMPORT COMPLETE // {Path(path).name}")

    def save_state(self) -> None:
        if not self.model.phases and not self.model.governance_gates:
            QMessageBox.warning(self, "No archive", "Load a JSON archive or import a legacy DOCX first.")
            return
        initial = self.state_path.name if self.state_path else "roadmap_tracker_v4_state.json"
        path, _ = QFileDialog.getSaveFileName(self, "Seal state JSON", str(Path.cwd() / initial), "JSON (*.json)")
        if not path:
            return
        try:
            if self.state_path:
                self.model.meta["last_loaded_from"] = str(self.state_path)
            self.model.save(Path(path))
        except Exception as exc:
            QMessageBox.critical(self, "Save failure", f"Could not seal JSON:\n{exc}")
            return
        self.state_path = Path(path)
        self.source_label.setText(f"ARCHIVE // JSON {self.state_path.name}")
        self.statusBar().showMessage(f"ARCHIVE SEALED // {self.state_path.name}")

    def export_csv(self) -> None:
        if not self.model.phases and not self.model.governance_gates:
            QMessageBox.warning(self, "No archive", "Load a roadmap archive first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export ledger CSV", str(Path.cwd() / "roadmap_tracker_v4_export.csv"), "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow([
                    "kind", "code", "title", "track", "line", "after", "implemented_after", "conceptually_after",
                    "claim_blocked_by", "status", "status_source", "validation_state", "claim_role", "priority_bucket",
                    "risk_tags", "claim_state", "maturity", "authority_role", "computational_role",
                    "functional_role", "observables", "failure_modes",
                    "forbidden_shortcuts", "evidence_ids", "notes",
                ])
                for p in self.model.phases:
                    writer.writerow([
                        "phase", p.code, p.title, p.track, p.line, p.after or "", p.implemented_after or "",
                        " | ".join(p.conceptually_after), " | ".join(p.claim_blocked_by), p.status, p.status_source,
                        p.validation_state, p.claim_role, p.priority_bucket, " | ".join(p.risk_tags), p.claim_state,
                        p.maturity, p.authority_role, p.computational_role, p.knowledge_card.functional_role,
                        " | ".join(p.knowledge_card.observables), " | ".join(p.knowledge_card.failure_modes),
                        " | ".join(p.knowledge_card.forbidden_shortcuts), " | ".join(p.knowledge_card.evidence_ids), p.notes,
                    ])
                for g in self.model.governance_gates:
                    writer.writerow([
                        "governance_gate", g.code, g.title, "governance", "governance", "", "", "", "", g.status,
                        "user", "", "validation_gate", "governance", "", g.claim_state, g.maturity, "", "", g.objective,
                        "", "", "", g.notes,
                    ])
        except Exception as exc:
            QMessageBox.critical(self, "Export failure", f"Could not export CSV:\n{exc}")
            return
        self.statusBar().showMessage(f"LEDGER EXPORTED // {Path(path).name}")

    # ---------- Refresh ----------
    def refresh_all_views(self, select_first: bool = False) -> None:
        self._rebuild_phase_order_cache()
        self.refresh_phase_table(select_first=select_first)
        self.refresh_gate_table(select_first=select_first)
        self.refresh_graph_scene()
        self.refresh_evidence_table(select_first=select_first)
        self.refresh_claim_view()
        self.refresh_summary_view()
        self.highest_claim_label.setText(f"CLAIM CEILING // {self.compute_highest_admissible_claim()}")

    def _rebuild_phase_order_cache(self) -> None:
        if not self.model.phases:
            self.phase_display_order = []
            return

        code_to_index = {normalize_code(phase.code): idx for idx, phase in enumerate(self.model.phases)}
        children: Dict[str, List[str]] = defaultdict(list)
        indegree: Dict[str, int] = {normalize_code(phase.code): 0 for phase in self.model.phases}

        for phase in self.model.phases:
            code = normalize_code(phase.code)
            for dep in phase.dependency_codes():
                if dep in code_to_index and dep != code:
                    children[dep].append(code)
                    indegree[code] += 1

        priority_rank = {name: idx for idx, name in enumerate(PRIORITY_LABELS.keys())}
        track_rank = {"build": 0, "refinement": 1, "frontier": 2}

        ready = [code for code, degree in indegree.items() if degree == 0]
        ready.sort(key=lambda code: (
            priority_rank.get(self.model.phases[code_to_index[code]].priority_bucket, 999),
            track_rank.get(self.model.phases[code_to_index[code]].track, 999),
            code_to_index[code],
        ))

        order_codes: List[str] = []
        queue = deque(ready)
        while queue:
            code = queue.popleft()
            order_codes.append(code)
            new_ready: List[str] = []
            for child in children.get(code, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    new_ready.append(child)
            new_ready.sort(key=lambda c: (
                priority_rank.get(self.model.phases[code_to_index[c]].priority_bucket, 999),
                track_rank.get(self.model.phases[code_to_index[c]].track, 999),
                code_to_index[c],
            ))
            for item in new_ready:
                queue.append(item)

        if len(order_codes) != len(self.model.phases):
            seen = set(order_codes)
            for phase in self.model.phases:
                code = normalize_code(phase.code)
                if code not in seen:
                    order_codes.append(code)

        self.phase_display_order = [code_to_index[code] for code in order_codes]

    def refresh_phase_table(self, select_first: bool = False) -> None:
        query = self.phase_search.text().strip().lower()
        track_filter = self.phase_track_filter.currentText()
        status_filter = self.phase_status_filter.currentText()
        validation_filter = self.phase_validation_filter.currentText()
        claim_role_filter = self.phase_claim_role_filter.currentText()
        priority_filter = self.phase_priority_filter.currentText()

        self.phase_table.setRowCount(0)
        visible = 0
        for idx in self.phase_display_order:
            phase = self.model.phases[idx]
            if query and query not in phase.searchable_blob():
                continue
            if track_filter != "ALL" and phase.display_track != track_filter:
                continue
            if status_filter != "ALL" and phase.display_status != status_filter:
                continue
            if validation_filter != "ALL" and phase.display_validation_state != validation_filter:
                continue
            if claim_role_filter != "ALL" and phase.display_claim_role != claim_role_filter:
                continue
            if priority_filter != "ALL" and phase.display_priority_bucket != priority_filter:
                continue
            row = self.phase_table.rowCount()
            self.phase_table.insertRow(row)
            values = [
                phase.code, phase.title, phase.display_track, phase.display_status,
                phase.display_validation_state,
                phase.display_claim_role,
                phase.display_authority_role,
                phase.display_computational_role,
                phase.display_claim_state,
                phase.display_maturity,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.UserRole, phase.code)
                if phase.status in STATUS_COLORS:
                    item.setForeground(STATUS_COLORS[phase.status])
                self.phase_table.setItem(row, col, item)
            visible += 1
        self.phase_table.resizeColumnsToContents()
        counts = self.model.status_counts()
        status_summary = " | ".join(f"{STATUS_LABELS[key]} {counts.get(key, 0)}" for key in STATUS_LABELS)
        self.count_label.setText(f"PHASE INDEX {visible}/{len(self.model.phases)} // {status_summary}")
        if select_first and self.phase_table.rowCount() > 0:
            self.phase_table.selectRow(0)

    def refresh_gate_table(self, select_first: bool = False) -> None:
        self.gate_table.setRowCount(0)
        for gate in self.model.governance_gates:
            row = self.gate_table.rowCount()
            self.gate_table.insertRow(row)
            values = [gate.code, gate.title, gate.display_status, display_from_map(gate.claim_state, CLAIM_STATE_LABELS), display_from_map(gate.maturity, MATURITY_LABELS)]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.UserRole, gate.code)
                if gate.status in STATUS_COLORS:
                    item.setForeground(STATUS_COLORS[gate.status])
                self.gate_table.setItem(row, col, item)
        self.gate_table.resizeColumnsToContents()
        if select_first and self.gate_table.rowCount() > 0:
            self.gate_table.selectRow(0)

    def refresh_graph_scene(self) -> None:
        self.graph_scene.clear()
        selected_layer = reverse_lookup(GRAPH_LAYER_LABELS, self.graph_layer_filter.currentText(), "all") if self.graph_layer_filter.currentText() != "ALL" else "all"
        selected_type = reverse_lookup(NODE_TYPE_LABELS, self.graph_type_filter.currentText(), "all") if self.graph_type_filter.currentText() != "ALL" else "all"

        nodes = self.model.graph_nodes_for_layer(selected_layer)
        if selected_type != "all":
            nodes = [node for node in nodes if node.node_type == selected_type]

        node_ids = {node.node_id for node in nodes}
        edges = [edge for edge in self.model.graph_edges_for_layer(selected_layer) if edge.source in node_ids and edge.target in node_ids]

        items_by_id: Dict[str, GraphNodeItem] = {}
        for node in nodes:
            item = GraphNodeItem(node, self.select_node_by_id, self._save_node_position)
            self.graph_scene.addItem(item)
            items_by_id[node.node_id] = item

        route_meta = self._build_edge_route_meta(edges)
        show_labels = self.graph_edge_labels_check.isChecked()
        for idx, edge in enumerate(edges):
            source_item = items_by_id.get(edge.source)
            target_item = items_by_id.get(edge.target)
            if not source_item or not target_item:
                continue
            edge_item = GraphEdgeItem(
                edge,
                source_item,
                target_item,
                self._make_routed_path,
                route_meta=route_meta[idx],
                show_label=show_labels,
            )
            self.graph_scene.addItem(edge_item)
            source_item.add_edge(edge_item)
            target_item.add_edge(edge_item)

        items_rect = self.graph_scene.itemsBoundingRect()
        if items_rect.isNull():
            items_rect = QRectF(-2000.0, -2000.0, 4000.0, 4000.0)
        padded = items_rect.adjusted(-2400.0, -2400.0, 2400.0, 2400.0)
        world = QRectF(-50000.0, -50000.0, 100000.0, 100000.0)
        self.graph_scene.setSceneRect(world.united(padded))

    def refresh_evidence_table(self, select_first: bool = False) -> None:
        self.evidence_table.setRowCount(0)
        for entry in self.model.evidence_entries:
            row = self.evidence_table.rowCount()
            self.evidence_table.insertRow(row)
            values = [
                entry.evidence_id,
                entry.title,
                display_from_map(entry.status, EVIDENCE_STATUS_LABELS),
                display_from_map(entry.evidence_role, EVIDENCE_ROLE_LABELS),
                entry.kind,
                entry.attached_summary(),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.UserRole, entry.evidence_id)
                self.evidence_table.setItem(row, col, item)
        self.evidence_table.resizeColumnsToContents()
        if select_first and self.evidence_table.rowCount() > 0:
            self.evidence_table.selectRow(0)

    def refresh_claim_view(self) -> None:
        lines: List[str] = []
        if self.model.meta:
            lines.append("ARCHIVE META")
            for key, value in self.model.meta.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
        if self.model.claim_ladder:
            lines.append("CLAIM LADDER")
            lines.append("")
            for level in self.model.claim_ladder:
                lines.append(f"{level.level} — {level.name}")
                lines.append(f"Allowed claim: {level.allowed_claim}")
                if level.requires:
                    lines.append(f"Требует: {', '.join(level.requires)}")
                if level.forbidden_shortcuts:
                    lines.append("Forbidden shortcuts:")
                    for item in level.forbidden_shortcuts:
                        lines.append(f"- {item}")
                missing = self._claim_level_missing(level)
                lines.append(f"Open blockers: {', '.join(missing) if missing else 'none'}")
                lines.append("")
        self.claim_text.setPlainText("\n".join(lines).strip() or "No claim ladder data.")

    def refresh_summary_view(self) -> None:
        metrics = self.model.archive_metrics()
        lines: List[str] = []
        lines.append(f"CLAIM CEILING: {self.compute_highest_admissible_claim()}")
        lines.append("")
        lines.append("STATION METRICS")
        lines.append(f"- Phases: {metrics['phases']}")
        lines.append(f"- Gates: {metrics['gates']}")
        lines.append(f"- Evidence records: {metrics['evidence']}")
        lines.append(f"- READY evidence: {metrics['ready_evidence']}")
        lines.append(f"- Graph nodes: {metrics['nodes']}")
        lines.append(f"- Graph edges: {metrics['edges']}")
        lines.append("")
        if self.model.strategic_answers:
            lines.append("STRATEGIC ANSWERS")
            for key, value in self.model.strategic_answers.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
        phase_without_observables = [p.code for p in self.model.phases if not p.knowledge_card.observables]
        phase_without_falsifiers = [p.code for p in self.model.phases if not p.knowledge_card.falsifiers]
        lines.append("KNOWLEDGE COVERAGE")
        lines.append(f"- Phases without observables: {len(phase_without_observables)}")
        lines.append(f"- Phases without falsifiers: {len(phase_without_falsifiers)}")
        lines.append("")
        strong_blockers = self._strong_claim_blockers()
        lines.append("STRONG-CLAIM BLOCKERS")
        if strong_blockers:
            for blocker in strong_blockers:
                lines.append(f"- {blocker}")
        else:
            lines.append("- No open blockers")
        self.summary_text.setPlainText("\n".join(lines).strip())

    # ---------- Selection ----------
    def on_phase_selected(self) -> None:
        items = self.phase_table.selectedItems()
        if not items:
            return
        code = items[0].data(Qt.UserRole)
        phase = self.model.get_phase(code)
        if not phase:
            return
        self.current_phase_code = phase.code
        self.phase_title_label.setText(phase.protocol_label)
        self.phase_meta_label.setText("\n".join([
            *phase.protocol_vector(),
            f"AFTER    {phase.after or '—'}",
            f"HISTORY  {phase.implemented_after or '—'}",
            f"CHAIN    {', '.join(phase.conceptually_after) if phase.conceptually_after else '—'}",
            f"BLOCKERS {', '.join(phase.claim_blocked_by) if phase.claim_blocked_by else '—'}",
            f"PRIORITY {phase.display_priority_bucket}",
            f"RISK     {', '.join(phase.risk_tags) if phase.risk_tags else '—'}",
        ]))
        self.phase_status_combo.setCurrentText(phase.display_status)
        self.phase_validation_combo.setCurrentText(phase.display_validation_state)
        self.phase_claim_state_combo.setCurrentText(phase.display_claim_state)
        self.phase_maturity_combo.setCurrentText(phase.display_maturity)
        self.phase_description_edit.setPlainText(phase_objective_text(phase))
        self.phase_notes_edit.setPlainText(phase.notes)
        self._populate_knowledge_editors(phase.knowledge_card)
        self._update_selection_inspector(self._render_phase_inspector(phase))

    def on_gate_selected(self) -> None:
        items = self.gate_table.selectedItems()
        if not items:
            return
        code = items[0].data(Qt.UserRole)
        gate = next((g for g in self.model.governance_gates if g.code == code), None)
        if not gate:
            return
        self.current_gate_code = gate.code
        self.gate_title_label.setText(gate.protocol_label)
        self.gate_status_combo.setCurrentText(gate.display_status)
        self.gate_claim_state_combo.setCurrentText(display_from_map(gate.claim_state, CLAIM_STATE_LABELS))
        self.gate_maturity_combo.setCurrentText(display_from_map(gate.maturity, MATURITY_LABELS))
        self.gate_objective_edit.setPlainText(gate.objective)
        self.gate_rationale_edit.setPlainText(gate.rationale)
        self.gate_notes_edit.setPlainText(gate.notes)
        self._update_selection_inspector(
            f"{gate.protocol_label}\n\nSTATE: {gate.display_status}\nCLAIM: {display_from_map(gate.claim_state, CLAIM_STATE_LABELS)}\nINTEGRITY: {display_from_map(gate.maturity, MATURITY_LABELS)}\n\nDIRECTIVE:\n{gate.objective or '—'}\n\nRATIONALE:\n{gate.rationale or '—'}"
        )

    def select_node_by_id(self, node_id: str) -> None:
        node = self.model.get_node(node_id)
        if not node:
            return
        self.current_node_id = node.node_id
        self.graph_node_title.setText(node.protocol_label)
        self.graph_node_meta.setText(
            f"NODE CLASS: {display_from_map(node.node_type, NODE_TYPE_LABELS)}\n"
            f"LAYER: {display_from_map(node.layer_hint, GRAPH_LAYER_LABELS)}\n"
            f"CLAIM: {display_from_map(node.claim_state, CLAIM_STATE_LABELS)}\n"
            f"INTEGRITY: {display_from_map(node.maturity, MATURITY_LABELS)}\n"
            f"PHASE LINK: {node.phase_code or '—'}"
        )
        lines = [node.summary or "—", ""]
        if node.knowledge_card.functional_role:
            lines.append("Functional role:")
            lines.append(node.knowledge_card.functional_role)
            lines.append("")
        if node.knowledge_card.observables:
            lines.append("Observables:")
            lines.extend(f"- {item}" for item in node.knowledge_card.observables)
            lines.append("")
        if node.knowledge_card.failure_modes:
            lines.append("Failure modes:")
            lines.extend(f"- {item}" for item in node.knowledge_card.failure_modes)
            lines.append("")
        if node.knowledge_card.forbidden_shortcuts:
            lines.append("Forbidden shortcuts:")
            lines.extend(f"- {item}" for item in node.knowledge_card.forbidden_shortcuts)
            lines.append("")
        if node.notes:
            lines.append("Field notes:")
            lines.append(node.notes)
            lines.append("")
        outgoing = [
            edge for edge in self.model.graph_edges
            if edge.source == node.node_id
        ]
        incoming = [
            edge for edge in self.model.graph_edges
            if edge.target == node.node_id
        ]
        if outgoing:
            lines.append("Outgoing links:")
            for edge in outgoing:
                relation_label = display_from_map(edge.relation, EDGE_RELATION_LABELS)
                lines.append(f"- [{relation_label}] {edge.target} ({edge.layer})")
            lines.append("")
        if incoming:
            lines.append("Incoming links:")
            for edge in incoming:
                relation_label = display_from_map(edge.relation, EDGE_RELATION_LABELS)
                lines.append(f"- {edge.source} [{relation_label}] ({edge.layer})")
        self.graph_node_details.setPlainText("\n".join(lines).strip())
        self._update_selection_inspector(self.graph_node_details.toPlainText())

    def on_evidence_selected(self) -> None:
        items = self.evidence_table.selectedItems()
        if not items:
            return
        evidence_id = items[0].data(Qt.UserRole)
        entry = self.model.get_evidence(evidence_id)
        if not entry:
            return
        self.current_evidence_id = entry.evidence_id
        self.populate_evidence_editors(entry)

    def _set_mechanistic_ui_payload(self, payload: Dict[str, Any]) -> None:
        text_map = mechanistic_payload_to_text_map(payload)
        for key, _label, kind in EVIDENCE_MECHANISTIC_FIELDS:
            widget = self.evidence_mech_editors[key]
            if kind == "single":
                widget.setText(text_map.get(key, ""))  # type: ignore[attr-defined]
            else:
                widget.setPlainText(text_map.get(key, ""))  # type: ignore[attr-defined]
        extra_payload = extract_extra_mechanistic_payload(payload)
        self.evidence_mech_extra_edit.setPlainText(json.dumps(extra_payload, ensure_ascii=False, indent=2))

    def _read_mechanistic_ui_payload(self) -> Dict[str, Any]:
        text_map: Dict[str, str] = {}
        for key, _label, kind in EVIDENCE_MECHANISTIC_FIELDS:
            widget = self.evidence_mech_editors[key]
            if kind == "single":
                text_map[key] = widget.text().strip()  # type: ignore[attr-defined]
            else:
                text_map[key] = widget.toPlainText().strip()  # type: ignore[attr-defined]
        raw_extra = self.evidence_mech_extra_edit.toPlainText().strip()
        extra_payload: Dict[str, Any] = {}
        if raw_extra:
            parsed = json.loads(raw_extra)
            if not isinstance(parsed, dict):
                raise ValueError("Extra mechanism payload must be a JSON object.")
            extra_payload = parsed
        return build_mechanistic_payload_from_text_map(text_map, extra_payload)

    def populate_evidence_editors(self, entry: EvidenceEntry) -> None:
        self.evidence_id_edit.setText(entry.evidence_id)
        self.evidence_title_edit.setText(entry.title)
        self.evidence_kind_edit.setText(entry.kind)
        self.evidence_status_combo.setCurrentText(display_from_map(entry.status, EVIDENCE_STATUS_LABELS))
        self.evidence_role_combo.setCurrentText(display_from_map(entry.evidence_role, EVIDENCE_ROLE_LABELS))
        self.evidence_strength_edit.setText(entry.evidence_strength)
        self.evidence_ready_check.setChecked(entry.ready_for_use)
        self.evidence_citation_edit.setText(entry.citation)
        self.evidence_url_edit.setText(entry.url)
        self.evidence_summary_edit.setPlainText(entry.summary)
        self.evidence_provenance_edit.setPlainText(entry.provenance)
        self.evidence_updated_edit.setText(entry.updated_at)
        self._set_mechanistic_ui_payload(entry.mechanistic_payload)
        self.evidence_limitations_edit.setPlainText(list_to_textblock(entry.limitations))
        self.evidence_open_questions_edit.setPlainText(list_to_textblock(entry.open_questions))
        phase_lines = [f"{ref.get('code', '')} | {ref.get('title', '')} | {ref.get('relation', '')}" for ref in entry.phase_refs]
        self.evidence_phase_refs_edit.setPlainText("\n".join(phase_lines))
        self.evidence_claim_refs_edit.setPlainText(list_to_textblock(entry.claim_refs))
        self.evidence_gate_refs_edit.setPlainText(list_to_textblock(entry.gate_refs))
        self.evidence_supports_edit.setPlainText(list_to_textblock(entry.supports))
        self.evidence_challenges_edit.setPlainText(list_to_textblock(entry.challenges))
        self.evidence_phase_context_edit.setPlainText(self.model.attached_phase_context_text(entry))

        mech_text = mechanistic_payload_to_text_map(entry.mechanistic_payload)
        missing = entry.readiness_missing_fields
        missing_text = ", ".join(missing) if missing else "—"
        self._update_selection_inspector(
            f"{entry.protocol_label}\n"
            f"STATE: {display_from_map(entry.status, EVIDENCE_STATUS_LABELS)}\n"
            f"ROLE: {display_from_map(entry.evidence_role, EVIDENCE_ROLE_LABELS)}\n"
            f"KIND: {entry.kind}\n"
            f"READINESS: {entry.readiness_label}\n"
            f"DECLARED READY: {'YES' if entry.ready_for_use else 'NO'}\n"
            f"MISSING: {missing_text}\n"
            f"ATTACHED: {entry.attached_summary()}\n\n"
            f"SUMMARY:\n{entry.summary or '—'}\n\n"
            f"CORE MECHANISM:\n{mech_text.get('core_mechanism', '—') or '—'}\n\n"
            f"OBSERVED EFFECT:\n{mech_text.get('observed_effect', '—') or '—'}\n\n"
            f"SUPPORTS: {', '.join(entry.supports) or '—'}\n"
            f"CHALLENGES: {', '.join(entry.challenges) or '—'}"
        )

    # ---------- Editing ----------
    def _populate_knowledge_editors(self, card: KnowledgeCard) -> None:
        self.k_functional_role.setPlainText(card.functional_role)
        self.k_why_exists.setPlainText(card.why_exists)
        self.k_inputs.setPlainText(list_to_textblock(card.inputs))
        self.k_outputs.setPlainText(list_to_textblock(card.outputs))
        self.k_authority.setPlainText(card.authority)
        self.k_forbidden.setPlainText(list_to_textblock(card.forbidden_shortcuts))
        self.k_uncertainty.setPlainText(card.uncertainty_policy)
        self.k_observables.setPlainText(list_to_textblock(card.observables))
        self.k_failure_modes.setPlainText(list_to_textblock(card.failure_modes))
        self.k_falsifiers.setPlainText(list_to_textblock(card.falsifiers))
        self.k_tests.setPlainText(list_to_textblock(card.tests))
        self.k_bio_analogy.setPlainText(card.biological_analogy)
        self.k_bio_support.setPlainText(card.biological_support)
        self.k_evidence_strength.setText(card.evidence_strength)
        self.k_provenance.setPlainText(card.provenance_note)
        self.k_disciplines.setPlainText(list_to_textblock(card.disciplines))
        self.k_evidence_ids.setPlainText(list_to_textblock(card.evidence_ids))
        self.k_alternatives.setPlainText("\n".join(f"{alt.title} | {alt.summary} | {alt.why_not_adopted}" for alt in card.alternative_models))

    def _read_knowledge_editors(self) -> KnowledgeCard:
        alternatives: List[AlternativeModel] = []
        for line in self.k_alternatives.toPlainText().splitlines():
            parts = [part.strip() for part in line.split("|")]
            if not any(parts):
                continue
            while len(parts) < 3:
                parts.append("")
            alternatives.append(AlternativeModel(parts[0], parts[1], parts[2]))
        return KnowledgeCard(
            functional_role=self.k_functional_role.toPlainText().strip(),
            why_exists=self.k_why_exists.toPlainText().strip(),
            inputs=textblock_to_list(self.k_inputs.toPlainText()),
            outputs=textblock_to_list(self.k_outputs.toPlainText()),
            authority=self.k_authority.toPlainText().strip(),
            forbidden_shortcuts=textblock_to_list(self.k_forbidden.toPlainText()),
            uncertainty_policy=self.k_uncertainty.toPlainText().strip(),
            observables=textblock_to_list(self.k_observables.toPlainText()),
            failure_modes=textblock_to_list(self.k_failure_modes.toPlainText()),
            falsifiers=textblock_to_list(self.k_falsifiers.toPlainText()),
            tests=textblock_to_list(self.k_tests.toPlainText()),
            biological_analogy=self.k_bio_analogy.toPlainText().strip(),
            biological_support=self.k_bio_support.toPlainText().strip(),
            evidence_strength=self.k_evidence_strength.text().strip(),
            provenance_note=self.k_provenance.toPlainText().strip(),
            disciplines=textblock_to_list(self.k_disciplines.toPlainText()),
            alternative_models=alternatives,
            evidence_ids=textblock_to_list(self.k_evidence_ids.toPlainText()),
        )

    def save_phase_edits(self) -> None:
        if not self.current_phase_code:
            return
        phase = self.model.get_phase(self.current_phase_code)
        if not phase:
            return
        phase.status = reverse_lookup(STATUS_LABELS, self.phase_status_combo.currentText(), DEFAULT_STATUS)
        phase.status_source = "user"
        phase.validation_state = reverse_lookup(VALIDATION_LABELS, self.phase_validation_combo.currentText(), phase.validation_state)
        phase.claim_state = reverse_lookup(CLAIM_STATE_LABELS, self.phase_claim_state_combo.currentText(), DEFAULT_CLAIM_STATE)
        phase.maturity = reverse_lookup(MATURITY_LABELS, self.phase_maturity_combo.currentText(), DEFAULT_MATURITY)
        phase.notes = self.phase_notes_edit.toPlainText().strip()
        phase.knowledge_card = self._read_knowledge_editors()
        phase.spec["objective"] = self.phase_description_edit.toPlainText().strip()
        self._sync_phase_node(phase)
        self.refresh_all_views()
        self._reselect_phase_row(phase.code)
        self.statusBar().showMessage(f"PHASE COMMITTED // {phase.code}")

    def _sync_phase_node(self, phase: Phase) -> None:
        node = self.model.get_node(f"phase::{normalize_code(phase.code)}")
        if node:
            node.label = f"{phase.code}. {phase.title}"
            node.summary = (phase.spec or {}).get("objective", "")
            node.claim_state = phase.claim_state
            node.maturity = phase.maturity
            node.knowledge_card = phase.knowledge_card
            node.notes = phase.notes

    def reset_phase_status(self) -> None:
        if not self.current_phase_code:
            return
        phase = self.model.get_phase(self.current_phase_code)
        if phase:
            phase.status = DEFAULT_STATUS
            phase.status_source = "user"
            self.refresh_all_views()
            self._reselect_phase_row(phase.code)

    def save_gate_edits(self) -> None:
        if not self.current_gate_code:
            return
        gate = next((g for g in self.model.governance_gates if g.code == self.current_gate_code), None)
        if not gate:
            return
        gate.status = reverse_lookup(STATUS_LABELS, self.gate_status_combo.currentText(), DEFAULT_STATUS)
        gate.claim_state = reverse_lookup(CLAIM_STATE_LABELS, self.gate_claim_state_combo.currentText(), DEFAULT_CLAIM_STATE)
        gate.maturity = reverse_lookup(MATURITY_LABELS, self.gate_maturity_combo.currentText(), DEFAULT_MATURITY)
        gate.objective = self.gate_objective_edit.toPlainText().strip()
        gate.rationale = self.gate_rationale_edit.toPlainText().strip()
        gate.notes = self.gate_notes_edit.toPlainText().strip()
        self.refresh_all_views()
        self._reselect_gate_row(gate.code)
        self.statusBar().showMessage(f"GATE COMMITTED // {gate.code}")

    def add_graph_node(self) -> None:
        dialog = AddNodeDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        label = dialog.label_edit.text().strip()
        if not label:
            QMessageBox.warning(self, "Empty label", "Node label is required.")
            return
        base = "custom::" + "_".join(label.lower().split())
        node_id = base
        suffix = 2
        existing = {node.node_id for node in self.model.graph_nodes}
        while node_id in existing:
            node_id = f"{base}_{suffix}"
            suffix += 1
        node_type = reverse_lookup(NODE_TYPE_LABELS, dialog.type_combo.currentText(), "mechanism")
        layer = reverse_lookup(GRAPH_LAYER_LABELS, dialog.layer_combo.currentText(), "causal")
        node = GraphNode(node_id=node_id, label=label, node_type=node_type, layer_hint=layer, summary=dialog.summary_edit.toPlainText().strip(), x=80.0, y=80.0)
        self.model.graph_nodes.append(node)
        self.refresh_graph_scene()
        self.statusBar().showMessage(f"NODE REGISTERED // {node_id}")

    def add_graph_edge(self) -> None:
        if len(self.model.graph_nodes) < 2:
            QMessageBox.warning(self, "Insufficient nodes", "At least two nodes are required.")
            return
        dialog = AddEdgeDialog([node.node_id for node in self.model.graph_nodes], self)
        if dialog.exec() != QDialog.Accepted:
            return
        source = dialog.source_combo.currentText()
        target = dialog.target_combo.currentText()
        if source == target:
            QMessageBox.warning(self, "Invalid link", "Source and target must differ.")
            return
        relation = reverse_lookup(EDGE_RELATION_LABELS, dialog.relation_combo.currentText(), "requires")
        layer = reverse_lookup(GRAPH_LAYER_LABELS, dialog.layer_combo.currentText(), "causal")
        self.model.graph_edges.append(GraphEdge(source=source, target=target, relation=relation, layer=layer, note=dialog.note_edit.text().strip()))
        self.refresh_graph_scene()
        self.statusBar().showMessage(f"LINK REGISTERED // {source} -> {target}")

    def relayout_graph(self) -> None:
        layer = reverse_lookup(GRAPH_LAYER_LABELS, self.graph_layer_filter.currentText(), "all") if self.graph_layer_filter.currentText() != "Все" else "all"
        self.model.apply_graph_layout(layer)
        self.refresh_graph_scene()
        self.graph_view.fit_graph()
        self.statusBar().showMessage("SIGNAL MAP RELAID")

    def jump_to_linked_phase(self) -> None:
        if not self.current_node_id:
            return
        node = self.model.get_node(self.current_node_id)
        if not node or not node.phase_code:
            QMessageBox.information(self, "No phase link", "Selected node does not point to a phase.")
            return
        self.tabs.setCurrentWidget(self.tab_phases)
        self._reselect_phase_row(node.phase_code)

    # ---------- Evidence ----------
    def add_evidence(self) -> None:
        entry = self.model.create_blank_evidence()
        self.model.evidence_entries.append(entry)
        self.refresh_evidence_table()
        self._reselect_evidence_row(entry.evidence_id)

    def add_evidence_from_current_phase(self) -> None:
        if not self.current_phase_code:
            QMessageBox.information(self, "No phase selected", "Select a phase first.")
            return
        phase = self.model.get_phase(self.current_phase_code)
        if not phase:
            return
        entry = self.model.create_blank_evidence(phase=phase)
        self.model.evidence_entries.append(entry)
        if entry.evidence_id not in phase.knowledge_card.evidence_ids:
            phase.knowledge_card.evidence_ids.append(entry.evidence_id)
        self.refresh_all_views()
        self.tabs.setCurrentWidget(self.tab_evidence)
        self._reselect_evidence_row(entry.evidence_id)

    def open_guided_evidence_fill(self) -> None:
        entry = self.model.get_evidence(self.current_evidence_id) if self.current_evidence_id else None
        if not entry:
            QMessageBox.information(self, "No evidence selected", "Select an evidence record first.")
            return
        dialog = GuidedEvidenceDialog(entry, [(p.code, p.title) for p in self.model.phases], self)
        if dialog.exec() != QDialog.Accepted:
            return
        dialog.apply_to_entry(entry)
        self._ensure_phase_evidence_attachment(entry)
        missing = evidence_missing_fields(entry)
        if entry.ready_for_use and missing:
            entry.ready_for_use = False
            QMessageBox.information(
                self,
                "Evidence readiness corrected",
                "Record was marked READY, but required fields are still missing:\n\n- " + "\n- ".join(missing),
            )
        self.refresh_all_views()
        self._reselect_evidence_row(entry.evidence_id)

    def open_current_evidence_json(self) -> None:
        entry = self.model.get_evidence(self.current_evidence_id) if self.current_evidence_id else None
        if not entry:
            QMessageBox.information(self, "No evidence selected", "Select an evidence record first.")
            return

        context_text = self.model.attached_phase_context_text(entry)

        def apply_callback(raw_text: str) -> None:
            payload = json.loads(raw_text)
            if not isinstance(payload, dict):
                raise ValueError("Evidence JSON payload must be an object.")
            updated = self.model.replace_evidence_from_dict(entry.evidence_id, payload)
            self._ensure_phase_evidence_attachment(updated)
            self.refresh_all_views()
            self.tabs.setCurrentWidget(self.tab_evidence)
            self._reselect_evidence_row(updated.evidence_id)
            self.statusBar().showMessage(f"EVIDENCE UPDATED FROM JSON // {updated.evidence_id}")

        JsonViewerDialog(
            f"Evidence JSON — {entry.evidence_id}",
            json.dumps(entry.to_export_dict(self.model), ensure_ascii=False, indent=2),
            self,
            apply_callback=apply_callback,
            context_title="Контекст прикреплённой фазы",
            context_text=context_text,
        ).exec()

    def export_current_phase_evidence_pack(self) -> None:
        if not self.current_phase_code:
            QMessageBox.information(self, "No phase selected", "Select a phase first.")
            return
        phase = self.model.get_phase(self.current_phase_code)
        if not phase:
            return
        text = f"-Фаза {phase.code} — {phase.title}\n" + json.dumps(
            self.model.export_phase_evidence_pack(phase.code), ensure_ascii=False, indent=2
        )
        JsonViewerDialog(f"Evidence pack — {phase.code}", text, self).exec()

    def export_current_phase_evidence_json(self) -> None:
        if not self.current_phase_code:
            QMessageBox.information(self, "No phase selected", "Select a phase first.")
            return
        phase = self.model.get_phase(self.current_phase_code)
        if not phase:
            return
        JsonViewerDialog(
            f"Evidence JSON — {phase.code}",
            json.dumps(self.model.export_phase_evidence_json(phase.code), ensure_ascii=False, indent=2),
            self,
        ).exec()

    def remove_evidence(self) -> None:
        if not self.current_evidence_id:
            return
        self.model.evidence_entries = [e for e in self.model.evidence_entries if e.evidence_id != self.current_evidence_id]
        for phase in self.model.phases:
            if self.current_evidence_id in phase.knowledge_card.evidence_ids:
                phase.knowledge_card.evidence_ids = [eid for eid in phase.knowledge_card.evidence_ids if eid != self.current_evidence_id]
        for node in self.model.graph_nodes:
            if self.current_evidence_id in node.knowledge_card.evidence_ids:
                node.knowledge_card.evidence_ids = [eid for eid in node.knowledge_card.evidence_ids if eid != self.current_evidence_id]
        self.current_evidence_id = None
        self.refresh_all_views()

    def save_evidence_edits(self) -> None:
        if not self.current_evidence_id:
            return
        entry = self.model.get_evidence(self.current_evidence_id)
        if not entry:
            return
        new_id = self.evidence_id_edit.text().strip()
        if not new_id:
            QMessageBox.warning(self, "Empty record ID", "Evidence ID must not be empty.")
            return

        try:
            mechanistic_payload = self._read_mechanistic_ui_payload()
        except Exception as exc:
            QMessageBox.warning(self, "Invalid mechanism payload", str(exc))
            return

        payload = {
            "evidence_id": new_id,
            "title": self.evidence_title_edit.text().strip() or entry.title,
            "kind": self.evidence_kind_edit.text().strip() or entry.kind,
            "status": reverse_lookup(EVIDENCE_STATUS_LABELS, self.evidence_status_combo.currentText(), DEFAULT_EVIDENCE_STATUS),
            "evidence_role": reverse_lookup(EVIDENCE_ROLE_LABELS, self.evidence_role_combo.currentText(), DEFAULT_EVIDENCE_ROLE),
            "evidence_strength": self.evidence_strength_edit.text().strip() or "weak",
            "ready_for_use": self.evidence_ready_check.isChecked(),
            "citation": self.evidence_citation_edit.text().strip(),
            "url": self.evidence_url_edit.text().strip(),
            "summary": self.evidence_summary_edit.toPlainText().strip(),
            "provenance": self.evidence_provenance_edit.toPlainText().strip(),
            "updated_at": self.evidence_updated_edit.text().strip(),
            "mechanistic_payload": mechanistic_payload,
            "limitations": textblock_to_list(self.evidence_limitations_edit.toPlainText()),
            "open_questions": textblock_to_list(self.evidence_open_questions_edit.toPlainText()),
            "phase_refs": self._parse_phase_refs_block(self.evidence_phase_refs_edit.toPlainText()),
            "claim_refs": textblock_to_list(self.evidence_claim_refs_edit.toPlainText()),
            "gate_refs": textblock_to_list(self.evidence_gate_refs_edit.toPlainText()),
            "supports": textblock_to_list(self.evidence_supports_edit.toPlainText()),
            "challenges": textblock_to_list(self.evidence_challenges_edit.toPlainText()),
        }

        try:
            updated = self.model.replace_evidence_from_dict(entry.evidence_id, payload)
        except Exception as exc:
            QMessageBox.warning(self, "Evidence commit failed", str(exc))
            return

        self._ensure_phase_evidence_attachment(updated)
        missing = evidence_missing_fields(updated)
        if updated.ready_for_use and missing:
            updated.ready_for_use = False
            QMessageBox.information(
                self,
                "Evidence readiness corrected",
                "Record was marked READY, but required fields are still missing:\n\n- " + "\n- ".join(missing),
            )

        self.current_evidence_id = updated.evidence_id
        self.refresh_all_views()
        self._reselect_evidence_row(self.current_evidence_id)
        self.statusBar().showMessage(f"EVIDENCE COMMITTED // {self.current_evidence_id}")

    def _parse_phase_refs_block(self, text: str) -> List[Dict[str, str]]:
        refs: List[Dict[str, str]] = []
        for line in text.splitlines():
            raw = line.strip()
            if not raw:
                continue
            parts = [part.strip() for part in raw.split("|")]
            while len(parts) < 3:
                parts.append("")
            refs.append({"code": parts[0], "title": parts[1], "relation": parts[2] or "supports"})
        return refs

    @staticmethod
    def _centered_offset(index: int, total: int, gap: float) -> float:
        if total <= 1:
            return 0.0
        return (index - (total - 1) / 2.0) * gap

    def _build_edge_route_meta(self, edges: List[GraphEdge]) -> List[Dict[str, float | str]]:
        node_lookup = {node.node_id: node for node in self.model.graph_nodes}
        source_totals: Dict[tuple[str, str], int] = defaultdict(int)
        target_totals: Dict[tuple[str, str], int] = defaultdict(int)
        lane_totals: Dict[tuple[bool, str, str, str], int] = defaultdict(int)
        prepared: List[Optional[tuple[str, str, tuple[bool, str, str, str]]]] = []

        for edge in edges:
            source_node = node_lookup.get(edge.source)
            target_node = node_lookup.get(edge.target)
            if not source_node or not target_node:
                prepared.append(None)
                continue

            forward = source_node.x <= target_node.x
            source_side = "right" if forward else "left"
            target_side = "left" if forward else "right"
            lane_group = (forward, edge.source, edge.target, edge.layer)
            source_totals[(edge.source, source_side)] += 1
            target_totals[(edge.target, target_side)] += 1
            lane_totals[lane_group] += 1
            prepared.append((source_side, target_side, lane_group))

        source_seen: Dict[tuple[str, str], int] = defaultdict(int)
        target_seen: Dict[tuple[str, str], int] = defaultdict(int)
        lane_seen: Dict[tuple[bool, str, str, str], int] = defaultdict(int)
        route_meta: List[Dict[str, float | str]] = []

        for edge, payload in zip(edges, prepared):
            if payload is None:
                route_meta.append({"source_side": "right", "target_side": "left", "start_dy": 0.0, "end_dy": 0.0, "lane_offset": 0.0, "style": "forward"})
                continue

            source_side, target_side, lane_group = payload
            source_key = (edge.source, source_side)
            target_key = (edge.target, target_side)
            source_index = source_seen[source_key]
            target_index = target_seen[target_key]
            lane_index = lane_seen[lane_group]
            source_seen[source_key] += 1
            target_seen[target_key] += 1
            lane_seen[lane_group] += 1

            forward = lane_group[0]
            lane_offset = self._centered_offset(lane_index, lane_totals[lane_group], 28.0)
            if not forward:
                lane_offset = 140.0 + abs(lane_offset) + lane_index * 18.0

            route_meta.append({
                "source_side": source_side,
                "target_side": target_side,
                "start_dy": self._centered_offset(source_index, source_totals[source_key], 14.0),
                "end_dy": self._centered_offset(target_index, target_totals[target_key], 14.0),
                "lane_offset": lane_offset,
                "style": "forward" if forward else "backward",
            })

        return route_meta

    def _make_routed_path(self, start: QPointF, end: QPointF, route_meta: Dict[str, float | str]):
        from PySide6.QtGui import QPainterPath

        path = QPainterPath(start)
        lane_offset = float(route_meta.get("lane_offset", 0.0))
        style = str(route_meta.get("style", "forward"))

        if style == "backward":
            corridor_x = max(start.x(), end.x()) + lane_offset
        else:
            corridor_x = ((start.x() + end.x()) / 2.0) + lane_offset

        if abs(start.x() - end.x()) < 40.0:
            corridor_x = max(start.x(), end.x()) + 120.0 + abs(lane_offset)

        path.lineTo(corridor_x, start.y())
        path.lineTo(corridor_x, end.y())
        path.lineTo(end)
        return path

    def _ensure_phase_evidence_attachment(self, entry: EvidenceEntry) -> None:
        attached_codes = {normalize_code(ref.get("code", "")) for ref in entry.phase_refs if ref.get("code")}
        relation_map = {normalize_code(ref.get("code", "")): str(ref.get("relation", "supports")).strip() or "supports" for ref in entry.phase_refs}
        for phase in self.model.phases:
            code = normalize_code(phase.code)
            phase_node = f"phase::{code}"
            if code in attached_codes:
                if entry.evidence_id not in phase.knowledge_card.evidence_ids:
                    phase.knowledge_card.evidence_ids.append(entry.evidence_id)
                relation = relation_map.get(code, "supports")
                if relation_is_challenging(relation):
                    if phase_node not in entry.challenges:
                        entry.challenges.append(phase_node)
                    entry.supports = [item for item in entry.supports if item != phase_node]
                else:
                    if phase_node not in entry.supports:
                        entry.supports.append(phase_node)
                    entry.challenges = [item for item in entry.challenges if item != phase_node]
            elif entry.evidence_id in phase.knowledge_card.evidence_ids:
                if phase_node not in entry.supports and phase_node not in entry.challenges:
                    phase.knowledge_card.evidence_ids = [eid for eid in phase.knowledge_card.evidence_ids if eid != entry.evidence_id]
        entry.supports = dedupe_preserve_order(entry.supports)
        entry.challenges = dedupe_preserve_order(entry.challenges)

    # ---------- Phase workspace / helpers ----------
    def _save_node_position(self, node_id: str, pos: QPointF) -> None:
        node = self.model.get_node(node_id)
        if node:
            node.x = float(pos.x())
            node.y = float(pos.y())

    def open_current_phase_execution_packet(self) -> None:
        if not self.model.phases:
            QMessageBox.information(self, "No phases", "Load a roadmap archive first.")
            return
        code = self.current_phase_code or self.model.phases[0].code
        JsonViewerDialog(
            f"Context assembler — {code}",
            self.model.phase_execution_packet_text(code),
            self,
            context_title="Assembly status",
            context_text=self.model.phase_execution_packet_summary_text(code),
        ).exec()

    def open_phase_workspace(self) -> None:
        if not self.model.phases:
            QMessageBox.information(self, "No phases", "Load a roadmap archive first.")
            return
        initial_code = self.current_phase_code or self.model.phases[0].code
        dialog = PhaseWorkspaceDialog(self.model, self.apply_phase_workspace_payload, initial_code=initial_code, parent=self)
        dialog.phase_applied.connect(self._on_phase_workspace_applied)
        dialog.exec()

    def apply_phase_workspace_payload(self, original_code: str, payload: Dict[str, Any]) -> Phase:
        phase = self.model.replace_phase_from_dict(original_code, payload)
        self.refresh_all_views()
        self._reselect_phase_row(phase.code)
        return phase

    def _on_phase_workspace_applied(self, code: str) -> None:
        self.current_phase_code = code
        self._reselect_phase_row(code)
        self.statusBar().showMessage(f"PHASE UPDATED FROM WORKSPACE // {code}")

    def _reselect_phase_row(self, code: str) -> None:
        for row in range(self.phase_table.rowCount()):
            item = self.phase_table.item(row, 0)
            if item and normalize_code(item.data(Qt.UserRole)) == normalize_code(code):
                self.phase_table.selectRow(row)
                return

    def _reselect_gate_row(self, code: str) -> None:
        for row in range(self.gate_table.rowCount()):
            item = self.gate_table.item(row, 0)
            if item and normalize_code(item.data(Qt.UserRole)) == normalize_code(code):
                self.gate_table.selectRow(row)
                return

    def _reselect_evidence_row(self, evidence_id: str) -> None:
        for row in range(self.evidence_table.rowCount()):
            item = self.evidence_table.item(row, 0)
            if item and item.data(Qt.UserRole) == evidence_id:
                self.evidence_table.selectRow(row)
                return

    def _render_phase_inspector(self, phase: Phase) -> str:
        lines = [phase.protocol_label, ""]
        lines.append(f"STATE: {phase.display_status}")
        lines.append(f"VERIFY: {phase.display_validation_state}")
        lines.append(f"AUTHORITY: {phase.display_authority_role}")
        lines.append(f"COMPUTE: {phase.display_computational_role}")
        lines.append(f"CLAIM: {phase.display_claim_state}")
        lines.append(f"INTEGRITY: {phase.display_maturity}")
        lines.append("")
        if phase.knowledge_card.functional_role:
            lines.append("Functional role:")
            lines.append(phase.knowledge_card.functional_role)
            lines.append("")
        if phase.knowledge_card.observables:
            lines.append("Observables:")
            lines.extend(f"- {item}" for item in phase.knowledge_card.observables)
            lines.append("")
        if phase.knowledge_card.failure_modes:
            lines.append("Failure modes:")
            lines.extend(f"- {item}" for item in phase.knowledge_card.failure_modes)
            lines.append("")
        if phase.knowledge_card.forbidden_shortcuts:
            lines.append("Forbidden shortcuts:")
            lines.extend(f"- {item}" for item in phase.knowledge_card.forbidden_shortcuts)
            lines.append("")
        if phase.knowledge_card.evidence_ids:
            lines.append(f"ARCHIVE IDS: {', '.join(phase.knowledge_card.evidence_ids)}")
        return "\n".join(lines).strip()

    def _update_selection_inspector(self, text: str) -> None:
        self.selection_text.setPlainText(text)

    def _count_statuses(self) -> Dict[str, int]:
        return self.model.status_counts()

    def _claim_level_missing(self, level) -> List[str]:
        missing: List[str] = []
        for code in level.requires:
            status = self.model.item_status(code)
            if status != "closed":
                title = self.model.item_title(code)
                status_label = display_from_map(status or "missing", STATUS_LABELS) if status else "missing"
                missing.append(f"{code} ({title}; {status_label})")
        return missing

    def compute_highest_admissible_claim(self) -> str:
        if not self.model.claim_ladder:
            return "NO DATA"
        highest = "No claim tier unlocked yet"
        for level in self.model.claim_ladder:
            missing = self._claim_level_missing(level)
            if missing:
                break
            highest = f"{level.level} — {level.name}"
        return highest

    def _strong_claim_blockers(self) -> List[str]:
        if not self.model.claim_ladder:
            return []
        blockers: List[str] = []
        target_levels = []
        for level in self.model.claim_ladder:
            target_levels.append(level)
            if level.level == "L3":
                break
        seen: set[str] = set()
        for level in target_levels:
            for item in self._claim_level_missing(level):
                if item not in seen:
                    seen.add(item)
                    blockers.append(item)
        return blockers

    @staticmethod
    def load_app_fonts() -> None:
        font_dir = Path(__file__).with_name("fonts")
        for filename in ("Exo2-VariableFont_wght.ttf", "RussoOne-Regular.ttf", "Jura-VariableFont_wght.ttf"):
            path = font_dir / filename
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))

    def _make_cubic_path(self, start: QPointF, end: QPointF, dx: float):
        return self._make_routed_path(start, end, {"lane_offset": dx, "style": "forward"})


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    MainWindow.load_app_fonts()
    initial_json = None
    for candidate in ("Aiko_vNextRoadmap.cleaned.json", "Aiko_vNextRoadmap_claim_honest_v3.json"):
        p = Path(candidate)
        if p.exists():
            initial_json = p
            break
    window = MainWindow(initial_json=initial_json)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
