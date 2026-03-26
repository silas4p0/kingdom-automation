from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox,
    QPushButton, QGroupBox, QGridLayout, QButtonGroup,
)
from PySide6.QtCore import Signal, Qt, QPoint
from PySide6.QtGui import QPainter, QColor


class SelectionPopover(QWidget):
    apply_clicked = Signal(dict)
    cancel_clicked = Signal()
    scope_changed = Signal(str)
    mode_changed = Signal(str)
    preview_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            "SelectionPopover {"
            "  background-color: #3a3a3a;"
            "  border: 2px solid #00bcd4;"
            "  border-radius: 8px;"
            "}"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        title = QLabel("Selection Controls")
        title.setStyleSheet(
            "font-weight: bold; color: #00bcd4; font-size: 13px;"
            "background: transparent;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        scope_group = QGroupBox("Preview Scope")
        scope_group.setStyleSheet(
            "QGroupBox { background-color: #333333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; color: #00bcd4; }"
        )
        scope_lay = QHBoxLayout(scope_group)
        self._pop_scope_group = QButtonGroup(self)
        self._pop_scope_group.setExclusive(True)
        self._pop_scope_btns: dict[str, QPushButton] = {}
        for label in ["Word", "From Word", "Line", "Section"]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555;"
                " border-radius: 4px; padding: 4px 8px; font-size: 11px; }"
                "QPushButton:checked { background: #00838f; border-color: #00bcd4; color: #fff; }"
                "QPushButton:hover { border-color: #00bcd4; }"
            )
            self._pop_scope_btns[label] = btn
            self._pop_scope_group.addButton(btn)
            scope_lay.addWidget(btn)
        self._pop_scope_btns["Section"].setChecked(True)
        self._pop_scope_group.buttonClicked.connect(
            lambda btn: self.scope_changed.emit(btn.text())
        )
        root.addWidget(scope_group)

        mode_group = QGroupBox("Preview Mode")
        mode_group.setStyleSheet(
            "QGroupBox { background-color: #333333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; color: #00bcd4; }"
        )
        mode_lay = QHBoxLayout(mode_group)
        self._pop_mode_group = QButtonGroup(self)
        self._pop_mode_group.setExclusive(True)
        self._pop_mode_btns: dict[str, QPushButton] = {}
        btn_style = (
            "QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555;"
            " border-radius: 4px; padding: 4px 8px; font-size: 11px; }"
            "QPushButton:checked { background: #00838f; border-color: #00bcd4; color: #fff; }"
            "QPushButton:hover { border-color: #00bcd4; }"
        )
        for label in ["Single", "Forward", "Assist (Later)"]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(btn_style)
            if label == "Assist (Later)":
                btn.setEnabled(False)
            self._pop_mode_btns[label] = btn
            self._pop_mode_group.addButton(btn)
            mode_lay.addWidget(btn)
        self._pop_mode_btns["Single"].setChecked(True)
        self._pop_mode_group.buttonClicked.connect(
            lambda btn: self.mode_changed.emit(btn.text())
        )
        root.addWidget(mode_group)

        params_group = QGroupBox("Apply Parameters")
        params_group.setStyleSheet(
            "QGroupBox { background-color: #333333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; color: #00bcd4; }"
        )
        params_lay = QVBoxLayout(params_group)

        slider_style = (
            "QSlider::groove:horizontal { height: 4px; background: #555; border-radius: 2px; }"
            "QSlider::handle:horizontal { background: #00bcd4; width: 12px; height: 12px;"
            " margin: -4px 0; border-radius: 6px; }"
        )
        label_style = "color: #e0e0e0; background: transparent; font-size: 11px;"
        cb_style = (
            "QCheckBox { color: #e0e0e0; spacing: 4px; background: transparent; }"
            "QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #555;"
            " border-radius: 3px; background: #444; }"
            "QCheckBox::indicator:checked { background: #00bcd4; border-color: #00bcd4; }"
        )

        self._dur_cb = QCheckBox("Duration")
        self._dur_cb.setToolTip("Include duration in the apply operation")
        self._dur_cb.setStyleSheet(cb_style)
        self._dur_slider = QSlider(Qt.Orientation.Horizontal)
        self._dur_slider.setRange(0, 2000)
        self._dur_slider.setValue(500)
        self._dur_slider.setStyleSheet(slider_style)
        self._dur_slider.setFixedWidth(140)
        self._dur_readout = QLabel("500ms")
        self._dur_readout.setStyleSheet(label_style)
        self._dur_readout.setFixedWidth(48)
        self._dur_slider.valueChanged.connect(
            lambda v: self._dur_readout.setText(f"{v}ms")
        )
        self._dur_slider.sliderReleased.connect(self._on_slider_released)
        row = QHBoxLayout()
        row.addWidget(self._dur_cb)
        row.addWidget(self._dur_slider)
        row.addWidget(self._dur_readout)
        params_lay.addLayout(row)

        self._loud_cb = QCheckBox("Loudness")
        self._loud_cb.setToolTip("Include loudness in the apply operation")
        self._loud_cb.setStyleSheet(cb_style)
        self._loud_slider = QSlider(Qt.Orientation.Horizontal)
        self._loud_slider.setRange(0, 200)
        self._loud_slider.setValue(100)
        self._loud_slider.setStyleSheet(slider_style)
        self._loud_slider.setFixedWidth(140)
        self._loud_readout = QLabel("100%")
        self._loud_readout.setStyleSheet(label_style)
        self._loud_readout.setFixedWidth(48)
        self._loud_slider.valueChanged.connect(
            lambda v: self._loud_readout.setText(f"{v}%")
        )
        self._loud_slider.sliderReleased.connect(self._on_slider_released)
        row = QHBoxLayout()
        row.addWidget(self._loud_cb)
        row.addWidget(self._loud_slider)
        row.addWidget(self._loud_readout)
        params_lay.addLayout(row)

        self._int_cb = QCheckBox("Intensity")
        self._int_cb.setToolTip("Include intensity in the apply operation")
        self._int_cb.setStyleSheet(cb_style)
        self._int_slider = QSlider(Qt.Orientation.Horizontal)
        self._int_slider.setRange(0, 100)
        self._int_slider.setValue(50)
        self._int_slider.setStyleSheet(slider_style)
        self._int_slider.setFixedWidth(140)
        self._int_readout = QLabel("50")
        self._int_readout.setStyleSheet(label_style)
        self._int_readout.setFixedWidth(48)
        self._int_slider.valueChanged.connect(
            lambda v: self._int_readout.setText(str(v))
        )
        self._int_slider.sliderReleased.connect(self._on_slider_released)
        row = QHBoxLayout()
        row.addWidget(self._int_cb)
        row.addWidget(self._int_slider)
        row.addWidget(self._int_readout)
        params_lay.addLayout(row)

        self._pitch_cb = QCheckBox("Pitch Offset")
        self._pitch_cb.setToolTip("Include pitch offset in the apply operation")
        self._pitch_cb.setStyleSheet(cb_style)
        self._pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self._pitch_slider.setRange(-24, 24)
        self._pitch_slider.setValue(0)
        self._pitch_slider.setStyleSheet(slider_style)
        self._pitch_slider.setFixedWidth(140)
        self._pitch_readout = QLabel("0 st")
        self._pitch_readout.setStyleSheet(label_style)
        self._pitch_readout.setFixedWidth(48)
        self._pitch_slider.valueChanged.connect(
            lambda v: self._pitch_readout.setText(f"{v:+d} st")
        )
        self._pitch_slider.sliderReleased.connect(self._on_slider_released)
        row = QHBoxLayout()
        row.addWidget(self._pitch_cb)
        row.addWidget(self._pitch_slider)
        row.addWidget(self._pitch_readout)
        params_lay.addLayout(row)

        root.addWidget(params_group)

        del_group = QGroupBox("Delivery")
        del_group.setStyleSheet(
            "QGroupBox { background-color: #333333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; color: #00bcd4; }"
        )
        del_lay = QGridLayout(del_group)
        self._del_cb = QCheckBox("Apply delivery")
        self._del_cb.setToolTip("Include delivery mode in the apply operation")
        self._del_cb.setStyleSheet(cb_style)
        del_lay.addWidget(self._del_cb, 0, 0, 1, 3)
        self._delivery_buttons: dict[str, QPushButton] = {}
        btn_style = (
            "QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555;"
            " border-radius: 4px; padding: 3px 6px; font-size: 11px; }"
            "QPushButton:checked { background: #00838f; border-color: #00bcd4; color: #fff; }"
            "QPushButton:hover { border-color: #00bcd4; }"
        )
        for i, mode in enumerate(["Whisper", "Normal", "Yell", "Scream", "Bravado"]):
            btn = QPushButton(mode)
            btn.setCheckable(True)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda checked, m=mode: self._on_delivery_clicked(m))
            del_lay.addWidget(btn, 1 + i // 3, i % 3)
            self._delivery_buttons[mode] = btn
        self._delivery_buttons["Normal"].setChecked(True)
        root.addWidget(del_group)

        self._auto_preview_cb = QCheckBox("Auto-preview on release")
        self._auto_preview_cb.setToolTip("Automatically preview audio when a slider is released")
        self._auto_preview_cb.setStyleSheet(cb_style)
        self._auto_preview_cb.setChecked(True)
        root.addWidget(self._auto_preview_cb)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply / OK (Lock)")
        apply_btn.setStyleSheet(
            "QPushButton { background: #00838f; color: white; font-weight: bold;"
            " border-radius: 6px; padding: 6px 16px; }"
            "QPushButton:hover { background: #00acc1; }"
        )
        apply_btn.clicked.connect(self._on_apply)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton { background: #555; color: #e0e0e0;"
            " border-radius: 6px; padding: 6px 16px; }"
            "QPushButton:hover { background: #666; }"
        )
        cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    def _on_delivery_clicked(self, mode: str) -> None:
        for name, btn in self._delivery_buttons.items():
            btn.setChecked(name == mode)

    def _on_slider_released(self) -> None:
        if self._auto_preview_cb.isChecked():
            self.preview_requested.emit()

    def _on_apply(self) -> None:
        result: dict = {}
        if self._dur_cb.isChecked():
            result["duration_ms"] = self._dur_slider.value()
        if self._loud_cb.isChecked():
            result["loudness_pct"] = self._loud_slider.value()
        if self._int_cb.isChecked():
            result["intensity"] = self._int_slider.value()
        if self._pitch_cb.isChecked():
            result["pitch_offset"] = self._pitch_slider.value()
        if self._del_cb.isChecked():
            for name, btn in self._delivery_buttons.items():
                if btn.isChecked():
                    result["delivery"] = name
                    break
        self.apply_clicked.emit(result)

    def _on_cancel(self) -> None:
        self.cancel_clicked.emit()
        self.close()

    def get_scope(self) -> str:
        checked = self._pop_scope_group.checkedButton()
        if checked:
            return checked.text()
        return "Section"

    def set_scope(self, scope: str) -> None:
        btn = self._pop_scope_btns.get(scope)
        if btn:
            btn.setChecked(True)

    def get_mode(self) -> str:
        checked = self._pop_mode_group.checkedButton()
        if checked:
            return checked.text()
        return "Single"

    def set_mode(self, mode: str) -> None:
        btn = self._pop_mode_btns.get(mode)
        if btn:
            btn.setChecked(True)

    def show_at(self, anchor_global: QPoint, avoid_rect_height: int = 0) -> None:
        self.adjustSize()
        sz = self.sizeHint()
        screen = self.screen()
        if screen:
            screen_rect = screen.availableGeometry()
        else:
            screen_rect = None

        x = anchor_global.x()
        y = anchor_global.y() - sz.height() - 8

        if screen_rect and y < screen_rect.top():
            y = anchor_global.y() + avoid_rect_height + 8

        if screen_rect:
            if x + sz.width() > screen_rect.right():
                x = screen_rect.right() - sz.width() - 4
            if x < screen_rect.left():
                x = screen_rect.left() + 4
            if y + sz.height() > screen_rect.bottom():
                y = screen_rect.bottom() - sz.height() - 4

        self.move(x, y)
        self.show()
        self.raise_()
