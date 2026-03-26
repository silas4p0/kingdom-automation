from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QComboBox,
    QGroupBox, QPushButton, QGridLayout,
)
from PySide6.QtCore import Signal, Qt


class GlobalControlsPanel(QWidget):
    tempo_changed = Signal(int)
    key_changed = Signal(str)
    voice_type_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        title = QLabel("Global Controls")
        title.setStyleSheet("font-weight: bold; color: #00bcd4; font-size: 14px;")
        layout.addWidget(title)

        tempo_group = QGroupBox("Tempo")
        tempo_lay = QVBoxLayout(tempo_group)
        tempo_top = QHBoxLayout()
        tempo_top.addWidget(QLabel("40"))
        tempo_top.addStretch()
        self._tempo_readout = QLabel("120 BPM")
        tempo_top.addWidget(self._tempo_readout)
        tempo_top.addStretch()
        tempo_top.addWidget(QLabel("240"))
        tempo_lay.addLayout(tempo_top)
        self._tempo_slider = QSlider(Qt.Orientation.Horizontal)
        self._tempo_slider.setToolTip("Global tempo for the performance (40-240 BPM)")
        self._tempo_slider.setRange(40, 240)
        self._tempo_slider.setValue(120)
        self._tempo_slider.valueChanged.connect(self._on_tempo)
        tempo_lay.addWidget(self._tempo_slider)
        layout.addWidget(tempo_group)

        key_group = QGroupBox("Key")
        key_lay = QVBoxLayout(key_group)
        self._key_combo = QComboBox()
        self._key_combo.setToolTip("Musical key for the performance")
        keys = [
            "C Major", "C Minor", "C# Major", "C# Minor",
            "D Major", "D Minor", "Eb Major", "Eb Minor",
            "E Major", "E Minor", "F Major", "F Minor",
            "F# Major", "F# Minor", "G Major", "G Minor",
            "Ab Major", "Ab Minor", "A Major", "A Minor",
            "Bb Major", "Bb Minor", "B Major", "B Minor",
        ]
        self._key_combo.addItems(keys)
        self._key_combo.currentTextChanged.connect(self._on_key)
        key_lay.addWidget(self._key_combo)
        layout.addWidget(key_group)

        vt_group = QGroupBox("Voice Type (Preview)")
        vt_lay = QVBoxLayout(vt_group)
        self._voice_type_combo = QComboBox()
        self._voice_type_combo.setToolTip("Voice type used for audio preview synthesis")
        self._voice_type_combo.addItems(["Male", "Female", "Robot", "Family Bathroom", "Muted Percussive Piano"])
        self._voice_type_combo.currentTextChanged.connect(self._on_voice_type)
        vt_lay.addWidget(self._voice_type_combo)
        layout.addWidget(vt_group)

        inst_group = QGroupBox("Instrument Layers")
        inst_lay = QVBoxLayout(inst_group)
        notice = QLabel("Instrument layer controls not yet implemented")
        notice.setStyleSheet("color: #ffc107; font-style: italic; padding: 4px;")
        notice.setWordWrap(True)
        inst_lay.addWidget(notice)
        inst_grid = QGridLayout()
        layer_names = ["Piano", "Strings", "Synth Pad", "Drums"]
        self._layer_btns: dict[str, QPushButton] = {}
        for i, name in enumerate(layer_names):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setEnabled(False)
            inst_grid.addWidget(btn, i // 2, i % 2)
            self._layer_btns[name] = btn
        inst_lay.addLayout(inst_grid)
        layout.addWidget(inst_group)

        voice_mod_group = QGroupBox("Voice Modifier Overlays")
        voice_mod_lay = QVBoxLayout(voice_mod_group)
        mod_notice = QLabel("Voice modifier overlays not yet implemented")
        mod_notice.setStyleSheet("color: #ffc107; font-style: italic; padding: 4px;")
        mod_notice.setWordWrap(True)
        voice_mod_lay.addWidget(mod_notice)
        mod_grid = QGridLayout()
        mod_names = ["Reverb", "Chorus", "Delay", "Distortion"]
        self._mod_btns: dict[str, QPushButton] = {}
        for i, name in enumerate(mod_names):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setEnabled(False)
            mod_grid.addWidget(btn, i // 2, i % 2)
            self._mod_btns[name] = btn
        voice_mod_lay.addLayout(mod_grid)
        layout.addWidget(voice_mod_group)

        layout.addStretch()

    def _on_tempo(self, val: int) -> None:
        self._tempo_readout.setText(f"{val} BPM")
        self.tempo_changed.emit(val)

    def _on_key(self, key: str) -> None:
        self.key_changed.emit(key)

    def get_tempo(self) -> int:
        return self._tempo_slider.value()

    def get_key(self) -> str:
        return self._key_combo.currentText()

    def set_tempo(self, val: int) -> None:
        self._tempo_slider.blockSignals(True)
        self._tempo_slider.setValue(val)
        self._tempo_slider.blockSignals(False)
        self._tempo_readout.setText(f"{val} BPM")

    def set_key(self, key: str) -> None:
        self._key_combo.blockSignals(True)
        self._key_combo.setCurrentText(key)
        self._key_combo.blockSignals(False)

    def _on_voice_type(self, vtype: str) -> None:
        self.voice_type_changed.emit(vtype)

    def get_voice_type(self) -> str:
        return self._voice_type_combo.currentText()

    def set_voice_type(self, vtype: str) -> None:
        self._voice_type_combo.blockSignals(True)
        self._voice_type_combo.setCurrentText(vtype)
        self._voice_type_combo.blockSignals(False)
