from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QInputDialog, QLineEdit,
    QGroupBox, QCheckBox,
)
from PySide6.QtCore import Signal, Qt
from models.track_model import TrackModel, TrackType


TRACK_TYPE_COLORS = {
    TrackType.VOCAL: "#4fc3f7",
    TrackType.INSTRUMENT: "#aed581",
    TrackType.MASTER: "#ffb74d",
}

TRACK_TYPE_LABELS = {
    TrackType.VOCAL: "VOC",
    TrackType.INSTRUMENT: "INS",
    TrackType.MASTER: "MIX",
}


class TrackItemWidget(QWidget):
    mute_toggled = Signal(str, bool)
    solo_toggled = Signal(str, bool)

    def __init__(self, track: TrackModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._track_id = track.id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        self._mute_cb = QCheckBox("M")
        self._mute_cb.setToolTip("Mute")
        self._mute_cb.setChecked(not track.enabled)
        self._mute_cb.setFixedWidth(28)
        layout.addWidget(self._mute_cb)

        self._solo_cb = QCheckBox("S")
        self._solo_cb.setToolTip("Solo")
        self._solo_cb.setChecked(track.solo)
        self._solo_cb.setFixedWidth(28)
        layout.addWidget(self._solo_cb)

        badge_color = TRACK_TYPE_COLORS.get(track.track_type, "#888")
        badge_text = TRACK_TYPE_LABELS.get(track.track_type, "?")
        badge = QLabel(badge_text)
        badge.setFixedWidth(36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background: {badge_color}; color: #1a1a1a; font-weight: bold; "
            f"font-size: 10px; border-radius: 3px; padding: 1px 4px;"
        )
        layout.addWidget(badge)

        self._name_label = QLabel(track.name)
        self._name_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self._name_label, 1)

        if track.track_type == TrackType.MASTER:
            self._mute_cb.setEnabled(False)
            self._solo_cb.setEnabled(False)

        self._mute_cb.toggled.connect(
            lambda checked: self.mute_toggled.emit(self._track_id, checked)
        )
        self._solo_cb.toggled.connect(
            lambda checked: self.solo_toggled.emit(self._track_id, checked)
        )

    @property
    def track_id(self) -> str:
        return self._track_id

    def set_name(self, name: str) -> None:
        self._name_label.setText(name)


