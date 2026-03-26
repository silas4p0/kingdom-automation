from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QSlider, QLineEdit, QCheckBox, QComboBox,
    QSpinBox, QDoubleSpinBox,
)
from PySide6.QtCore import Qt, Signal

from models.instrument_patch import InstrumentPatch


class InstrumentEditorDialog(QDialog):
    audition_requested = Signal(dict)

    def __init__(self, patch: InstrumentPatch, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Instrument Editor — {patch.name}")
        self.setMinimumSize(520, 580)
        self._patch = InstrumentPatch.from_dict(patch.to_dict())
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setToolTip("Instrument patch name")
        name_row.addWidget(self._name_edit)
        layout.addLayout(name_row)

        env_group = QGroupBox("Envelope (ADSR)")
        env_form = QFormLayout(env_group)
        self._attack = self._make_dbl_spin(0.1, 500.0, 1, " ms")
        self._attack.setToolTip("Time for sound to reach peak level")
        self._decay = self._make_dbl_spin(1.0, 2000.0, 1, " ms")
        self._decay.setToolTip("Time for sound to drop from peak to sustain level")
        self._sustain = self._make_dbl_spin(0.0, 1.0, 0.01, "")
        self._sustain.setToolTip("Held volume level while note is sustained (0-1)")
        self._release = self._make_dbl_spin(1.0, 2000.0, 1, " ms")
        self._release.setToolTip("Time for sound to fade out after note ends")
        env_form.addRow("Attack:", self._attack)
        env_form.addRow("Decay:", self._decay)
        env_form.addRow("Sustain Level:", self._sustain)
        env_form.addRow("Release:", self._release)
        layout.addWidget(env_group)

        timbre_group = QGroupBox("Timbre / Damping")
        timbre_form = QFormLayout(timbre_group)
        self._damping = self._make_dbl_spin(0.0, 1.0, 0.01, "")
        self._damping.setToolTip("String/resonance damping factor (higher = more muted)")
        self._harmonics = self._make_dbl_spin(0.0, 1.0, 0.01, "")
        self._harmonics.setToolTip("Overtone richness (0 = pure sine, 1 = full harmonic series)")
        self._lowpass = self._make_dbl_spin(100.0, 20000.0, 10, " Hz")
        self._lowpass.setToolTip("Low-pass filter cutoff frequency in Hz")
        self._brightness = self._make_dbl_spin(0.0, 1.0, 0.01, "")
        self._brightness.setToolTip("Overall tonal brightness (0 = dark, 1 = bright)")
        timbre_form.addRow("Damping:", self._damping)
        timbre_form.addRow("Harmonics Level:", self._harmonics)
        timbre_form.addRow("Lowpass Hz:", self._lowpass)
        timbre_form.addRow("Brightness:", self._brightness)
        layout.addWidget(timbre_group)

        noise_group = QGroupBox("Noise / Transient")
        noise_form = QFormLayout(noise_group)
        self._noise = self._make_dbl_spin(0.0, 1.0, 0.01, "")
        self._noise.setToolTip("Amount of breath/noise mixed into the sound")
        self._click = self._make_dbl_spin(0.0, 1.0, 0.01, "")
        self._click.setToolTip("Transient click intensity at note onset")
        noise_form.addRow("Noise Amount:", self._noise)
        noise_form.addRow("Transient Click:", self._click)
        layout.addWidget(noise_group)

        defaults_group = QGroupBox("Token Defaults")
        defaults_form = QFormLayout(defaults_group)
        self._dur_min = QSpinBox()
        self._dur_min.setToolTip("Minimum token duration for this instrument")
        self._dur_min.setRange(10, 5000)
        self._dur_min.setSuffix(" ms")
        self._dur_max = QSpinBox()
        self._dur_max.setToolTip("Maximum token duration for this instrument")
        self._dur_max.setRange(10, 5000)
        self._dur_max.setSuffix(" ms")
        self._def_intensity = QSpinBox()
        self._def_intensity.setToolTip("Default intensity applied to tokens using this instrument")
        self._def_intensity.setRange(0, 100)
        self._delivery_combo = QComboBox()
        self._delivery_combo.setToolTip("Default delivery mode for tokens using this instrument")
        self._delivery_combo.addItems(["Normal", "Whisper", "Yell", "Scream", "Bravado"])
        self._vibrato_cb = QCheckBox("Vibrato ON")
        self._vibrato_cb.setToolTip("Enable vibrato by default for this instrument")
        defaults_form.addRow("Duration Min:", self._dur_min)
        defaults_form.addRow("Duration Max:", self._dur_max)
        defaults_form.addRow("Intensity:", self._def_intensity)
        defaults_form.addRow("Delivery:", self._delivery_combo)
        defaults_form.addRow("", self._vibrato_cb)
        layout.addWidget(defaults_group)

        btn_row = QHBoxLayout()
        self._audition_btn = QPushButton("Audition")
        self._audition_btn.setToolTip("Preview how this instrument sounds with current settings")
        self._audition_btn.setStyleSheet("background: #00695c; color: white; padding: 4px 12px;")
        self._audition_btn.clicked.connect(self._on_audition)
        btn_row.addWidget(self._audition_btn)
        btn_row.addStretch()
        self._ok_btn = QPushButton("OK")
        self._ok_btn.clicked.connect(self.accept)
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._ok_btn)
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)

    def _make_dbl_spin(self, lo: float, hi: float, step: float, suffix: str) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(lo, hi)
        sb.setSingleStep(step)
        sb.setSuffix(suffix)
        sb.setDecimals(2 if step < 1 else 1)
        return sb

    def _populate(self) -> None:
        p = self._patch
        self._name_edit.setText(p.name)
        self._attack.setValue(p.attack_ms)
        self._decay.setValue(p.decay_ms)
        self._sustain.setValue(p.sustain_level)
        self._release.setValue(p.release_ms)
        self._damping.setValue(p.damping)
        self._harmonics.setValue(p.harmonics_level)
        self._lowpass.setValue(p.lowpass_hz)
        self._brightness.setValue(p.brightness)
        self._noise.setValue(p.noise_amount)
        self._click.setValue(p.transient_click)
        self._dur_min.setValue(p.default_duration_ms_min)
        self._dur_max.setValue(p.default_duration_ms_max)
        self._def_intensity.setValue(p.default_intensity)
        idx = self._delivery_combo.findText(p.default_delivery_mode)
        if idx >= 0:
            self._delivery_combo.setCurrentIndex(idx)
        self._vibrato_cb.setChecked(p.default_vibrato_on)

    def _read_back(self) -> None:
        p = self._patch
        p.name = self._name_edit.text().strip() or "Untitled"
        p.attack_ms = self._attack.value()
        p.decay_ms = self._decay.value()
        p.sustain_level = self._sustain.value()
        p.release_ms = self._release.value()
        p.damping = self._damping.value()
        p.harmonics_level = self._harmonics.value()
        p.lowpass_hz = self._lowpass.value()
        p.brightness = self._brightness.value()
        p.noise_amount = self._noise.value()
        p.transient_click = self._click.value()
        p.default_duration_ms_min = self._dur_min.value()
        p.default_duration_ms_max = self._dur_max.value()
        p.default_intensity = self._def_intensity.value()
        p.default_delivery_mode = self._delivery_combo.currentText()
        p.default_vibrato_on = self._vibrato_cb.isChecked()

    def _on_audition(self) -> None:
        self._read_back()
        self.audition_requested.emit(self._patch.to_dict())

    def get_patch(self) -> InstrumentPatch:
        self._read_back()
        return self._patch
