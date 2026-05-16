from __future__ import annotations

import json
from typing import Any

from .gui.chamber_view import create_chamber_view_class
from .gui.localization import RUSSIAN_UI_STRINGS
from .gui.viewmodel import (
    Stage5GuiViewModel,
    build_stage5_gui_view_model,
    list_stage5_gui_scenarios,
    run_stage5_gui_payload,
)

PYSIDE6_MISSING_MESSAGE = "PySide6 is required for this GUI. Install PySide6 to run symbolic trade GUI."


def _load_qt() -> dict[str, Any] | None:
    try:
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QColor, QFont, QPainter, QPen
        from PySide6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QPlainTextEdit,
            QPushButton,
            QSizePolicy,
            QSplitter,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        return None
    return {
        "Qt": Qt,
        "QTimer": QTimer,
        "QRectF": QRectF,
        "QColor": QColor,
        "QFont": QFont,
        "QPainter": QPainter,
        "QPen": QPen,
        "QApplication": QApplication,
        "QCheckBox": QCheckBox,
        "QComboBox": QComboBox,
        "QFormLayout": QFormLayout,
        "QGroupBox": QGroupBox,
        "QHBoxLayout": QHBoxLayout,
        "QLabel": QLabel,
        "QListWidget": QListWidget,
        "QListWidgetItem": QListWidgetItem,
        "QMainWindow": QMainWindow,
        "QPlainTextEdit": QPlainTextEdit,
        "QPushButton": QPushButton,
        "QSizePolicy": QSizePolicy,
        "QSplitter": QSplitter,
        "QTableWidget": QTableWidget,
        "QTableWidgetItem": QTableWidgetItem,
        "QVBoxLayout": QVBoxLayout,
        "QWidget": QWidget,
    }


