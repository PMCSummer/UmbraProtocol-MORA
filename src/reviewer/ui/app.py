from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from reviewer.config import ReviewerPipelineConfig
from reviewer.pipeline import LocalStatelessReviewerPipeline

try:
    from PySide6.QtCore import QThread, QTimer, Signal
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("PySide6 is required for reviewer UI") from exc


class _RunnerThread(QThread):
    cycle_finished = Signal(dict)
    run_failed = Signal(str)

    def __init__(
        self,
        *,
        pipeline: LocalStatelessReviewerPipeline,
        case_count: int,
        themes: list[str] | None,
        continuous: bool,
    ) -> None:
        super().__init__()
        self.pipeline = pipeline
        self.case_count = case_count
        self.themes = themes
        self.continuous = continuous
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True
        self.pipeline.stop()

    def run(self) -> None:  # noqa: D401
        try:
            while not self._stop_requested:
                summary = self.pipeline.run_cycle(case_count=self.case_count, themes=self.themes)
                self.cycle_finished.emit(summary)
                if not self.continuous:
                    break
                self.msleep(200)
        except Exception as exc:  # noqa: BLE001
            self.run_failed.emit(str(exc))


class ReviewerOperatorApp(QMainWindow):
    def __init__(self, *, config: ReviewerPipelineConfig | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Subject Trace Reviewer")
        self.resize(1280, 820)
        self.config = config or ReviewerPipelineConfig.default()
        self.pipeline: LocalStatelessReviewerPipeline | None = None
        self.runner_thread: _RunnerThread | None = None
        self.artifacts_root = Path(self.config.artifacts_root).expanduser().resolve()
        self.artifacts_root.mkdir(parents=True, exist_ok=True)

        self._build_ui()
        self._refresh_from_artifacts()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_from_artifacts)
        self.refresh_timer.start(1000)

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)
        splitter = QSplitter(self)
        layout.addWidget(splitter)
        self.setCentralWidget(root)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([430, 850])

        # Controls
        controls_box = QGroupBox("Controls")
        controls_form = QFormLayout(controls_box)
        self.case_count_spin = QSpinBox()
        self.case_count_spin.setRange(1, 200)
        self.case_count_spin.setValue(self.config.generation.max_cases_per_cycle)
        controls_form.addRow("Cases per cycle", self.case_count_spin)

        self.tier1_workers = QSpinBox()
        self.tier1_workers.setRange(1, 32)
        self.tier1_workers.setValue(self.config.tiers["tier1"].max_parallel_workers)
        controls_form.addRow("Tier1 workers", self.tier1_workers)
        self.tier2_workers = QSpinBox()
        self.tier2_workers.setRange(1, 32)
        self.tier2_workers.setValue(self.config.tiers["tier2"].max_parallel_workers)
        controls_form.addRow("Tier2 workers", self.tier2_workers)
        self.tier3_workers = QSpinBox()
        self.tier3_workers.setRange(1, 32)
        self.tier3_workers.setValue(self.config.tiers["tier3"].max_parallel_workers)
        controls_form.addRow("Tier3 workers", self.tier3_workers)

        self.keep_traces_checkbox = QCheckBox("Keep non-suspicious traces")
        self.keep_traces_checkbox.setChecked(self.config.retention.keep_non_suspicious_trace)
        controls_form.addRow(self.keep_traces_checkbox)

        self.trace_cap_spin = QSpinBox()
        self.trace_cap_spin.setRange(1, 10000)
        self.trace_cap_spin.setValue(self.config.retention.max_non_suspicious_traces)
        controls_form.addRow("Non-suspicious trace cap", self.trace_cap_spin)

        self.low_conf_t1_spin = QSpinBox()
        self.low_conf_t1_spin.setRange(1, 100)
        self.low_conf_t1_spin.setValue(
            int(self.config.escalation.tier1_escalate_confidence_max * 100)
        )
        controls_form.addRow("Tier1 escalation max conf %", self.low_conf_t1_spin)

        self.low_conf_t2_spin = QSpinBox()
        self.low_conf_t2_spin.setRange(1, 100)
        self.low_conf_t2_spin.setValue(
            int(self.config.escalation.tier2_second_opinion_confidence_max * 100)
        )
        controls_form.addRow("Tier2 second opinion max conf %", self.low_conf_t2_spin)

        self.second_opinion_check = QCheckBox("Second opinion on high priority")
        self.second_opinion_check.setChecked(
            self.config.escalation.second_opinion_on_high_priority
        )
        controls_form.addRow(self.second_opinion_check)

        theme_box = QGroupBox("Themes")
        theme_layout = QVBoxLayout(theme_box)
        self.theme_checks: dict[str, QCheckBox] = {}
        for theme in self.config.generation.themes:
            cb = QCheckBox(theme)
            cb.setChecked(True)
            self.theme_checks[theme] = cb
            theme_layout.addWidget(cb)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Stop")
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.pause_btn)
        btn_row.addWidget(self.resume_btn)
        btn_row.addWidget(self.stop_btn)
        self.start_btn.clicked.connect(self._start_pipeline)
        self.pause_btn.clicked.connect(self._pause_pipeline)
        self.resume_btn.clicked.connect(self._resume_pipeline)
        self.stop_btn.clicked.connect(self._stop_pipeline)

        left_layout.addWidget(controls_box)
        left_layout.addWidget(theme_box)
        left_layout.addLayout(btn_row)

        # Dashboard
        dashboard_box = QGroupBox("Dashboard")
        dashboard_form = QFormLayout(dashboard_box)
        self.active_workers_label = QLabel("-")
        self.queue_size_label = QLabel("-")
        self.reviewed_count_label = QLabel("-")
        self.suspicious_count_label = QLabel("-")
        self.theme_count_label = QLabel("-")
        self.tier_count_label = QLabel("-")
        self.model_health_label = QLabel("-")
        dashboard_form.addRow("Active workers", self.active_workers_label)
        dashboard_form.addRow("Queue size", self.queue_size_label)
        dashboard_form.addRow("Reviewed count", self.reviewed_count_label)
        dashboard_form.addRow("Suspicious count", self.suspicious_count_label)
        dashboard_form.addRow("Per-theme", self.theme_count_label)
        dashboard_form.addRow("Per-tier", self.tier_count_label)
        dashboard_form.addRow("Model health", self.model_health_label)
        right_layout.addWidget(dashboard_box)

        # Suspicious table
        self.suspicious_table = QTableWidget(0, 6)
        self.suspicious_table.setHorizontalHeaderLabels(
            ["case_id", "theme", "verdict", "priority", "model", "timestamp"]
        )
        self.suspicious_table.cellClicked.connect(self._load_case_detail_from_row)
        right_layout.addWidget(self.suspicious_table)

        # Case detail
        detail_box = QGroupBox("Case Detail")
        detail_layout = QVBoxLayout(detail_box)
        self.case_meta_text = QTextEdit()
        self.case_meta_text.setReadOnly(True)
        self.trace_preview_text = QTextEdit()
        self.trace_preview_text.setReadOnly(True)
        self.reviewer_json_text = QTextEdit()
        self.reviewer_json_text.setReadOnly(True)
        self.open_folder_btn = QPushButton("Open Artifact Folder")
        self.open_folder_btn.clicked.connect(self._open_current_artifact_folder)
        self._current_artifact_dir: Path | None = None

        detail_layout.addWidget(QLabel("Metadata"))
        detail_layout.addWidget(self.case_meta_text)
        detail_layout.addWidget(QLabel("Trace Preview"))
        detail_layout.addWidget(self.trace_preview_text)
        detail_layout.addWidget(QLabel("Reviewer JSON"))
        detail_layout.addWidget(self.reviewer_json_text)
        detail_layout.addWidget(self.open_folder_btn)
        right_layout.addWidget(detail_box)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._refresh_from_artifacts)
        file_menu.addAction(refresh_action)

    def _selected_themes(self) -> list[str]:
        return [name for name, cb in self.theme_checks.items() if cb.isChecked()]

    def _apply_controls_to_config(self) -> None:
        self.config.generation.max_cases_per_cycle = int(self.case_count_spin.value())
        self.config.tiers["tier1"].max_parallel_workers = int(self.tier1_workers.value())
        self.config.tiers["tier2"].max_parallel_workers = int(self.tier2_workers.value())
        self.config.tiers["tier3"].max_parallel_workers = int(self.tier3_workers.value())
        self.config.retention.keep_non_suspicious_trace = self.keep_traces_checkbox.isChecked()
        self.config.retention.max_non_suspicious_traces = int(self.trace_cap_spin.value())
        self.config.escalation.tier1_escalate_confidence_max = (
            float(self.low_conf_t1_spin.value()) / 100.0
        )
        self.config.escalation.tier2_second_opinion_confidence_max = (
            float(self.low_conf_t2_spin.value()) / 100.0
        )
        self.config.escalation.second_opinion_on_high_priority = (
            self.second_opinion_check.isChecked()
        )

    def _start_pipeline(self) -> None:
        if self.runner_thread is not None and self.runner_thread.isRunning():
            QMessageBox.information(self, "Reviewer", "Pipeline is already running.")
            return
        self._apply_controls_to_config()
        self.pipeline = LocalStatelessReviewerPipeline(config=self.config)
        self.runner_thread = _RunnerThread(
            pipeline=self.pipeline,
            case_count=self.config.generation.max_cases_per_cycle,
            themes=self._selected_themes(),
            continuous=True,
        )
        self.runner_thread.cycle_finished.connect(self._on_cycle_finished)
        self.runner_thread.run_failed.connect(self._on_run_failed)
        self.runner_thread.start()

    def _pause_pipeline(self) -> None:
        if self.pipeline is not None:
            self.pipeline.set_paused(True)

    def _resume_pipeline(self) -> None:
        if self.pipeline is not None:
            self.pipeline.set_paused(False)

    def _stop_pipeline(self) -> None:
        if self.runner_thread is not None:
            self.runner_thread.stop()
            self.runner_thread.wait(2000)
        self.runner_thread = None

    def _on_cycle_finished(self, _summary: dict) -> None:
        self._refresh_from_artifacts()

    def _on_run_failed(self, error_message: str) -> None:
        QMessageBox.critical(self, "Reviewer Pipeline Error", error_message)

    def _refresh_from_artifacts(self) -> None:
        status_path = self.artifacts_root / "logs" / "pipeline_status.json"
        if status_path.exists():
            status = json.loads(status_path.read_text(encoding="utf-8"))
            self.active_workers_label.setText(str(status.get("active_workers", "-")))
            self.queue_size_label.setText(str(status.get("queue_size", "-")))
            reviewed_count = status.get("closed_cases", 0) + status.get("suspicious_cases", 0)
            self.reviewed_count_label.setText(str(reviewed_count))
            self.suspicious_count_label.setText(str(status.get("suspicious_cases", "-")))
            self.theme_count_label.setText(str(status.get("per_theme_reviews", {})))
            self.tier_count_label.setText(str(status.get("per_tier_reviews", {})))
            self.model_health_label.setText(str(status.get("model_health", {})))

        suspicious_rows = []
        suspicious_path = self.artifacts_root / "summaries" / "suspicious_cases.jsonl"
        if suspicious_path.exists():
            for line in suspicious_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    suspicious_rows.append(json.loads(line))

        self.suspicious_table.setRowCount(len(suspicious_rows))
        for row_idx, row in enumerate(reversed(suspicious_rows[-500:])):
            self.suspicious_table.setItem(row_idx, 0, QTableWidgetItem(str(row.get("case_id", ""))))
            self.suspicious_table.setItem(row_idx, 1, QTableWidgetItem(str(row.get("theme", ""))))
            self.suspicious_table.setItem(
                row_idx, 2, QTableWidgetItem(str(row.get("overall_reading", "")))
            )
            self.suspicious_table.setItem(row_idx, 3, QTableWidgetItem(str(row.get("priority", ""))))
            self.suspicious_table.setItem(row_idx, 4, QTableWidgetItem(str(row.get("model", ""))))
            self.suspicious_table.setItem(row_idx, 5, QTableWidgetItem(str(row.get("timestamp", ""))))
            self.suspicious_table.item(row_idx, 0).setData(256, row.get("artifact_dir", ""))

    def _load_case_detail_from_row(self, row: int, _column: int) -> None:
        item = self.suspicious_table.item(row, 0)
        if item is None:
            return
        artifact_dir = Path(str(item.data(256)))
        self._current_artifact_dir = artifact_dir
        case_path = artifact_dir / "case.json"
        reviews_path = artifact_dir / "reviews.json"
        trace_path = artifact_dir / "trace.jsonl"
        if case_path.exists():
            self.case_meta_text.setPlainText(case_path.read_text(encoding="utf-8"))
        else:
            self.case_meta_text.setPlainText("{}")
        if reviews_path.exists():
            self.reviewer_json_text.setPlainText(reviews_path.read_text(encoding="utf-8"))
        else:
            self.reviewer_json_text.setPlainText("[]")
        if trace_path.exists():
            preview_lines = trace_path.read_text(encoding="utf-8").splitlines()[:80]
            self.trace_preview_text.setPlainText("\n".join(preview_lines))
        else:
            self.trace_preview_text.setPlainText("")

    def _open_current_artifact_folder(self) -> None:
        if self._current_artifact_dir is None:
            return
        path = self._current_artifact_dir.resolve()
        if not path.exists():
            return
        os.startfile(str(path))  # type: ignore[attr-defined]


def launch_ui(config: ReviewerPipelineConfig | None = None) -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    win = ReviewerOperatorApp(config=config)
    win.show()
    return app.exec()

