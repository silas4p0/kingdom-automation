from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QScrollArea,
    QHBoxLayout, QLayout, QLayoutItem, QApplication,
)
from PySide6.QtCore import Signal, Qt, QRect, QSize, QPoint
from PySide6.QtGui import QMouseEvent


class FlowLayout(QLayout):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._spacing_val = 4

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def setSpacing(self, spacing: int) -> None:
        self._spacing_val = spacing

    def spacing(self) -> int:
        return self._spacing_val

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            sz = item.sizeHint()
            next_x = x + sz.width() + self._spacing_val
            if next_x - self._spacing_val > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + self._spacing_val
                next_x = x + sz.width() + self._spacing_val
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), sz))

            x = next_x
            line_height = max(line_height, sz.height())

        return y + line_height - rect.y() + m.bottom()


class TokenButton(QPushButton):
    token_clicked = Signal(int)
    token_shift_clicked = Signal(int)
    token_drag_entered = Signal(int)

    def __init__(self, word: str, index: int, parent: QWidget | None = None) -> None:
        super().__init__(word, parent)
        self.index = index
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._locked = False
        self._range_selected = False
        self._update_style(False)

    def set_selected(self, selected: bool) -> None:
        self.setChecked(selected)
        self._update_style(selected)

    def set_locked(self, locked: bool) -> None:
        self._locked = locked
        self._update_style(self.isChecked())

    def set_range_selected(self, selected: bool) -> None:
        self._range_selected = selected
        self._custom_highlight: str | None = None
        self._update_style(self.isChecked())

    def set_custom_highlight(self, color: str | None) -> None:
        self._custom_highlight = color
        self._update_style(self.isChecked())

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            mods = QApplication.keyboardModifiers()
            if mods & Qt.KeyboardModifier.ShiftModifier:
                self.token_shift_clicked.emit(self.index)
                return
            self.token_clicked.emit(self.index)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.token_drag_entered.emit(self.index)
        super().mouseMoveEvent(e)

    def _update_style(self, selected: bool) -> None:
        custom = getattr(self, "_custom_highlight", None)
        if custom:
            self.setStyleSheet(
                f"QPushButton {{ font-size: 12px; font-weight: bold; "
                f"border: 2px solid {custom}; border-radius: 4px; "
                f"padding: 3px 6px; background: {custom}; color: #1a1a1a; }}"
                f"QPushButton:hover {{ border-color: {custom}; background: {custom}; color: #1a1a1a; }}"
            )
            return
        if self._range_selected:
            self.setStyleSheet(
                "QPushButton { font-size: 12px; font-weight: bold; "
                "border: 2px solid #ffc107; border-radius: 4px; "
                "padding: 3px 6px; background: #ffc107; color: #1a1a1a; }"
                "QPushButton:hover { border-color: #ffca28; background: #ffca28; color: #1a1a1a; }"
            )
            return
        base_size = 14 if selected else 12
        border_color = "#ffc107" if self._locked else ("#00bcd4" if selected else "transparent")
        bg = "#00838f" if selected else "transparent"
        font_weight = "bold" if selected else "normal"
        self.setStyleSheet(
            f"QPushButton {{ font-size: {base_size}px; font-weight: {font_weight}; "
            f"border: 2px solid {border_color}; border-radius: 4px; "
            f"padding: 3px 6px; background: {bg}; }}"
            f"QPushButton:hover {{ border-color: #00bcd4; background: #3a4a4a; }}"
        )