class _WindowController:
    def __init__(self, qt: dict[str, Any], *, scenario: str, execute_world_actuator: bool, dev_mode: bool) -> None:
        self.qt = qt
        self._scenario = scenario
        self._execute = execute_world_actuator
        self._dev_mode = dev_mode
        self.vm: Stage5GuiViewModel | None = None

        QTimer = self.qt["QTimer"]
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self._play_tick)

        self.window = self._create_window()
        self._run_scenario()

    def _create_window(self):
        QMainWindow = self.qt["QMainWindow"]
        QWidget = self.qt["QWidget"]
        QVBoxLayout = self.qt["QVBoxLayout"]
        QHBoxLayout = self.qt["QHBoxLayout"]
        QGroupBox = self.qt["QGroupBox"]
        QFormLayout = self.qt["QFormLayout"]
        QComboBox = self.qt["QComboBox"]
        QCheckBox = self.qt["QCheckBox"]
        QPushButton = self.qt["QPushButton"]
        QSplitter = self.qt["QSplitter"]
        QListWidget = self.qt["QListWidget"]
        QTableWidget = self.qt["QTableWidget"]
        QPlainTextEdit = self.qt["QPlainTextEdit"]
        QLabel = self.qt["QLabel"]
        QSizePolicy = self.qt["QSizePolicy"]
        Qt = self.qt["Qt"]
        ChamberView = create_chamber_view_class(self.qt)

        win = QMainWindow()
        win.setWindowTitle(RUSSIAN_UI_STRINGS["window_title"])
        root = QWidget()
        root_layout = QVBoxLayout(root)

        controls = QGroupBox("Управление запуском")
        controls_layout = QFormLayout(controls)

        self.scenario_selector = QComboBox()
        for scenario_id in list_stage5_gui_scenarios():
            self.scenario_selector.addItem(scenario_id)
        index = self.scenario_selector.findText(self._scenario)
        if index >= 0:
            self.scenario_selector.setCurrentIndex(index)
        controls_layout.addRow(RUSSIAN_UI_STRINGS["scenario_selector"], self.scenario_selector)

        self.mode_selector = QComboBox()
        self.mode_selector.addItem(RUSSIAN_UI_STRINGS["run_mode_observe"], userData=False)
        self.mode_selector.addItem(RUSSIAN_UI_STRINGS["run_mode_execute"], userData=True)
        self.mode_selector.setCurrentIndex(1 if self._execute else 0)
        controls_layout.addRow(RUSSIAN_UI_STRINGS["run_mode"], self.mode_selector)

        mode_row = QHBoxLayout()
        self.run_button = QPushButton(RUSSIAN_UI_STRINGS["run_button"])
        self.reset_button = QPushButton(RUSSIAN_UI_STRINGS["reset_button"])
        mode_row.addWidget(self.run_button)
        mode_row.addWidget(self.reset_button)
        controls_layout.addRow(mode_row)

        timeline_row = QHBoxLayout()
        self.first_button = QPushButton(RUSSIAN_UI_STRINGS["first_step_button"])
        self.prev_button = QPushButton(RUSSIAN_UI_STRINGS["prev_step_button"])
        self.next_button = QPushButton(RUSSIAN_UI_STRINGS["next_step_button"])
        self.last_button = QPushButton(RUSSIAN_UI_STRINGS["last_step_button"])
        timeline_row.addWidget(self.first_button)
        timeline_row.addWidget(self.prev_button)
        timeline_row.addWidget(self.next_button)
        timeline_row.addWidget(self.last_button)
        controls_layout.addRow(timeline_row)

        play_row = QHBoxLayout()
        self.play_pause_button = QPushButton(RUSSIAN_UI_STRINGS["play_button"])
        self.speed_selector = QComboBox()
        self.speed_selector.addItem(RUSSIAN_UI_STRINGS["speed_slow"], userData=1500)
        self.speed_selector.addItem(RUSSIAN_UI_STRINGS["speed_normal"], userData=800)
        self.speed_selector.addItem(RUSSIAN_UI_STRINGS["speed_fast"], userData=350)
        self.speed_selector.setCurrentIndex(1)
        play_row.addWidget(self.play_pause_button)
        play_row.addWidget(QLabel(RUSSIAN_UI_STRINGS["speed_selector"]))
        play_row.addWidget(self.speed_selector)
        controls_layout.addRow(play_row)

        self.step_label = QLabel(RUSSIAN_UI_STRINGS["current_step_label"].format(current=0, total=0))
        controls_layout.addRow(self.step_label)

        self.dev_mode_toggle = QCheckBox(RUSSIAN_UI_STRINGS["dev_mode_toggle"])
        self.dev_mode_toggle.setChecked(self._dev_mode)
        controls_layout.addRow(self.dev_mode_toggle)

        self.include_eval_toggle = QCheckBox(RUSSIAN_UI_STRINGS["include_eval_toggle"])
        self.include_eval_toggle.setEnabled(self._dev_mode)
        controls_layout.addRow(self.include_eval_toggle)

        root_layout.addWidget(controls)

        splitter = QSplitter(Qt.Horizontal)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        scene_group = QGroupBox(RUSSIAN_UI_STRINGS["scene_panel"])
        scene_layout = QVBoxLayout(scene_group)
        self.chamber_view = ChamberView()
        self.chamber_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scene_layout.addWidget(self.chamber_view)
        left_layout.addWidget(scene_group, 5)

        timeline_group = QGroupBox(RUSSIAN_UI_STRINGS["timeline_panel"])
        timeline_layout = QVBoxLayout(timeline_group)
        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(3)
        self.timeline_table.setHorizontalHeaderLabels(
            [
                RUSSIAN_UI_STRINGS["timeline_columns_step"],
                RUSSIAN_UI_STRINGS["timeline_columns_title"],
                RUSSIAN_UI_STRINGS["timeline_columns_status"],
            ]
        )
        self.timeline_table.horizontalHeader().setStretchLastSection(True)
        timeline_layout.addWidget(self.timeline_table)
        left_layout.addWidget(timeline_group, 2)

        causal_group = QGroupBox(RUSSIAN_UI_STRINGS["causal_spine_panel"])
        causal_layout = QVBoxLayout(causal_group)
        self.causal_table = QTableWidget()
        self.causal_table.setColumnCount(3)
        self.causal_table.setHorizontalHeaderLabels(["Этап", "Описание", "Статус"])
        self.causal_table.horizontalHeader().setStretchLastSection(True)
        causal_layout.addWidget(self.causal_table)
        left_layout.addWidget(causal_group, 2)

        anti_group = QGroupBox(RUSSIAN_UI_STRINGS["anti_shortcut_panel"])
        anti_layout = QVBoxLayout(anti_group)
        self.anti_list = QListWidget()
        anti_layout.addWidget(self.anti_list)
        left_layout.addWidget(anti_group, 1)

        result_group = QGroupBox(RUSSIAN_UI_STRINGS["result_panel"])
        result_layout = QVBoxLayout(result_group)
        self.result_text = QPlainTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        right_layout.addWidget(result_group)

        compare_group = QGroupBox(RUSSIAN_UI_STRINGS["compare_panel"])
        compare_layout = QHBoxLayout(compare_group)
        self.compare_left = QLabel()
        self.compare_left.setWordWrap(True)
        self.compare_right = QLabel()
        self.compare_right.setWordWrap(True)
        compare_layout.addWidget(self.compare_left)
        compare_layout.addWidget(self.compare_right)
        right_layout.addWidget(compare_group)

        dev_group = QGroupBox(RUSSIAN_UI_STRINGS["trace_inspector_panel"])
        dev_layout = QVBoxLayout(dev_group)
        self.dev_caption = QLabel(RUSSIAN_UI_STRINGS["eval_only_caption"])
        self.dev_text = QPlainTextEdit()
        self.dev_text.setReadOnly(True)
        dev_layout.addWidget(self.dev_caption)
        dev_layout.addWidget(self.dev_text)
        right_layout.addWidget(dev_group)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([900, 520])
        root_layout.addWidget(splitter)

        win.setCentralWidget(root)

        self.run_button.clicked.connect(self._run_scenario)
        self.reset_button.clicked.connect(self._reset_timeline)
        self.first_button.clicked.connect(self._go_first)
        self.prev_button.clicked.connect(self._go_previous)
        self.next_button.clicked.connect(self._go_next)
        self.last_button.clicked.connect(self._go_last)
        self.play_pause_button.clicked.connect(self._toggle_play_pause)
        self.speed_selector.currentIndexChanged.connect(self._update_timer_interval)
        self.scenario_selector.currentIndexChanged.connect(self._run_scenario)
        self.mode_selector.currentIndexChanged.connect(self._run_scenario)
        self.dev_mode_toggle.toggled.connect(self._on_dev_mode_toggle)
        self.include_eval_toggle.toggled.connect(self._run_scenario)
        self.timeline_table.cellClicked.connect(self._set_step_from_table)

        return win

    def _play_tick(self) -> None:
        if self.vm is None:
            return
        if self.vm.can_go_next:
            self.vm.go_next()
            self._refresh_view()
            return
        self.play_timer.stop()
        self.vm.set_play_state("paused")
        self.play_pause_button.setText(RUSSIAN_UI_STRINGS["play_button"])

    def _toggle_play_pause(self) -> None:
        if self.vm is None:
            return
        if self.play_timer.isActive():
            self.play_timer.stop()
            self.vm.set_play_state("paused")
            self.play_pause_button.setText(RUSSIAN_UI_STRINGS["play_button"])
            return
        self._update_timer_interval()
        self.play_timer.start()
        self.vm.set_play_state("playing")
        self.play_pause_button.setText(RUSSIAN_UI_STRINGS["pause_button"])

    def _update_timer_interval(self) -> None:
        interval = int(self.speed_selector.currentData())
        self.play_timer.setInterval(interval)

    def _on_dev_mode_toggle(self, checked: bool) -> None:
        self.include_eval_toggle.setEnabled(checked)
        if not checked:
            self.include_eval_toggle.setChecked(False)
        self._run_scenario()

    def _set_step_from_table(self, row: int, _column: int) -> None:
        if self.vm is None:
            return
        self.vm.set_step(row)
        self._refresh_view()

    def _run_scenario(self) -> None:
        self.play_timer.stop()
        scenario_id = self.scenario_selector.currentText()
        execute = bool(self.mode_selector.currentData())
        dev_mode = bool(self.dev_mode_toggle.isChecked())
        include_eval_only = dev_mode and bool(self.include_eval_toggle.isChecked())

        payload = run_stage5_gui_payload(
            scenario_id,
            execute_world_actuator=execute,
            include_eval_only=include_eval_only,
            include_ledger=True,
            include_records=True,
        )
        self.vm = build_stage5_gui_view_model(
            payload,
            dev_mode=dev_mode,
            include_eval_only=include_eval_only,
        )
        self._refresh_view()

    def _reset_timeline(self) -> None:
        if self.vm is None:
            return
        self.vm.reset_timeline()
        self.play_timer.stop()
        self.play_pause_button.setText(RUSSIAN_UI_STRINGS["play_button"])
        self._refresh_view()

    def _go_first(self) -> None:
        if self.vm is None:
            return
        self.vm.go_first()
        self._refresh_view()

    def _go_previous(self) -> None:
        if self.vm is None:
            return
        self.vm.go_previous()
        self._refresh_view()

    def _go_next(self) -> None:
        if self.vm is None:
            return
        self.vm.go_next()
        self._refresh_view()

    def _go_last(self) -> None:
        if self.vm is None:
            return
        self.vm.go_last()
        self._refresh_view()

    def _refresh_timeline_table(self, vm: Stage5GuiViewModel) -> None:
        QTableWidgetItem = self.qt["QTableWidgetItem"]
        self.timeline_table.blockSignals(True)
        self.timeline_table.setRowCount(vm.step_count)
        for row, step in enumerate(vm.timeline_state.steps):
            self.timeline_table.setItem(row, 0, QTableWidgetItem(str(step.step_index)))
            self.timeline_table.setItem(row, 1, QTableWidgetItem(step.title_ru))
            self.timeline_table.setItem(row, 2, QTableWidgetItem(_status_ru_for_gui(step.status)))
        if vm.step_count:
            self.timeline_table.selectRow(vm.current_step_index)
        self.timeline_table.blockSignals(False)

    def _refresh_view(self) -> None:
        if self.vm is None:
            return
        vm = self.vm
        QListWidgetItem = self.qt["QListWidgetItem"]
        QTableWidgetItem = self.qt["QTableWidgetItem"]

        self.chamber_view.set_frame(vm.current_frame)
        self._refresh_timeline_table(vm)

        self.step_label.setText(
            RUSSIAN_UI_STRINGS["current_step_label"].format(
                current=vm.current_step_index + 1,
                total=vm.step_count,
            )
            + f": {vm.current_step.title_ru} ({_status_ru_for_gui(vm.current_step.status)})"
        )

        self.causal_table.setRowCount(len(vm.causal_spine_items))
        for row, item in enumerate(vm.causal_spine_items):
            self.causal_table.setItem(row, 0, QTableWidgetItem(item["phase"]))
            self.causal_table.setItem(row, 1, QTableWidgetItem(item["label_ru"]))
            self.causal_table.setItem(row, 2, QTableWidgetItem(item["status_ru"]))

        self.anti_list.clear()
        for item in vm.anti_shortcut_items:
            prefix = "[OK]" if item["passed"] else "[FAIL]"
            self.anti_list.addItem(QListWidgetItem(f"{prefix} {item['label_ru']}"))

        result_lines = [f"{entry['label_ru']}: {entry['value']}" for entry in vm.result_items]
        result_lines.append("")
        result_lines.append(f"{RUSSIAN_UI_STRINGS['timeline_step_header']}: {vm.current_step.short_explanation_ru}")
        result_lines.append(f"Кадр камеры: {vm.current_frame.title_ru} / {vm.current_frame.public_status}")
        result_lines.append(f"Тип события: {vm.current_frame.event_kind}; basis={vm.current_frame.basis.value}")
        result_lines.append(f"evidence_refs: {list(vm.current_step.evidence_refs)}")
        result_lines.append(f"note: {vm.current_step.claim_boundary_note_ru}")
        self.result_text.setPlainText("\n".join(result_lines))

        self.compare_left.setText(f"{vm.compare_items[0]['title']}\n{vm.compare_items[0]['text']}")
        self.compare_right.setText(f"{vm.compare_items[1]['title']}\n{vm.compare_items[1]['text']}")

        if self.dev_mode_toggle.isChecked():
            self.dev_text.setPlainText(json.dumps(vm.developer_payload, ensure_ascii=False, indent=2, sort_keys=True))
            self.dev_caption.setText(RUSSIAN_UI_STRINGS["eval_only_caption"])
        else:
            self.dev_text.setPlainText(RUSSIAN_UI_STRINGS["dev_mode_disabled"])
            self.dev_caption.setText(RUSSIAN_UI_STRINGS["dev_mode_disabled"])

        self.prev_button.setEnabled(vm.can_go_previous)
        self.first_button.setEnabled(vm.can_go_previous)
        self.next_button.setEnabled(vm.can_go_next)
        self.last_button.setEnabled(vm.can_go_next)


