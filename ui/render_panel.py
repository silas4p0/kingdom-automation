from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QGroupBox,
)
from PySide6.QtCore import Signal, Qt
from models.render_job import RenderJob, RenderStatus


STATUS_COLORS = {
    RenderStatus.PENDING: "#90a4ae",
    RenderStatus.RUNNING: "#ffc107",
    RenderStatus.DONE: "#4caf50",
    RenderStatus.FAILED: "#f44336",
    RenderStatus.CANCELLED: "#9e9e9e",
}


class RenderPanel(QWidget):
    add_master_job = Signal()
    add_track_job = Signal()
    run_selected = Signal(str)
    run_all = Signal()
    cancel_job = Signal(str)
    export_script = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Render Queue")
        header.setStyleSheet("font-weight: bold; color: #00bcd4;")
        layout.addWidget(header)

        self._export_script_btn = QPushButton("Export Script")
        self._export_script_btn.setToolTip("Export the performance script as a JSON file for external render engines")
        self._export_script_btn.setStyleSheet(
            "QPushButton { background: #6a1b9a; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 4px 8px; }"
            "QPushButton:hover { background: #8e24aa; }"
        )
        layout.addWidget(self._export_script_btn)

        self._list_widget = QListWidget()
        self._list_widget.setMinimumHeight(80)
        layout.addWidget(self._list_widget, 1)

        add_row = QHBoxLayout()
        self._add_master_btn = QPushButton("+ Master")
        self._add_master_btn.setToolTip("Add Master render job")
        self._add_track_btn = QPushButton("+ Track")
        self._add_track_btn.setToolTip("Add job for selected track")
        add_row.addWidget(self._add_master_btn)
        add_row.addWidget(self._add_track_btn)
        layout.addLayout(add_row)

        action_row = QHBoxLayout()
        self._run_sel_btn = QPushButton("Run")
        self._run_sel_btn.setToolTip("Run selected job")
        self._run_all_btn = QPushButton("All")
        self._run_all_btn.setToolTip("Run all pending jobs")
        self._cancel_btn = QPushButton("X")
        self._cancel_btn.setToolTip("Cancel selected job")
        action_row.addWidget(self._run_sel_btn)
        action_row.addWidget(self._run_all_btn)
        action_row.addWidget(self._cancel_btn)
        layout.addLayout(action_row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-size: 11px; color: #aaa;")
        layout.addWidget(self._status_label)

        self._export_script_btn.clicked.connect(self.export_script.emit)
        self._add_master_btn.clicked.connect(self.add_master_job.emit)
        self._add_track_btn.clicked.connect(self.add_track_job.emit)
        self._run_sel_btn.clicked.connect(self._on_run_selected)
        self._run_all_btn.clicked.connect(self.run_all.emit)
        self._cancel_btn.clicked.connect(self._on_cancel)

        self._jobs: list[RenderJob] = []

    def set_jobs(self, jobs: list[RenderJob]) -> None:
        self._jobs = jobs
        self._rebuild_list()

    def refresh(self) -> None:
        self._rebuild_list()

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def get_selected_job_id(self) -> str:
        row = self._list_widget.currentRow()
        if 0 <= row < len(self._jobs):
            return self._jobs[row].id
        return ""

    def _rebuild_list(self) -> None:
        self._list_widget.clear()
        for job in self._jobs:
            color = STATUS_COLORS.get(job.status, "#aaa")
            text = f"[{job.status.value}] {job.label()} — {job.engine}"
            item = QListWidgetItem(text)
            item.setForeground(Qt.GlobalColor.white)
            item.setToolTip(f"Output: {job.output_path or '(auto)'}")
            self._list_widget.addItem(item)
        pending = sum(1 for j in self._jobs if j.status == RenderStatus.PENDING)
        done = sum(1 for j in self._jobs if j.status == RenderStatus.DONE)
        self._status_label.setText(f"{len(self._jobs)} jobs ({done} done, {pending} pending)")

    def _on_run_selected(self) -> None:
        jid = self.get_selected_job_id()
        if jid:
            self.run_selected.emit(jid)

    def _on_cancel(self) -> None:
        jid = self.get_selected_job_id()
        if jid:
            self.cancel_job.emit(jid)
