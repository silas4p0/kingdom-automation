from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, QHBoxLayout,
)
from PySide6.QtCore import Qt
import datetime


class ConsolePanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self._toggle_btn = QPushButton("Console")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(True)
        self._toggle_btn.setStyleSheet("font-weight: bold; text-align: left;")
        self._toggle_btn.clicked.connect(self._on_toggle)
        header.addWidget(self._toggle_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedWidth(60)
        self._clear_btn.clicked.connect(self._on_clear)
        header.addWidget(self._clear_btn)
        layout.addLayout(header)

        self._text_area = QPlainTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setMaximumBlockCount(500)
        self._text_area.setMinimumHeight(80)
        layout.addWidget(self._text_area)

    def log(self, message: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._text_area.appendPlainText(f"[{ts}] {message}")
        self._text_area.verticalScrollBar().setValue(
            self._text_area.verticalScrollBar().maximum()
        )

    def _on_toggle(self) -> None:
        self._collapsed = not self._collapsed
        self._text_area.setVisible(not self._collapsed)
        self._clear_btn.setVisible(not self._collapsed)

    def _on_clear(self) -> None:
        self._text_area.clear()
