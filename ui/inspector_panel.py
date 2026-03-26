from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton,
    QGroupBox, QGridLayout,
)
from PySide6.QtCore import Signal, Qt


class InspectorPanel(QWidget):
    duration_changed = Signal(int)
    loudness_changed = Signal(int)
    intensity_changed = Signal(int)
    pitch_offset_changed = Signal(int)
    slider_released = Signal()
    delivery_changed = Signal(str)
    bravado_subtype_changed = Signal(str)
    ok_clicked = Signal()
    cancel_clicked = Signal()
    next_clicked = Signal()
    prev_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        title = QLabel("Word Inspector")
        title.setStyleSheet("font-weight: bold; color: #00bcd4; font-size: 14px;")
        layout.addWidget(title)

        self._word_label = QLabel("(no token selected)")
        self._word_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        self._word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._word_label)

        dur_group = QGroupBox("Duration")
        dur_lay = QVBoxLayout(dur_group)
        dur_top = QHBoxLayout()
        dur_top.addWidget(QLabel("0ms"))
        dur_top.addStretch()
        self._dur_readout = QLabel("500ms")
        dur_top.addWidget(self._dur_readout)
        dur_top.addStretch()
        dur_top.addWidget(QLabel("2000ms"))
        dur_lay.addLayout(dur_top)
        self._dur_slider = QSlider(Qt.Orientation.Horizontal)
        self._dur_slider.setToolTip("How long the word sounds (0-2000ms)")
        self._dur_slider.setRange(0, 2000)
        self._dur_slider.setValue(500)
        self._dur_slider.valueChanged.connect(self._on_duration)
        self._dur_slider.sliderReleased.connect(self._on_slider_released)
        dur_lay.addWidget(self._dur_slider)
        layout.addWidget(dur_group)

        loud_group = QGroupBox("Loudness")
        loud_lay = QVBoxLayout(loud_group)
        loud_top = QHBoxLayout()
        loud_top.addWidget(QLabel("0%"))
        loud_top.addStretch()
        self._loud_readout = QLabel("100%")
        loud_top.addWidget(self._loud_readout)
        loud_top.addStretch()
        loud_top.addWidget(QLabel("200%"))
        loud_lay.addLayout(loud_top)
        self._loud_slider = QSlider(Qt.Orientation.Horizontal)
        self._loud_slider.setToolTip("Volume level for this token (0-200%)")
        self._loud_slider.setRange(0, 200)
        self._loud_slider.setValue(100)
        self._loud_slider.valueChanged.connect(self._on_loudness)
        self._loud_slider.sliderReleased.connect(self._on_slider_released)
        loud_lay.addWidget(self._loud_slider)
        layout.addWidget(loud_group)

        int_group = QGroupBox("Intensity")
        int_lay = QVBoxLayout(int_group)
        int_top = QHBoxLayout()
        int_top.addWidget(QLabel("0"))
        int_top.addStretch()
        self._int_readout = QLabel("50")
        int_top.addWidget(self._int_readout)
        int_top.addStretch()
        int_top.addWidget(QLabel("100"))
        int_lay.addLayout(int_top)
        self._int_slider = QSlider(Qt.Orientation.Horizontal)
        self._int_slider.setToolTip("Vocal energy and effort (0 = soft, 100 = maximum)")
        self._int_slider.setRange(0, 100)
        self._int_slider.setValue(50)
        self._int_slider.valueChanged.connect(self._on_intensity)
        self._int_slider.sliderReleased.connect(self._on_slider_released)
        int_lay.addWidget(self._int_slider)
        layout.addWidget(int_group)

        pitch_group = QGroupBox("Pitch Offset")
        pitch_lay = QVBoxLayout(pitch_group)
        pitch_top = QHBoxLayout()
        pitch_top.addWidget(QLabel("-24"))
        pitch_top.addStretch()
        self._pitch_readout = QLabel("0 st")
        pitch_top.addWidget(self._pitch_readout)
        pitch_top.addStretch()
        pitch_top.addWidget(QLabel("+24"))
        pitch_lay.addLayout(pitch_top)
        self._pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self._pitch_slider.setToolTip("Semitone shift from base pitch (-24 to +24)")
        self._pitch_slider.setRange(-24, 24)
        self._pitch_slider.setValue(0)
        self._pitch_slider.valueChanged.connect(self._on_pitch_offset)
        self._pitch_slider.sliderReleased.connect(self._on_slider_released)
        pitch_lay.addWidget(self._pitch_slider)
        layout.addWidget(pitch_group)

        del_group = QGroupBox("Delivery")
        del_lay = QGridLayout(del_group)
        self._delivery_buttons: dict[str, QPushButton] = {}
        delivery_modes = ["Whisper", "Normal", "Yell", "Scream", "Bravado"]
        for i, mode in enumerate(delivery_modes):
            btn = QPushButton(mode)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self._on_delivery(m))
            del_lay.addWidget(btn, i // 3, i % 3)
            self._delivery_buttons[mode] = btn
        self._delivery_buttons["Normal"].setChecked(True)
        layout.addWidget(del_group)

        self._bravado_group = QGroupBox("Bravado Subtype")
        brav_lay = QGridLayout(self._bravado_group)
        self._bravado_buttons: dict[str, QPushButton] = {}
        subtypes = ["Confident", "Aggressive", "Triumphant", "Defiant"]
        for i, sub in enumerate(subtypes):
            btn = QPushButton(sub)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, s=sub: self._on_bravado_sub(s))
            brav_lay.addWidget(btn, i // 2, i % 2)
            self._bravado_buttons[sub] = btn
        self._bravado_buttons["Confident"].setChecked(True)
        self._bravado_group.setVisible(False)
        layout.addWidget(self._bravado_group)

        layout.addStretch()

        nav_group = QGroupBox("Navigation")
        nav_lay = QGridLayout(nav_group)
        self._ok_btn = QPushButton("OK (Lock)")
        self._ok_btn.setToolTip("Lock this token with current settings and move on")
        self._ok_btn.setStyleSheet(
            "QPushButton { background: #00838f; color: white; font-weight: bold; }"
        )
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setToolTip("Revert changes to this token")
        self._prev_btn = QPushButton("< Previous")
        self._prev_btn.setToolTip("Select the previous token")
        self._next_btn = QPushButton("Next >")
        self._next_btn.setToolTip("Select the next token")
        nav_lay.addWidget(self._prev_btn, 0, 0)
        nav_lay.addWidget(self._next_btn, 0, 1)
        nav_lay.addWidget(self._ok_btn, 1, 0)
        nav_lay.addWidget(self._cancel_btn, 1, 1)
        layout.addWidget(nav_group)

        self._ok_btn.clicked.connect(self.ok_clicked.emit)
        self._cancel_btn.clicked.connect(self.cancel_clicked.emit)
        self._next_btn.clicked.connect(self.next_clicked.emit)
        self._prev_btn.clicked.connect(self.prev_clicked.emit)

        self.set_enabled(False)

    def set_enabled(self, enabled: bool) -> None:
        self._dur_slider.setEnabled(enabled)
        self._loud_slider.setEnabled(enabled)
        self._int_slider.setEnabled(enabled)
        self._pitch_slider.setEnabled(enabled)
        for btn in self._delivery_buttons.values():
            btn.setEnabled(enabled)
        for btn in self._bravado_buttons.values():
            btn.setEnabled(enabled)
        self._ok_btn.setEnabled(enabled)
        self._cancel_btn.setEnabled(enabled)
        self._next_btn.setEnabled(enabled)
        self._prev_btn.setEnabled(enabled)

    def display_token(self, word: str, duration: int, loudness: int,
                      intensity: int, pitch_offset: int,
                      delivery: str, bravado_sub: str) -> None:
        self._word_label.setText(word)
        self._dur_slider.blockSignals(True)
        self._dur_slider.setValue(duration)
        self._dur_slider.blockSignals(False)
        self._dur_readout.setText(f"{duration}ms")

        self._loud_slider.blockSignals(True)
        self._loud_slider.setValue(loudness)
        self._loud_slider.blockSignals(False)
        self._loud_readout.setText(f"{loudness}%")

        self._int_slider.blockSignals(True)
        self._int_slider.setValue(intensity)
        self._int_slider.blockSignals(False)
        self._int_readout.setText(str(intensity))

        self._pitch_slider.blockSignals(True)
        self._pitch_slider.setValue(pitch_offset)
        self._pitch_slider.blockSignals(False)
        self._pitch_readout.setText(f"{pitch_offset:+d} st")

        for name, btn in self._delivery_buttons.items():
            btn.setChecked(name == delivery)
        self._bravado_group.setVisible(delivery == "Bravado")

        for name, btn in self._bravado_buttons.items():
            btn.setChecked(name == bravado_sub)

        self.set_enabled(True)

    def clear_display(self) -> None:
        self._word_label.setText("(no token selected)")
        self._dur_slider.setValue(500)
        self._loud_slider.setValue(100)
        self._int_slider.setValue(50)
        self._pitch_slider.setValue(0)
        self._dur_readout.setText("500ms")
        self._loud_readout.setText("100%")
        self._int_readout.setText("50")
        self._pitch_readout.setText("0 st")
        for btn in self._delivery_buttons.values():
            btn.setChecked(False)
        self._delivery_buttons["Normal"].setChecked(True)
        self._bravado_group.setVisible(False)
        self.set_enabled(False)

    def _on_duration(self, val: int) -> None:
        self._dur_readout.setText(f"{val}ms")
        self.duration_changed.emit(val)

    def _on_loudness(self, val: int) -> None:
        self._loud_readout.setText(f"{val}%")
        self.loudness_changed.emit(val)

    def _on_delivery(self, mode: str) -> None:
        for name, btn in self._delivery_buttons.items():
            btn.setChecked(name == mode)
        self._bravado_group.setVisible(mode == "Bravado")
        self.delivery_changed.emit(mode)

    def _on_intensity(self, val: int) -> None:
        self._int_readout.setText(str(val))
        self.intensity_changed.emit(val)

    def _on_pitch_offset(self, val: int) -> None:
        self._pitch_readout.setText(f"{val:+d} st")
        self.pitch_offset_changed.emit(val)

    def _on_slider_released(self) -> None:
        self.slider_released.emit()

    def _on_bravado_sub(self, sub: str) -> None:
        for name, btn in self._bravado_buttons.items():
            btn.setChecked(name == sub)
        self.bravado_subtype_changed.emit(sub)