def _status_ru_for_gui(status: str) -> str:
    mapping = {
        "trace_derived": RUSSIAN_UI_STRINGS["status_trace_derived"],
        "inferred_from_stage5_summary": RUSSIAN_UI_STRINGS["status_inferred"],
        "not_exposed": RUSSIAN_UI_STRINGS["status_not_exposed"],
        "blocked": RUSSIAN_UI_STRINGS["status_blocked"],
        "skipped": RUSSIAN_UI_STRINGS["status_skipped"],
        "failed": RUSSIAN_UI_STRINGS["status_failed"],
        "verified": RUSSIAN_UI_STRINGS["status_verified"],
        "unverified": RUSSIAN_UI_STRINGS["status_unverified"],
        "missing": RUSSIAN_UI_STRINGS["status_missing"],
    }
    return mapping.get(status, status)


def run_symbolic_trade_gui(
    *,
    scenario: str | None = None,
    execute_world_actuator: bool = False,
    dev_mode: bool = False,
) -> int:
    qt = _load_qt()
    if qt is None:
        print(PYSIDE6_MISSING_MESSAGE)
        return 2

    QApplication = qt["QApplication"]
    app = QApplication.instance() or QApplication([])
    selected_scenario = scenario or list_stage5_gui_scenarios()[0]
    controller = _WindowController(
        qt,
        scenario=selected_scenario,
        execute_world_actuator=execute_world_actuator,
        dev_mode=dev_mode,
    )
    controller.window.resize(1360, 860)
    controller.window.show()
    return app.exec()
