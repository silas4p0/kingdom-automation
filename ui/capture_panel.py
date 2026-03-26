from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QLineEdit, QGroupBox, QScrollArea, QListWidget, QListWidgetItem,
    QSlider, QSpinBox, QMessageBox, QButtonGroup,
)
from PySide6.QtCore import Signal, Qt, QTimer


class CapturePanel(QWidget):
    record_requested = Signal()
    stop_requested = Signal()
    import_requested = Signal()
    analyze_requested = Signal()
    apply_to_tokens = Signal(dict)
    preview_apply_requested = Signal(dict, str)
    commit_apply_requested = Signal(dict, str)
    revert_preview_requested = Signal()
    use_preset_requested = Signal(str)
    create_new_preset_requested = Signal()
    compare_details_requested = Signal(str)
    preset_created = Signal(str, dict)
    session_preset_accepted = Signal(str)
    session_preset_renamed = Signal(str, str)
    session_finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._recording = False
        self._analysis_result: dict | None = None
        self._mapped_params: dict | None = None
        self._session_active = False
        self._preview_active = False

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        title = QLabel("Performance Capture")
        title.setStyleSheet("font-weight: bold; color: #00bcd4; font-size: 14px;")
        root.addWidget(title)

        btn_style = (
            "QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555;"
            " border-radius: 4px; padding: 5px 12px; font-size: 11px; }"
            "QPushButton:hover { border-color: #00bcd4; background: #555; }"
            "QPushButton:disabled { color: #666; background: #333; }"
        )
        active_btn_style = (
            "QPushButton { background: #b71c1c; color: white; border: 1px solid #e53935;"
            " border-radius: 4px; padding: 5px 12px; font-size: 11px; font-weight: bold; }"
            "QPushButton:hover { background: #c62828; }"
        )

        rec_group = QGroupBox("Capture")
        rec_group.setStyleSheet(
            "QGroupBox { background-color: #333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; }"
        )
        rec_lay = QVBoxLayout(rec_group)

        row1 = QHBoxLayout()
        self._record_btn = QPushButton("Record Sample")
        self._record_btn.setToolTip("Record a vocal sample from the microphone")
        self._record_btn.setStyleSheet(btn_style)
        self._record_btn.clicked.connect(self._on_record_toggle)
        row1.addWidget(self._record_btn)

        self._import_btn = QPushButton("Import Audio File")
        self._import_btn.setToolTip("Import an existing audio file for analysis")
        self._import_btn.setStyleSheet(btn_style)
        self._import_btn.clicked.connect(lambda: self.import_requested.emit())
        row1.addWidget(self._import_btn)
        rec_lay.addLayout(row1)

        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Max Duration:"))
        self._dur_spin = QSpinBox()
        self._dur_spin.setToolTip("Maximum recording duration in seconds")
        self._dur_spin.setRange(1, 30)
        self._dur_spin.setValue(5)
        self._dur_spin.setSuffix("s")
        self._dur_spin.setStyleSheet(
            "QSpinBox { background: #444; color: #e0e0e0; border: 1px solid #555;"
            " border-radius: 3px; padding: 2px 6px; }"
        )
        dur_row.addWidget(self._dur_spin)
        dur_row.addStretch()
        rec_lay.addLayout(dur_row)

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #aaa; font-size: 11px; background: transparent;")
        rec_lay.addWidget(self._status_label)

        self._analyze_btn = QPushButton("Analyze")
        self._analyze_btn.setToolTip("Run DSP analysis on the recorded/imported audio")
        self._analyze_btn.setStyleSheet(
            "QPushButton { background: #00838f; color: white; font-weight: bold;"
            " border-radius: 4px; padding: 5px 16px; }"
            "QPushButton:hover { background: #00acc1; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._analyze_btn.setEnabled(False)
        self._analyze_btn.clicked.connect(lambda: self.analyze_requested.emit())
        rec_lay.addWidget(self._analyze_btn)

        root.addWidget(rec_group)

        results_group = QGroupBox("Analysis Results")
        results_group.setStyleSheet(
            "QGroupBox { background-color: #333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; }"
        )
        results_lay = QVBoxLayout(results_group)

        label_style = "color: #ccc; font-size: 11px; background: transparent;"
        self._rms_label = QLabel("RMS Loudness: --")
        self._rms_label.setStyleSheet(label_style)
        self._peak_label = QLabel("Peak Amplitude: --")
        self._peak_label.setStyleSheet(label_style)
        self._pitch_label = QLabel("Pitch: --")
        self._pitch_label.setStyleSheet(label_style)
        self._vibrato_label = QLabel("Vibrato: --")
        self._vibrato_label.setStyleSheet(label_style)
        self._centroid_label = QLabel("Spectral Centroid: --")
        self._centroid_label.setStyleSheet(label_style)
        self._rolloff_label = QLabel("Spectral Rolloff: --")
        self._rolloff_label.setStyleSheet(label_style)
        self._envelope_label = QLabel("Envelope Duration: --")
        self._envelope_label.setStyleSheet(label_style)

        self._pitch_conf_label = QLabel("Pitch confidence: --")
        self._pitch_conf_label.setStyleSheet(label_style)
        self._vib_conf_label = QLabel("Vibrato confidence: --")
        self._vib_conf_label.setStyleSheet(label_style)
        self._overall_conf_label = QLabel("Overall confidence: --")
        self._overall_conf_label.setStyleSheet("color: #ffc107; font-size: 11px; font-weight: bold; background: transparent;")
        self._conf_warning_label = QLabel("")
        self._conf_warning_label.setStyleSheet("color: #ff5252; font-size: 11px; background: transparent;")
        self._conf_warning_label.setWordWrap(True)
        self._conf_warning_label.setVisible(False)

        for lbl in [self._rms_label, self._peak_label, self._pitch_label,
                     self._vibrato_label, self._centroid_label, self._rolloff_label,
                     self._envelope_label,
                     self._pitch_conf_label, self._vib_conf_label,
                     self._overall_conf_label, self._conf_warning_label]:
            results_lay.addWidget(lbl)

        root.addWidget(results_group)

        mapped_group = QGroupBox("Mapped Parameters")
        mapped_group.setStyleSheet(
            "QGroupBox { background-color: #333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; }"
        )
        mapped_lay = QVBoxLayout(mapped_group)

        self._mapped_loud_label = QLabel("Loudness: --")
        self._mapped_loud_label.setStyleSheet(label_style)
        self._mapped_int_label = QLabel("Intensity: --")
        self._mapped_int_label.setStyleSheet(label_style)
        self._mapped_pitch_label = QLabel("Pitch Offset: --")
        self._mapped_pitch_label.setStyleSheet(label_style)
        self._mapped_dur_label = QLabel("Duration: --")
        self._mapped_dur_label.setStyleSheet(label_style)
        self._mapped_del_label = QLabel("Delivery: --")
        self._mapped_del_label.setStyleSheet(label_style)

        for lbl in [self._mapped_loud_label, self._mapped_int_label,
                     self._mapped_pitch_label, self._mapped_dur_label,
                     self._mapped_del_label]:
            mapped_lay.addWidget(lbl)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Apply Target:"))
        self._target_group = QButtonGroup(self)
        self._target_group.setExclusive(True)
        self._target_btns: dict[str, QPushButton] = {}
        for label in ["Single Word", "Selected Range", "Forward"]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555;"
                " border-radius: 4px; padding: 3px 8px; font-size: 10px; }"
                "QPushButton:checked { background: #00838f; color: white; border-color: #00bcd4; }"
                "QPushButton:hover { border-color: #00bcd4; }"
            )
            self._target_btns[label] = btn
            self._target_group.addButton(btn)
            target_row.addWidget(btn)
        self._target_btns["Single Word"].setChecked(True)
        mapped_lay.addLayout(target_row)

        apply_row = QHBoxLayout()
        self._preview_apply_btn = QPushButton("Preview Apply")
        self._preview_apply_btn.setToolTip("Preview the mapped parameters on tokens before committing")
        self._preview_apply_btn.setStyleSheet(
            "QPushButton { background: #e65100; color: white; font-weight: bold;"
            " border-radius: 4px; padding: 5px 12px; }"
            "QPushButton:hover { background: #f57c00; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._preview_apply_btn.setEnabled(False)
        self._preview_apply_btn.clicked.connect(self._on_preview_apply)
        apply_row.addWidget(self._preview_apply_btn)

        self._commit_btn = QPushButton("Commit Apply")
        self._commit_btn.setToolTip("Lock the previewed parameter changes into tokens")
        self._commit_btn.setStyleSheet(
            "QPushButton { background: #2e7d32; color: white; font-weight: bold;"
            " border-radius: 4px; padding: 5px 12px; }"
            "QPushButton:hover { background: #43a047; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._commit_btn.setEnabled(False)
        self._commit_btn.clicked.connect(self._on_commit_apply)
        apply_row.addWidget(self._commit_btn)

        self._revert_btn = QPushButton("Revert Preview")
        self._revert_btn.setToolTip("Undo the previewed changes and restore original values")
        self._revert_btn.setStyleSheet(
            "QPushButton { background: #b71c1c; color: white; font-weight: bold;"
            " border-radius: 4px; padding: 5px 12px; }"
            "QPushButton:hover { background: #c62828; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._revert_btn.setEnabled(False)
        self._revert_btn.clicked.connect(self._on_revert_preview)
        apply_row.addWidget(self._revert_btn)
        mapped_lay.addLayout(apply_row)

        self._apply_btn = QPushButton("Apply to Selected Tokens")
        self._apply_btn.setToolTip("Apply captured parameters directly to selected tokens")
        self._apply_btn.setStyleSheet(
            "QPushButton { background: #00838f; color: white; font-weight: bold;"
            " border-radius: 4px; padding: 5px 16px; }"
            "QPushButton:hover { background: #00acc1; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._on_apply)
        mapped_lay.addWidget(self._apply_btn)

        root.addWidget(mapped_group)

        match_group = QGroupBox("Closest Matches")
        match_group.setStyleSheet(
            "QGroupBox { background-color: #333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; }"
        )
        match_lay = QVBoxLayout(match_group)

        self._match_status_label = QLabel("No analysis yet")
        self._match_status_label.setStyleSheet("color: #999; font-size: 11px; background: transparent;")
        match_lay.addWidget(self._match_status_label)

        self._match_list = QListWidget()
        self._match_list.setMaximumHeight(80)
        self._match_list.setStyleSheet(
            "QListWidget { background: #2b2b2b; color: #e0e0e0; border: 1px solid #555;"
            " border-radius: 3px; font-size: 11px; }"
            "QListWidget::item { padding: 2px 4px; }"
            "QListWidget::item:selected { background: #00838f; color: white; }"
        )
        match_lay.addWidget(self._match_list)

        match_btn_row = QHBoxLayout()
        self._use_preset_btn = QPushButton("Use Preset")
        self._use_preset_btn.setToolTip("Use the selected matching preset instead of creating a new one")
        self._use_preset_btn.setStyleSheet(
            "QPushButton { background: #00838f; color: white; font-weight: bold;"
            " border-radius: 4px; padding: 4px 10px; font-size: 10px; }"
            "QPushButton:hover { background: #00acc1; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._use_preset_btn.setEnabled(False)
        self._use_preset_btn.clicked.connect(self._on_use_preset)
        match_btn_row.addWidget(self._use_preset_btn)

        self._create_new_btn = QPushButton("New Preset")
        self._create_new_btn.setToolTip("Create a new style preset from this analysis")
        self._create_new_btn.setStyleSheet(
            "QPushButton { background: #e65100; color: white; font-weight: bold;"
            " border-radius: 4px; padding: 4px 10px; font-size: 10px; }"
            "QPushButton:hover { background: #f57c00; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._create_new_btn.setEnabled(False)
        self._create_new_btn.clicked.connect(self._on_create_new_anyway)
        match_btn_row.addWidget(self._create_new_btn)

        self._compare_btn = QPushButton("Compare")
        self._compare_btn.setToolTip("Show per-feature comparison between analysis and selected preset")
        self._compare_btn.setStyleSheet(
            "QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555;"
            " border-radius: 4px; padding: 4px 10px; font-size: 10px; }"
            "QPushButton:hover { border-color: #00bcd4; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._compare_btn.setEnabled(False)
        self._compare_btn.clicked.connect(self._on_compare_details)
        match_btn_row.addWidget(self._compare_btn)
        match_lay.addLayout(match_btn_row)

        root.addWidget(match_group)

        preset_group = QGroupBox("Style Preset")
        preset_group.setStyleSheet(
            "QGroupBox { background-color: #333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; }"
        )
        preset_lay = QVBoxLayout(preset_group)

        cb_style = (
            "QCheckBox { color: #e0e0e0; spacing: 4px; background: transparent; }"
            "QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #555;"
            " border-radius: 3px; background: #444; }"
            "QCheckBox::indicator:checked { background: #00bcd4; border-color: #00bcd4; }"
        )
        self._create_preset_cb = QCheckBox("Create new style preset if unmatched")
        self._create_preset_cb.setToolTip("Automatically create a new preset when no close match is found")
        self._create_preset_cb.setStyleSheet(cb_style)
        self._create_preset_cb.toggled.connect(self._on_preset_cb_toggled)
        preset_lay.addWidget(self._create_preset_cb)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self._preset_name_edit = QLineEdit()
        self._preset_name_edit.setPlaceholderText("Auto-generated if blank")
        self._preset_name_edit.setEnabled(False)
        self._preset_name_edit.setStyleSheet(
            "QLineEdit { background: #444; color: #e0e0e0; border: 1px solid #555;"
            " border-radius: 3px; padding: 3px 6px; }"
            "QLineEdit:disabled { background: #333; color: #666; }"
        )
        name_row.addWidget(self._preset_name_edit)
        preset_lay.addLayout(name_row)

        self._save_preset_btn = QPushButton("Save Preset")
        self._save_preset_btn.setToolTip("Save the current analysis as a named style preset")
        self._save_preset_btn.setStyleSheet(btn_style)
        self._save_preset_btn.setEnabled(False)
        self._save_preset_btn.clicked.connect(self._on_save_preset)
        preset_lay.addWidget(self._save_preset_btn)

        root.addWidget(preset_group)

        session_group = QGroupBox("Style Capture Session")
        session_group.setStyleSheet(
            "QGroupBox { background-color: #333; border: 1px solid #555;"
            " border-radius: 6px; margin-top: 12px; padding: 10px 6px 6px 6px;"
            " font-weight: bold; color: #00bcd4; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " subcontrol-position: top left; padding: 2px 8px; }"
        )
        session_lay = QVBoxLayout(session_group)

        sess_btn_row = QHBoxLayout()
        self._start_session_btn = QPushButton("Start Session")
        self._start_session_btn.setToolTip("Begin a multi-sample capture session")
        self._start_session_btn.setStyleSheet(btn_style)
        self._start_session_btn.clicked.connect(self._on_start_session)
        sess_btn_row.addWidget(self._start_session_btn)

        self._end_session_btn = QPushButton("End Session")
        self._end_session_btn.setToolTip("Finish the current capture session")
        self._end_session_btn.setStyleSheet(btn_style)
        self._end_session_btn.setEnabled(False)
        self._end_session_btn.clicked.connect(self._on_end_session)
        sess_btn_row.addWidget(self._end_session_btn)
        session_lay.addLayout(sess_btn_row)

        self._session_list = QListWidget()
        self._session_list.setStyleSheet(
            "QListWidget { background: #2b2b2b; color: #e0e0e0; border: 1px solid #555;"
            " border-radius: 4px; }"
            "QListWidget::item { padding: 4px; }"
            "QListWidget::item:selected { background: #00838f; color: white; }"
        )
        self._session_list.setMaximumHeight(120)
        session_lay.addWidget(self._session_list)

        sess_action_row = QHBoxLayout()
        self._accept_btn = QPushButton("Accept")
        self._accept_btn.setToolTip("Accept the selected session preset")
        self._accept_btn.setStyleSheet(btn_style)
        self._accept_btn.setEnabled(False)
        self._accept_btn.clicked.connect(self._on_accept_preset)
        sess_action_row.addWidget(self._accept_btn)

        self._rename_btn = QPushButton("Rename")
        self._rename_btn.setToolTip("Rename the selected session preset")
        self._rename_btn.setStyleSheet(btn_style)
        self._rename_btn.setEnabled(False)
        self._rename_btn.clicked.connect(self._on_rename_preset)
        sess_action_row.addWidget(self._rename_btn)

        self._save_all_btn = QPushButton("Save All")
        self._save_all_btn.setToolTip("Save all presets from this session")
        self._save_all_btn.setStyleSheet(btn_style)
        self._save_all_btn.setEnabled(False)
        self._save_all_btn.clicked.connect(self._on_save_all)
        sess_action_row.addWidget(self._save_all_btn)
        session_lay.addLayout(sess_action_row)

        self._session_status = QLabel("No active session")
        self._session_status.setStyleSheet("color: #aaa; font-size: 11px; background: transparent;")
        session_lay.addWidget(self._session_status)

        root.addWidget(session_group)
        root.addStretch()

    @property
    def max_duration_s(self) -> float:
        return float(self._dur_spin.value())

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def set_recording(self, active: bool) -> None:
        self._recording = active
        if active:
            self._record_btn.setText("Stop Recording")
            self._record_btn.setStyleSheet(
                "QPushButton { background: #b71c1c; color: white; border: 1px solid #e53935;"
                " border-radius: 4px; padding: 5px 12px; font-size: 11px; font-weight: bold; }"
                "QPushButton:hover { background: #c62828; }"
            )
            self._import_btn.setEnabled(False)
            self._analyze_btn.setEnabled(False)
        else:
            self._record_btn.setText("Record Sample")
            self._record_btn.setStyleSheet(
                "QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555;"
                " border-radius: 4px; padding: 5px 12px; font-size: 11px; }"
                "QPushButton:hover { border-color: #00bcd4; background: #555; }"
            )
            self._import_btn.setEnabled(True)
            self._analyze_btn.setEnabled(True)

    def display_analysis(self, analysis: dict) -> None:
        self._analysis_result = analysis
        self._rms_label.setText(f"RMS Loudness: {analysis.get('rms_loudness', 0):.4f}")
        self._peak_label.setText(f"Peak Amplitude: {analysis.get('peak_amplitude', 0):.4f}")
        pitch = analysis.get("pitch_hz", 0)
        self._pitch_label.setText(f"Pitch: {pitch:.1f} Hz" if pitch > 0 else "Pitch: undetected")
        vr = analysis.get("vibrato_rate_hz", 0)
        vd = analysis.get("vibrato_depth_cents", 0)
        self._vibrato_label.setText(
            f"Vibrato: {vr:.1f} Hz, {vd:.1f} cents" if vr > 0 else "Vibrato: none detected"
        )
        self._centroid_label.setText(
            f"Spectral Centroid: {analysis.get('spectral_centroid_hz', 0):.0f} Hz"
        )
        self._rolloff_label.setText(
            f"Spectral Rolloff: {analysis.get('spectral_rolloff_hz', 0):.0f} Hz"
        )
        self._envelope_label.setText(
            f"Envelope Duration: {analysis.get('envelope_duration_ms', 0):.0f} ms"
        )

        pc = analysis.get("pitch_confidence", 0)
        vc = analysis.get("vibrato_confidence", 0)
        oc = analysis.get("overall_confidence", 0)
        self._pitch_conf_label.setText(f"Pitch confidence: {pc:.0%}")
        self._vib_conf_label.setText(f"Vibrato confidence: {vc:.0%}")
        self._overall_conf_label.setText(f"Overall confidence: {oc:.0%}")

        warnings: list[str] = []
        if oc < 0.4:
            warnings.append("Low confidence — try re-recording with less noise.")
        if pc < 0.3:
            warnings.append("Pitch unclear — try a longer sample or use an instrument.")
        if analysis.get("envelope_duration_ms", 0) < 200:
            warnings.append("Very short sample — try a longer recording.")
        if warnings:
            self._conf_warning_label.setText("\n".join(warnings))
            self._conf_warning_label.setVisible(True)
        else:
            self._conf_warning_label.setVisible(False)

    def display_closest_matches(self, matches: list[tuple[str, float, dict[str, float]]]) -> None:
        self._match_list.clear()
        self._match_data = matches
        if not matches:
            self._match_status_label.setText("No presets to compare against")
            self._match_status_label.setStyleSheet("color: #999; font-size: 11px; background: transparent;")
            self._use_preset_btn.setEnabled(False)
            self._create_new_btn.setEnabled(True)
            self._compare_btn.setEnabled(False)
            return

        best_score = matches[0][1] if matches else 0
        if best_score >= 0.80:
            self._match_status_label.setText("Likely match found")
            self._match_status_label.setStyleSheet("color: #4caf50; font-size: 11px; font-weight: bold; background: transparent;")
        elif best_score >= 0.60:
            self._match_status_label.setText("Possible match")
            self._match_status_label.setStyleSheet("color: #ffc107; font-size: 11px; font-weight: bold; background: transparent;")
        else:
            self._match_status_label.setText("No close match")
            self._match_status_label.setStyleSheet("color: #ff5252; font-size: 11px; font-weight: bold; background: transparent;")

        for name, score, _deltas in matches:
            tag = ""
            if score >= 0.80:
                tag = " [Likely]"
            elif score >= 0.60:
                tag = " [Possible]"
            item = QListWidgetItem(f"{name} \u2014 {score:.2f}{tag}")
            self._match_list.addItem(item)

        if matches:
            self._match_list.setCurrentRow(0)
        self._use_preset_btn.setEnabled(best_score >= 0.60)
        self._create_new_btn.setEnabled(True)
        self._compare_btn.setEnabled(len(matches) > 0)

    def _on_use_preset(self) -> None:
        row = self._match_list.currentRow()
        if row >= 0 and hasattr(self, "_match_data") and row < len(self._match_data):
            name = self._match_data[row][0]
            self.use_preset_requested.emit(name)

    def _on_create_new_anyway(self) -> None:
        self.create_new_preset_requested.emit()

    def _on_compare_details(self) -> None:
        row = self._match_list.currentRow()
        if row >= 0 and hasattr(self, "_match_data") and row < len(self._match_data):
            name = self._match_data[row][0]
            self.compare_details_requested.emit(name)

    def display_mapped_params(self, params: dict) -> None:
        self._mapped_params = params
        self._mapped_loud_label.setText(f"Loudness: {params.get('loudness_pct', '--')}%")
        self._mapped_int_label.setText(f"Intensity: {params.get('intensity', '--')}")
        self._mapped_pitch_label.setText(f"Pitch Offset: {params.get('pitch_offset', '--')} st")
        self._mapped_dur_label.setText(f"Duration: {params.get('duration_ms', '--')} ms")
        self._mapped_del_label.setText(f"Delivery: {params.get('delivery', '--')}")
        self._apply_btn.setEnabled(True)
        self._preview_apply_btn.setEnabled(True)
        self._save_preset_btn.setEnabled(self._create_preset_cb.isChecked())

    def add_session_preset(self, name: str) -> None:
        item = QListWidgetItem(name)
        self._session_list.addItem(item)
        self._session_list.setCurrentItem(item)

    def clear_session_list(self) -> None:
        self._session_list.clear()

    def _on_record_toggle(self) -> None:
        if self._recording:
            self.stop_requested.emit()
        else:
            self.record_requested.emit()

    def _on_preset_cb_toggled(self, checked: bool) -> None:
        self._preset_name_edit.setEnabled(checked)
        self._save_preset_btn.setEnabled(checked and self._mapped_params is not None)

    def get_apply_target(self) -> str:
        for label, btn in self._target_btns.items():
            if btn.isChecked():
                return label
        return "Single Word"

    def set_default_target(self, has_range: bool) -> None:
        if has_range:
            self._target_btns["Selected Range"].setChecked(True)
        else:
            self._target_btns["Single Word"].setChecked(True)

    def set_preview_active(self, active: bool) -> None:
        self._preview_active = active
        self._commit_btn.setEnabled(active)
        self._revert_btn.setEnabled(active)
        self._preview_apply_btn.setEnabled(not active and self._mapped_params is not None)
        self._apply_btn.setEnabled(not active and self._mapped_params is not None)

    def _on_preview_apply(self) -> None:
        if self._mapped_params:
            self.preview_apply_requested.emit(self._mapped_params, self.get_apply_target())

    def _on_commit_apply(self) -> None:
        if self._mapped_params:
            self.commit_apply_requested.emit(self._mapped_params, self.get_apply_target())

    def _on_revert_preview(self) -> None:
        self.revert_preview_requested.emit()

    def _on_apply(self) -> None:
        if self._mapped_params:
            self.apply_to_tokens.emit(self._mapped_params)

    def _on_save_preset(self) -> None:
        if not self._mapped_params:
            return
        name = self._preset_name_edit.text().strip()
        self.preset_created.emit(name, self._mapped_params)

    def _on_start_session(self) -> None:
        self._session_active = True
        self._start_session_btn.setEnabled(False)
        self._end_session_btn.setEnabled(True)
        self._accept_btn.setEnabled(True)
        self._rename_btn.setEnabled(True)
        self._save_all_btn.setEnabled(True)
        self._session_list.clear()
        self._session_status.setText("Session active - record samples and analyze")
        self._create_preset_cb.setChecked(True)

    def _on_end_session(self) -> None:
        self._session_active = False
        self._start_session_btn.setEnabled(True)
        self._end_session_btn.setEnabled(False)
        self._accept_btn.setEnabled(False)
        self._rename_btn.setEnabled(False)
        self._save_all_btn.setEnabled(False)
        self._session_status.setText("Session ended")
        self.session_finished.emit()

    def _on_accept_preset(self) -> None:
        item = self._session_list.currentItem()
        if item:
            self.session_preset_accepted.emit(item.text())

    def _on_rename_preset(self) -> None:
        item = self._session_list.currentItem()
        if not item:
            return
        old_name = item.text()
        new_name = self._preset_name_edit.text().strip()
        if new_name and new_name != old_name:
            item.setText(new_name)
            self.session_preset_renamed.emit(old_name, new_name)

    def _on_save_all(self) -> None:
        for i in range(self._session_list.count()):
            item = self._session_list.item(i)
            if item:
                self.session_preset_accepted.emit(item.text())
        self._session_status.setText(f"Saved {self._session_list.count()} presets")

    @property
    def is_session_active(self) -> bool:
        return self._session_active
