from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QListWidget, QListWidgetItem, QGroupBox,
    QLineEdit, QFormLayout, QDialog, QDialogButtonBox, QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from typing import Any

from models.reference_template import EMOTIONAL_TONES


class ReferencePanelUI(QWidget):
    import_reference = Signal()
    import_vocal_stem = Signal()
    extract_template = Signal()
    apply_template = Signal(str)
    reapply_to_selection = Signal(str)
    switch_tone = Signal(str, str)
    create_from_template = Signal(str)
    create_from_family = Signal(str)
    reference_mode_changed = Signal(str)
    manage_families_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Reference Templates")
        header.setStyleSheet("font-weight: bold; color: #00bcd4;")
        layout.addWidget(header)

        import_row = QHBoxLayout()
        self._import_ref_btn = QPushButton("Import Ref")
        self._import_ref_btn.setToolTip("Import reference song (wav/mp3/m4a)")
        self._import_ref_btn.setStyleSheet(
            "background: #7b1fa2; color: white; padding: 4px 8px; border-radius: 3px;"
        )
        self._import_stem_btn = QPushButton("Import Stem")
        self._import_stem_btn.setToolTip("Import vocal stem (optional)")
        self._import_stem_btn.setStyleSheet(
            "background: #5c6bc0; color: white; padding: 4px 8px; border-radius: 3px;"
        )
        import_row.addWidget(self._import_ref_btn)
        import_row.addWidget(self._import_stem_btn)
        layout.addLayout(import_row)

        self._ref_label = QLabel("No reference loaded")
        self._ref_label.setStyleSheet("font-size: 11px; color: #aaa;")
        self._ref_label.setWordWrap(True)
        layout.addWidget(self._ref_label)

        self._stem_label = QLabel("")
        self._stem_label.setStyleSheet("font-size: 11px; color: #aaa;")
        self._stem_label.setWordWrap(True)
        layout.addWidget(self._stem_label)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self._mode_combo = QComboBox()
        self._mode_combo.setToolTip("Analysis mode: Master Mix, Vocal Stem only, or both")
        self._mode_combo.addItems(["Master Mix", "Vocal Stem", "Dual"])
        mode_row.addWidget(self._mode_combo)
        layout.addLayout(mode_row)

        tone_row = QHBoxLayout()
        tone_row.addWidget(QLabel("Tone:"))
        self._tone_combo = QComboBox()
        self._tone_combo.setToolTip("Emotional tone to tag the extracted template with")
        self._tone_combo.setEditable(True)
        for tone in EMOTIONAL_TONES:
            self._tone_combo.addItem(tone)
        tone_row.addWidget(self._tone_combo)
        layout.addLayout(tone_row)

        self._extract_btn = QPushButton("Extract Template")
        self._extract_btn.setToolTip("Analyze the reference audio and create a performance template")
        self._extract_btn.setStyleSheet(
            "background: #00897b; color: white; padding: 6px; border-radius: 3px; font-weight: bold;"
        )
        layout.addWidget(self._extract_btn)

        tpl_header = QLabel("Templates")
        tpl_header.setStyleSheet("font-weight: bold; color: #00bcd4; font-size: 12px;")
        layout.addWidget(tpl_header)

        self._template_list = QListWidget()
        self._template_list.setMaximumHeight(100)
        self._template_list.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._template_list)

        tpl_actions = QHBoxLayout()
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setToolTip("Apply selected template to new lyrics")
        self._apply_btn.setStyleSheet("background: #e65100; color: white; padding: 3px 6px; border-radius: 3px;")
        self._reapply_btn = QPushButton("Reapply")
        self._reapply_btn.setToolTip("Reapply template to current selection")
        self._reapply_btn.setStyleSheet("padding: 3px 6px;")
        tpl_actions.addWidget(self._apply_btn)
        tpl_actions.addWidget(self._reapply_btn)
        layout.addLayout(tpl_actions)

        tone_switch_row = QHBoxLayout()
        tone_switch_row.addWidget(QLabel("Switch to:"))
        self._switch_tone_combo = QComboBox()
        self._switch_tone_combo.setEditable(True)
        for tone in EMOTIONAL_TONES:
            self._switch_tone_combo.addItem(tone)
        self._switch_tone_btn = QPushButton("Switch")
        self._switch_tone_btn.setToolTip("Switch emotional tone without breaking family structure")
        self._switch_tone_btn.setStyleSheet("padding: 3px 6px;")
        tone_switch_row.addWidget(self._switch_tone_combo)
        tone_switch_row.addWidget(self._switch_tone_btn)
        layout.addLayout(tone_switch_row)

        create_header = QLabel("Create From")
        create_header.setStyleSheet("font-weight: bold; color: #00bcd4; font-size: 12px;")
        layout.addWidget(create_header)

        create_row = QHBoxLayout()
        self._create_tpl_btn = QPushButton("Template")
        self._create_tpl_btn.setToolTip("Create new song from selected template")
        self._create_tpl_btn.setStyleSheet("background: #1565c0; color: white; padding: 3px 6px; border-radius: 3px;")
        self._create_fam_btn = QPushButton("Family")
        self._create_fam_btn.setToolTip("Create new song from selected family averages")
        self._create_fam_btn.setStyleSheet("background: #1565c0; color: white; padding: 3px 6px; border-radius: 3px;")
        create_row.addWidget(self._create_tpl_btn)
        create_row.addWidget(self._create_fam_btn)
        layout.addLayout(create_row)

        self._manage_fam_btn = QPushButton("Manage Families")
        self._manage_fam_btn.setToolTip("Create, rename, delete, and assign templates to families")
        self._manage_fam_btn.setStyleSheet("padding: 4px 8px;")
        layout.addWidget(self._manage_fam_btn)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-size: 11px; color: #4caf50;")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        layout.addStretch()

        self._import_ref_btn.clicked.connect(self.import_reference.emit)
        self._import_stem_btn.clicked.connect(self.import_vocal_stem.emit)
        self._extract_btn.clicked.connect(self.extract_template.emit)
        self._mode_combo.currentTextChanged.connect(self.reference_mode_changed.emit)
        self._apply_btn.clicked.connect(self._on_apply)
        self._reapply_btn.clicked.connect(self._on_reapply)
        self._switch_tone_btn.clicked.connect(self._on_switch_tone)
        self._create_tpl_btn.clicked.connect(self._on_create_from_template)
        self._create_fam_btn.clicked.connect(self._on_create_from_family)
        self._manage_fam_btn.clicked.connect(self.manage_families_requested.emit)

    def set_reference_label(self, text: str) -> None:
        self._ref_label.setText(text)

    def set_stem_label(self, text: str) -> None:
        self._stem_label.setText(text)

    def set_templates(self, names: list[str]) -> None:
        self._template_list.clear()
        for name in names:
            self._template_list.addItem(name)

    def get_selected_template(self) -> str:
        item = self._template_list.currentItem()
        return item.text() if item else ""

    def get_reference_mode(self) -> str:
        return self._mode_combo.currentText()

    def get_emotional_tone(self) -> str:
        return self._tone_combo.currentText()

    def set_tones(self, tones: list[str]) -> None:
        current = self._tone_combo.currentText()
        self._tone_combo.clear()
        self._switch_tone_combo.clear()
        for tone in tones:
            self._tone_combo.addItem(tone)
            self._switch_tone_combo.addItem(tone)
        idx = self._tone_combo.findText(current)
        if idx >= 0:
            self._tone_combo.setCurrentIndex(idx)

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _on_apply(self) -> None:
        name = self.get_selected_template()
        if name:
            self.apply_template.emit(name)

    def _on_reapply(self) -> None:
        name = self.get_selected_template()
        if name:
            self.reapply_to_selection.emit(name)

    def _on_switch_tone(self) -> None:
        name = self.get_selected_template()
        tone = self._switch_tone_combo.currentText()
        if name and tone:
            self.switch_tone.emit(name, tone)

    def _on_create_from_template(self) -> None:
        name = self.get_selected_template()
        if name:
            self.create_from_template.emit(name)

    def _on_create_from_family(self) -> None:
        name = self.get_selected_template()
        if name:
            self.create_from_family.emit(name)