class TracksPanel(QWidget):
    track_selected = Signal(str)
    assign_requested = Signal(str)
    export_stems_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Tracks")
        header.setStyleSheet("font-weight: bold; color: #00bcd4;")
        layout.addWidget(header)

        self._list_widget = QListWidget()
        self._list_widget.setMinimumHeight(100)
        self._list_widget.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self._list_widget, 1)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("+")
        self._add_btn.setToolTip("Add Track")
        self._rename_btn = QPushButton("Ren")
        self._rename_btn.setToolTip("Rename Track")
        self._delete_btn = QPushButton("Del")
        self._delete_btn.setToolTip("Delete Track")
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._rename_btn)
        btn_row.addWidget(self._delete_btn)
        layout.addLayout(btn_row)

        self._assign_btn = QPushButton("Assign to Track")
        self._assign_btn.setToolTip("Assign the currently selected tokens to this track")
        self._assign_btn.setEnabled(False)
        self._assign_btn.setStyleSheet(
            "QPushButton { background: #00838f; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 4px 8px; }"
            "QPushButton:hover { background: #00acc1; }"
            "QPushButton:disabled { background: #555; color: #888; }"
        )
        layout.addWidget(self._assign_btn)

        self._export_btn = QPushButton("Export Stems")
        self._export_btn.setToolTip("Export each track as a separate audio stem file")
        self._export_btn.setStyleSheet(
            "QPushButton { background: #5c6bc0; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 4px 8px; }"
            "QPushButton:hover { background: #7986cb; }"
        )
        layout.addWidget(self._export_btn)

        scope_group = QGroupBox("Playback Track Scope")
        scope_layout = QHBoxLayout(scope_group)
        self._scope_current_btn = QPushButton("Current")
        self._scope_current_btn.setToolTip("Preview only the selected track")
        self._scope_current_btn.setCheckable(True)
        self._scope_master_btn = QPushButton("Master")
        self._scope_master_btn.setToolTip("Preview the full master mix of all tracks")
        self._scope_master_btn.setCheckable(True)
        self._scope_master_btn.setChecked(True)
        scope_layout.addWidget(self._scope_current_btn)
        scope_layout.addWidget(self._scope_master_btn)
        layout.addWidget(scope_group)

        self._scope_current_btn.clicked.connect(self._on_scope_current)
        self._scope_master_btn.clicked.connect(self._on_scope_master)

        self._add_btn.clicked.connect(self._on_add)
        self._rename_btn.clicked.connect(self._on_rename)
        self._delete_btn.clicked.connect(self._on_delete)
        self._assign_btn.clicked.connect(self._on_assign)
        self._export_btn.clicked.connect(self.export_stems_requested.emit)

        self._tracks: list[TrackModel] = []
        self._item_widgets: list[TrackItemWidget] = []

    def set_tracks(self, tracks: list[TrackModel]) -> None:
        self._tracks = tracks
        self._rebuild_list()

    def set_assign_enabled(self, enabled: bool) -> None:
        self._assign_btn.setEnabled(enabled)

    def get_selected_track_id(self) -> str:
        row = self._list_widget.currentRow()
        if 0 <= row < len(self._tracks):
            return self._tracks[row].id
        return ""

    def get_playback_scope(self) -> str:
        if self._scope_current_btn.isChecked():
            return "current"
        return "master"

    def _rebuild_list(self) -> None:
        self._list_widget.clear()
        self._item_widgets.clear()
        for track in self._tracks:
            item = QListWidgetItem()
            widget = TrackItemWidget(track)
            widget.mute_toggled.connect(self._on_mute)
            widget.solo_toggled.connect(self._on_solo)
            item.setSizeHint(widget.sizeHint())
            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, widget)
            self._item_widgets.append(widget)
        if self._tracks:
            self._list_widget.setCurrentRow(0)

    def _on_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._tracks):
            self.track_selected.emit(self._tracks[row].id)

    def _on_mute(self, track_id: str, muted: bool) -> None:
        for t in self._tracks:
            if t.id == track_id:
                t.enabled = not muted
                break

    def _on_solo(self, track_id: str, soloed: bool) -> None:
        for t in self._tracks:
            if t.id == track_id:
                t.solo = soloed
                break

    def _on_add(self) -> None:
        items = ["VOCAL", "INSTRUMENT"]
        type_str, ok = QInputDialog.getItem(
            self, "Add Track", "Track type:", items, 0, False
        )
        if not ok:
            return
        name, ok2 = QInputDialog.getText(
            self, "Add Track", "Track name:",
            QLineEdit.EchoMode.Normal, f"New {type_str.title()}"
        )
        if ok2 and name.strip():
            ttype = TrackType.VOCAL if type_str == "VOCAL" else TrackType.INSTRUMENT
            new_track = TrackModel(name.strip(), ttype)
            self._tracks.insert(len(self._tracks) - 1, new_track)
            self._rebuild_list()

    def _on_rename(self) -> None:
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self._tracks):
            return
        track = self._tracks[row]
        if track.track_type == TrackType.MASTER:
            return
        name, ok = QInputDialog.getText(
            self, "Rename Track", "New name:",
            QLineEdit.EchoMode.Normal, track.name
        )
        if ok and name.strip():
            track.name = name.strip()
            self._item_widgets[row].set_name(track.name)

    def _on_delete(self) -> None:
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self._tracks):
            return
        if self._tracks[row].track_type == TrackType.MASTER:
            return
        self._tracks.pop(row)
        self._rebuild_list()

    def _on_assign(self) -> None:
        track_id = self.get_selected_track_id()
        if track_id:
            self.assign_requested.emit(track_id)

    def _on_scope_current(self) -> None:
        self._scope_current_btn.setChecked(True)
        self._scope_master_btn.setChecked(False)

    def _on_scope_master(self) -> None:
        self._scope_master_btn.setChecked(True)
        self._scope_current_btn.setChecked(False)
