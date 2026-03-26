from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QComboBox, QGroupBox, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Signal, Qt


class ImportPanel(QWidget):
    import_audio = Signal()
    run_alignment = Signal()
    auto_fill_tokens = Signal()
    track_chosen = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Import Song")
        header.setStyleSheet("font-weight: bold; color: #00bcd4;")
        layout.addWidget(header)

        self._import_btn = QPushButton("Import Audio")
        self._import_btn.setToolTip("Load an audio file (WAV/MP3/M4A) for alignment")
        self._import_btn.setStyleSheet(
            "QPushButton { background: #6a1b9a; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 4px 8px; }"
            "QPushButton:hover { background: #8e24aa; }"
        )
        layout.addWidget(self._import_btn)

        self._audio_label = QLabel("No audio loaded")
        self._audio_label.setStyleSheet("font-size: 11px; color: #aaa;")
        self._audio_label.setWordWrap(True)
        layout.addWidget(self._audio_label)

        lyrics_header = QLabel("Lyrics")
        lyrics_header.setStyleSheet("font-weight: bold; color: #00bcd4; font-size: 12px;")
        layout.addWidget(lyrics_header)

        self._lyrics_edit = QTextEdit()
        self._lyrics_edit.setToolTip("Paste the song lyrics here for forced alignment with the imported audio")
        self._lyrics_edit.setPlaceholderText("Paste lyrics here...")
        self._lyrics_edit.setMaximumHeight(100)
        layout.addWidget(self._lyrics_edit)

        self._transcribe_btn = QPushButton("Auto-Transcribe")
        self._transcribe_btn.setToolTip("Placeholder for offline ASR")
        self._transcribe_btn.setEnabled(False)
        self._transcribe_btn.setStyleSheet("color: #666;")
        layout.addWidget(self._transcribe_btn)

        align_row = QHBoxLayout()
        self._align_btn = QPushButton("Align")
        self._align_btn.setToolTip("Run forced alignment on audio + lyrics")
        self._align_btn.setStyleSheet(
            "QPushButton { background: #1b5e20; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 4px 8px; }"
            "QPushButton:hover { background: #2e7d32; }"
        )
        align_row.addWidget(self._align_btn)
        layout.addLayout(align_row)

        self._alignment_list = QListWidget()
        self._alignment_list.setMaximumHeight(120)
        layout.addWidget(self._alignment_list)

        self._confidence_label = QLabel("")
        self._confidence_label.setStyleSheet("font-size: 11px; color: #aaa;")
        layout.addWidget(self._confidence_label)

        track_row = QHBoxLayout()
        track_row.addWidget(QLabel("Target:"))
        self._track_combo = QComboBox()
        self._track_combo.setToolTip("Select the target track for auto-filled tokens")
        self._track_combo.setMinimumWidth(80)
        track_row.addWidget(self._track_combo, 1)
        layout.addLayout(track_row)

        self._autofill_btn = QPushButton("Auto-Fill Tokens")
        self._autofill_btn.setToolTip("Map alignment to tokens and fill parameters via DSP")
        self._autofill_btn.setStyleSheet(
            "QPushButton { background: #e65100; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 4px 8px; }"
            "QPushButton:hover { background: #f57c00; }"
        )
        layout.addWidget(self._autofill_btn)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-size: 11px; color: #aaa;")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        layout.addStretch()

        self._import_btn.clicked.connect(self.import_audio.emit)
        self._align_btn.clicked.connect(self.run_alignment.emit)
        self._autofill_btn.clicked.connect(self.auto_fill_tokens.emit)
        self._track_combo.currentTextChanged.connect(self.track_chosen.emit)

    def set_audio_label(self, text: str) -> None:
        self._audio_label.setText(text)

    def get_lyrics_text(self) -> str:
        return self._lyrics_edit.toPlainText().strip()

    def set_lyrics_text(self, text: str) -> None:
        self._lyrics_edit.setPlainText(text)

    def set_tracks(self, track_names: list[str]) -> None:
        current = self._track_combo.currentText()
        self._track_combo.clear()
        self._track_combo.addItems(track_names)
        idx = self._track_combo.findText(current)
        if idx >= 0:
            self._track_combo.setCurrentIndex(idx)

    def get_selected_track(self) -> str:
        return self._track_combo.currentText()

    def set_alignment_words(self, words: list[dict]) -> None:
        self._alignment_list.clear()
        low_conf = 0
        for w in words:
            conf = w.get("confidence", 0)
            text = w.get("word", "")
            start = w.get("start_ms", 0)
            end = w.get("end_ms", 0)
            dur = end - start
            label = f"{text}  {start:.0f}-{end:.0f}ms  ({dur:.0f}ms)  [{conf:.0%}]"
            item = QListWidgetItem(label)
            if conf < 0.6:
                item.setForeground(Qt.GlobalColor.red)
                low_conf += 1
            elif conf < 0.8:
                item.setForeground(Qt.GlobalColor.yellow)
            self._alignment_list.addItem(item)
        if low_conf > 0:
            self._confidence_label.setText(
                f"{len(words)} words aligned, {low_conf} low confidence"
            )
            self._confidence_label.setStyleSheet("font-size: 11px; color: #f44336;")
        else:
            self._confidence_label.setText(f"{len(words)} words aligned")
            self._confidence_label.setStyleSheet("font-size: 11px; color: #4caf50;")

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)
