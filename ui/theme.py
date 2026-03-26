DARK_THEME = """
QMainWindow, QDialog {
    background-color: #2b2b2b;
}
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #333333;
    border: 1px solid #444444;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    font-weight: bold;
    color: #00bcd4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #00bcd4;
}
QPushButton {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #444444;
    border-color: #00bcd4;
}
QPushButton:pressed {
    background-color: #00838f;
}
QPushButton:checked {
    background-color: #00838f;
    border-color: #00bcd4;
    color: #ffffff;
}
QPushButton:disabled {
    background-color: #2e2e2e;
    color: #666666;
    border-color: #3a3a3a;
}
QComboBox {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 24px;
}
QComboBox:hover {
    border-color: #00bcd4;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #333333;
    color: #e0e0e0;
    selection-background-color: #00838f;
    border: 1px solid #555555;
}
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #444444;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #00bcd4;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #00e5ff;
}
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #00838f;
}
QLabel {
    background-color: transparent;
    color: #e0e0e0;
}
QToolBar {
    background-color: #333333;
    border-bottom: 1px solid #444444;
    spacing: 6px;
    padding: 4px;
}
QCheckBox {
    color: #e0e0e0;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #3a3a3a;
}
QCheckBox::indicator:checked {
    background-color: #00bcd4;
    border-color: #00bcd4;
}
QScrollBar:vertical {
    background: #2b2b2b;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #555555;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #00bcd4;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QSplitter::handle {
    background-color: #444444;
}
"""

LIGHT_THEME = """
QMainWindow, QDialog {
    background-color: #f0f0f0;
}
QWidget {
    background-color: #f0f0f0;
    color: #222222;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    font-weight: bold;
    color: #00838f;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #00838f;
}
QPushButton {
    background-color: #e0e0e0;
    color: #222222;
    border: 1px solid #bbbbbb;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #d0d0d0;
    border-color: #00bcd4;
}
QPushButton:pressed {
    background-color: #00bcd4;
    color: #ffffff;
}
QPushButton:checked {
    background-color: #00838f;
    border-color: #00bcd4;
    color: #ffffff;
}
QPushButton:disabled {
    background-color: #e8e8e8;
    color: #aaaaaa;
    border-color: #cccccc;
}
QComboBox {
    background-color: #ffffff;
    color: #222222;
    border: 1px solid #bbbbbb;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 24px;
}
QComboBox:hover {
    border-color: #00bcd4;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #222222;
    selection-background-color: #00bcd4;
    border: 1px solid #bbbbbb;
}
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #cccccc;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #00bcd4;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #00acc1;
}
QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #222222;
    border: 1px solid #cccccc;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #b2ebf2;
}
QLabel {
    background-color: transparent;
    color: #222222;
}
QToolBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #cccccc;
    spacing: 6px;
    padding: 4px;
}
QCheckBox {
    color: #222222;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #bbbbbb;
    border-radius: 3px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #00bcd4;
    border-color: #00bcd4;
}
QScrollBar:vertical {
    background: #f0f0f0;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #bbbbbb;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #00bcd4;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QSplitter::handle {
    background-color: #cccccc;
}
"""


class ThemeManager:
    DARK = "dark"
    LIGHT = "light"

    def __init__(self) -> None:
        self._current = self.DARK

    @property
    def current(self) -> str:
        return self._current

    def toggle(self) -> str:
        self._current = self.LIGHT if self._current == self.DARK else self.DARK
        return self._current

    def set_theme(self, theme: str) -> None:
        if theme in (self.DARK, self.LIGHT):
            self._current = theme

    def stylesheet(self) -> str:
        return DARK_THEME if self._current == self.DARK else LIGHT_THEME