class LyricsPanel(QWidget):
    token_selected = Signal(int)
    lyrics_changed = Signal(str)
    range_selected = Signal(int, int)
    selection_cleared = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        lbl = QLabel("Lyrics Input")
        lbl.setStyleSheet("font-weight: bold; color: #00bcd4;")
        layout.addWidget(lbl)

        self._text_edit = QTextEdit()
        self._text_edit.setToolTip("Type or paste lyrics here, then click Tokenize to split into editable words")
        self._text_edit.setPlaceholderText("Enter lyrics here...")
        self._text_edit.setMaximumHeight(120)
        layout.addWidget(self._text_edit)

        btn_row = QHBoxLayout()
        self._tokenize_btn = QPushButton("Tokenize")
        self._tokenize_btn.setToolTip("Split lyrics into individual word tokens for editing")
        self._tokenize_btn.setStyleSheet(
            "QPushButton { background: #00838f; color: white; font-weight: bold; "
            "border-radius: 6px; padding: 6px 18px; }"
            "QPushButton:hover { background: #00acc1; }"
        )
        btn_row.addWidget(self._tokenize_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        tokens_label = QLabel("Tokens")
        tokens_label.setStyleSheet("font-weight: bold; color: #00bcd4;")
        layout.addWidget(tokens_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(100)
        self._token_container = QWidget()
        self._token_layout = FlowLayout(self._token_container)
        self._token_layout.setSpacing(4)
        scroll.setWidget(self._token_container)
        layout.addWidget(scroll, 1)

        self._token_buttons: list[TokenButton] = []
        self._selected_index: int = -1
        self._anchor_index: int = -1
        self._range_start: int = -1
        self._range_end: int = -1
        self._dragging: bool = False

        self._tokenize_btn.clicked.connect(self._on_tokenize_clicked)

    @property
    def text_edit(self) -> QTextEdit:
        return self._text_edit

    @property
    def tokenize_btn(self) -> QPushButton:
        return self._tokenize_btn

    def get_lyrics_text(self) -> str:
        return self._text_edit.toPlainText()

    def set_lyrics_text(self, text: str) -> None:
        self._text_edit.setPlainText(text)

    def display_tokens(self, words: list[str]) -> None:
        for btn in self._token_buttons:
            self._token_layout.removeWidget(btn)
            btn.deleteLater()
        self._token_buttons.clear()
        self._selected_index = -1
        self._anchor_index = -1
        self._range_start = -1
        self._range_end = -1

        for i, word in enumerate(words):
            btn = TokenButton(word, i)
            btn.token_clicked.connect(self._on_token_clicked)
            btn.token_shift_clicked.connect(self._on_shift_click)
            btn.token_drag_entered.connect(self._on_drag_enter)
            btn.setMouseTracking(True)
            self._token_layout.addWidget(btn)
            self._token_buttons.append(btn)

    def select_token(self, index: int) -> None:
        self._clear_range_highlight()
        if 0 <= self._selected_index < len(self._token_buttons):
            self._token_buttons[self._selected_index].set_selected(False)
        self._selected_index = index
        self._anchor_index = index
        self._range_start = -1
        self._range_end = -1
        if 0 <= index < len(self._token_buttons):
            self._token_buttons[index].set_selected(True)

    def set_range(self, start: int, end: int) -> None:
        self._clear_range_highlight()
        if 0 <= self._selected_index < len(self._token_buttons):
            self._token_buttons[self._selected_index].set_selected(False)
        self._selected_index = start
        lo = min(start, end)
        hi = max(start, end)
        self._range_start = lo
        self._range_end = hi
        for i in range(lo, hi + 1):
            if 0 <= i < len(self._token_buttons):
                self._token_buttons[i].set_range_selected(True)

    def clear_selection(self) -> None:
        self._clear_range_highlight()
        if 0 <= self._selected_index < len(self._token_buttons):
            self._token_buttons[self._selected_index].set_selected(False)
        self._selected_index = -1
        self._anchor_index = -1
        self._range_start = -1
        self._range_end = -1
        self.selection_cleared.emit()

    def has_range(self) -> bool:
        return (self._range_start >= 0 and self._range_end >= 0
                and self._range_start != self._range_end)

    def get_range(self) -> tuple[int, int]:
        return (self._range_start, self._range_end)

    def set_token_locked(self, index: int, locked: bool) -> None:
        if 0 <= index < len(self._token_buttons):
            self._token_buttons[index].set_locked(locked)

    def token_count(self) -> int:
        return len(self._token_buttons)

    def get_token_global_rect(self, index: int) -> QRect | None:
        if 0 <= index < len(self._token_buttons):
            btn = self._token_buttons[index]
            return QRect(btn.mapToGlobal(QPoint(0, 0)), btn.size())
        return None

    def get_range_global_rect(self) -> QRect | None:
        if self._range_start < 0 or self._range_end < 0:
            return None
        first = self.get_token_global_rect(self._range_start)
        last = self.get_token_global_rect(self._range_end)
        if first and last:
            return first.united(last)
        return first or last

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.clear_selection()
            return
        super().keyPressEvent(event)

    def _clear_range_highlight(self) -> None:
        for btn in self._token_buttons:
            btn.set_range_selected(False)

    def _on_token_clicked(self, index: int) -> None:
        self._dragging = True
        self._anchor_index = index
        self.select_token(index)
        self.token_selected.emit(index)

    def _on_shift_click(self, index: int) -> None:
        if self._anchor_index < 0:
            self._anchor_index = 0
        lo = min(self._anchor_index, index)
        hi = max(self._anchor_index, index)
        if lo == hi:
            self.select_token(index)
            self.token_selected.emit(index)
            return
        self.set_range(lo, hi)
        self.range_selected.emit(lo, hi)

    def _on_drag_enter(self, index: int) -> None:
        if not self._dragging:
            return
        if self._anchor_index < 0:
            return
        if index == self._anchor_index:
            self.select_token(index)
            self.token_selected.emit(index)
            return
        lo = min(self._anchor_index, index)
        hi = max(self._anchor_index, index)
        self.set_range(lo, hi)
        self.range_selected.emit(lo, hi)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False
        super().mouseReleaseEvent(event)

    def highlight_tokens(self, indices: list[int], color: str) -> None:
        for i in indices:
            if 0 <= i < len(self._token_buttons):
                self._token_buttons[i].set_custom_highlight(color)

    def clear_highlight(self) -> None:
        for btn in self._token_buttons:
            btn.set_custom_highlight(None)

    def _on_tokenize_clicked(self) -> None:
        self.lyrics_changed.emit(self._text_edit.toPlainText())