class FamilyManagerDialog(QDialog):
    def __init__(self, families: list[dict[str, Any]],
                 templates: list[str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Template Family Manager")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Families:"))
        self._family_list = QListWidget()
        for fam in families:
            self._family_list.addItem(fam.get("name", ""))
        top_row.addWidget(self._family_list)

        btn_col = QVBoxLayout()
        self._create_btn = QPushButton("Create")
        self._delete_btn = QPushButton("Delete")
        self._rename_btn = QPushButton("Rename")
        btn_col.addWidget(self._create_btn)
        btn_col.addWidget(self._delete_btn)
        btn_col.addWidget(self._rename_btn)
        btn_col.addStretch()
        top_row.addLayout(btn_col)
        layout.addLayout(top_row)

        assign_row = QHBoxLayout()
        assign_row.addWidget(QLabel("Assign template:"))
        self._assign_combo = QComboBox()
        self._assign_combo.addItems(templates)
        self._assign_btn = QPushButton("Assign")
        assign_row.addWidget(self._assign_combo)
        assign_row.addWidget(self._assign_btn)
        layout.addLayout(assign_row)

        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setMaximumHeight(150)
        self._summary_text.setStyleSheet("font-size: 11px; font-family: monospace;")
        layout.addWidget(QLabel("Family Summary:"))
        layout.addWidget(self._summary_text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._families_data = families
        self.result_action: str = ""
        self.result_family_name: str = ""
        self.result_template_name: str = ""
        self.result_new_name: str = ""

        self._create_btn.clicked.connect(self._on_create)
        self._delete_btn.clicked.connect(self._on_delete)
        self._rename_btn.clicked.connect(self._on_rename)
        self._assign_btn.clicked.connect(self._on_assign)
        self._family_list.currentRowChanged.connect(self._on_family_selected)

    def _on_create(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Create Family", "Family name:")
        if ok and name.strip():
            self.result_action = "create"
            self.result_new_name = name.strip()
            self.accept()

    def _on_delete(self) -> None:
        item = self._family_list.currentItem()
        if item:
            self.result_action = "delete"
            self.result_family_name = item.text()
            self.accept()

    def _on_rename(self) -> None:
        item = self._family_list.currentItem()
        if not item:
            return
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Rename Family", "New name:", text=item.text())
        if ok and name.strip():
            self.result_action = "rename"
            self.result_family_name = item.text()
            self.result_new_name = name.strip()
            self.accept()

    def _on_assign(self) -> None:
        item = self._family_list.currentItem()
        tpl_name = self._assign_combo.currentText()
        if item and tpl_name:
            self.result_action = "assign"
            self.result_family_name = item.text()
            self.result_template_name = tpl_name
            self.accept()

    def _on_family_selected(self, row: int) -> None:
        if 0 <= row < len(self._families_data):
            fam = self._families_data[row]
            summary = fam.get("summary", {})
            if summary:
                lines = []
                lines.append(f"Templates: {summary.get('template_count', 0)}")
                tempo = summary.get("tempo_range", {})
                lines.append(f"Tempo: {tempo.get('min', 0)}-{tempo.get('max', 0)} BPM (avg {tempo.get('mean', 0)})")
                intensity = summary.get("intensity_distribution", {})
                lines.append(f"Intensity: mean={intensity.get('mean', 0)}, std={intensity.get('std', 0)}")
                delivery = summary.get("delivery_tendencies", {})
                for d, ratio in delivery.items():
                    if ratio > 0.01:
                        lines.append(f"  {d}: {ratio:.1%}")
                tones = summary.get("emotional_tones", {})
                if tones:
                    lines.append("Tones: " + ", ".join(f"{t}({c})" for t, c in tones.items()))
                self._summary_text.setPlainText("\n".join(lines))
            else:
                self._summary_text.setPlainText("No summary data")

    def set_summary(self, text: str) -> None:
        self._summary_text.setPlainText(text)
