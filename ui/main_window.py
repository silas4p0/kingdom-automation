import sys
import os
import shutil
import subprocess as _subprocess
import time as _time
import webbrowser as _webbrowser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QPushButton, QComboBox, QLabel, QSlider, QCheckBox,
    QGroupBox, QFileDialog, QApplication, QButtonGroup,
    QDialog, QDialogButtonBox, QTextEdit, QLineEdit, QFormLayout,
    QMessageBox, QInputDialog, QListWidget, QListWidgetItem,
    QStackedWidget, QTabWidget, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence

from ui.theme import ThemeManager
from ui.lyrics_panel import LyricsPanel
from ui.inspector_panel import InspectorPanel
from ui.console_panel import ConsolePanel
from ui.global_controls_panel import GlobalControlsPanel
from ui.selection_popover import SelectionPopover
from models.project_model import ProjectModel
from models.token_model import TokenModel, DeliveryMode, BravadoSubtype, BoundaryMarker
from models.voice_profile import VoiceModelManager
from core.tokenizer import Tokenizer
from core.undo_manager import UndoManager
from core.singer_router import SingerRouter
from engines.preview_engine import PreviewEngine
from engines.audio_synth import AudioPreviewSynthesizer
from engines.audio_player import AudioPlayer
from engines.dsp_analyzer import DSPAnalyzer, TokenParameterMapper
from engines.audio_recorder import AudioRecorder
from models.style_preset import StylePreset, StylePresetStore, compute_feature_vector, FEATURE_KEYS
from ui.capture_panel import CapturePanel
from ui.tracks_panel import TracksPanel
from ui.render_panel import RenderPanel
from ui.import_panel import ImportPanel
from models.render_job import RenderJob, RenderTarget, RenderStatus
from engines.alignment_engine import AlignmentEngine, AlignmentResult
from core.logger import get_logger, write_crash_report, write_solution_folder, export_debug_bundle
from core.fix_registry import lookup_fix, save_fix, export_fix_pack, import_fix_pack
from models.track_model import TrackModel, TrackAssignment, TrackType
from models.reference_template import ReferenceTemplate, TemplateFamily, TemplateFamilyStore
from engines.template_extractor import TemplateExtractor
from engines.training_pack_exporter import TrainingPackExporter
from ui.reference_panel import ReferencePanelUI, FamilyManagerDialog
from ui.world_navigator import WorldNavigatorDialog, WORKSPACE_BOOK_MAP
from ui.instrument_editor import InstrumentEditorDialog
from models.instrument_patch import InstrumentPatch, InstrumentStore


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Kingdom Digital Systems \u2013 Lyric Performance Engine")
        self.setMinimumSize(1200, 750)

        self._theme = ThemeManager()
        self._project = ProjectModel()
        self._undo = UndoManager()
        self._selected_token_idx: int = -1
        self._selection_range: tuple[int, int] | None = None
        self._popover: SelectionPopover | None = None
        self._preview_mode: str = "Single"
        self._log = get_logger("main_window")
        self._dsp_analyzer = DSPAnalyzer()
        self._param_mapper = TokenParameterMapper()
        self._audio_recorder = AudioRecorder()
        self._preset_store = StylePresetStore()
        self._last_capture_wav: str = ""
        self._last_analysis_dict: dict | None = None
        self._preview_apply_backup: list[dict] | None = None
        self._preview_apply_indices: list[int] = []
        self._render_jobs: list[RenderJob] = []
        self._alignment_engine = AlignmentEngine()
        self._imported_audio_path: str = ""
        self._last_alignment: AlignmentResult | None = None
        self._template_store = TemplateFamilyStore()
        self._template_extractor = TemplateExtractor()
        self._training_exporter = TrainingPackExporter()
        self._ref_audio_path: str = ""
        self._ref_stem_path: str = ""
        self._instrument_store = InstrumentStore()
        self._active_instrument: InstrumentPatch | None = None

        self._voice_manager = VoiceModelManager()
        self._preview_engine = PreviewEngine()
        self._audio_synth = AudioPreviewSynthesizer()
        self._preview_engine.set_synthesizer(self._audio_synth)
        self._audio_player = AudioPlayer()
        self._singer_router = SingerRouter(self._voice_manager, self._preview_engine)

        self._autosave_path = os.path.join(os.path.expanduser("~"), ".kds_lpe", "autosave.json")
        self._backups_dir = os.path.join(os.path.expanduser("~"), ".kds_lpe", "backups")
        self._projects_base = os.path.join(os.path.expanduser("~"), "Documents", "KDS_Projects")

        self._build_toolbar()
        self._build_menu()
        self._build_central()
        self._connect_signals()
        self._apply_theme()

        self._tracks_panel.set_tracks(self._project.tracks)
        self._import_panel.set_tracks([t.name for t in self._project.tracks if t.track_type != TrackType.MASTER])

        restored = self._try_restore_session()
        if not restored:
            self._push_undo()

        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(60_000)
        self._autosave_timer.timeout.connect(self._on_autosave)
        self._autosave_timer.start()

        self._console.log("Application started.")
        self._console.log(f"Voice profiles loaded: {', '.join(self._voice_manager.profile_names())}")
        self._console.log(f"Active singer: {self._voice_manager.active_profile.name if self._voice_manager.active_profile else 'None'}")
        self._console.log("Vocal preview engine ready (formant synthesis).")
        if restored:
            self._console.log("Previous session restored from autosave.")
        self._console.log("Auto-save enabled (every 60 s).")
        self._log.info("MainWindow initialized")

    def _build_toolbar(self) -> None:
        tb1 = QToolBar("Main Toolbar")
        tb1.setMovable(False)
        self.addToolBar(tb1)

        self._save_btn = QPushButton("Save Project")
        self._save_btn.setToolTip("Save current project to file")
        self._save_as_btn = QPushButton("Save As\u2026")
        self._save_as_btn.setToolTip("Save project to a new location; creates folder-based project if enabled in Settings")
        self._load_btn = QPushButton("Load Project")
        self._load_btn.setToolTip("Load a project from a JSON file")
        self._theme_btn = QPushButton("Toggle Theme")
        self._theme_btn.setToolTip("Switch between dark and light theme")
        self._settings_btn = QPushButton("Settings")
        self._settings_btn.setToolTip("Open application settings (folder-based projects toggle)")
        self._settings_btn.clicked.connect(self._on_settings)
        self._reveal_project_btn = QPushButton("Reveal Project")
        self._reveal_project_btn.setToolTip("Open project folder in file manager")
        self._reveal_project_btn.setEnabled(False)
        self._export_fixpack_btn = QPushButton("Fix Pack Export")
        self._export_fixpack_btn.setToolTip("Export all known fixes as a shareable zip for other machines")
        self._import_fixpack_btn = QPushButton("Fix Pack Import")
        self._import_fixpack_btn.setToolTip("Import a fix pack zip from another machine")
        self._export_debug_btn = QPushButton("Debug Bundle")
        self._export_debug_btn.setToolTip("Export a zip of logs, crash reports, and solution folders for debugging")
        self._export_training_btn = QPushButton("Export Training Pack")
        self._export_training_btn.setToolTip("Export aligned audio + lyrics dataset for voice training")
        self._export_training_btn.setStyleSheet("background: #00695c; color: white; padding: 3px 8px; border-radius: 3px;")

        self._autosave_label = QLabel("")
        self._autosave_label.setStyleSheet(
            "color: #8e8e8e; font-size: 11px; padding: 0 6px;"
        )
        self._reveal_autosave_btn = QPushButton("Reveal Autosave")
        self._reveal_autosave_btn.setToolTip("Open the autosave folder in file manager")
        self._reveal_backups_btn = QPushButton("Reveal Backups")
        self._reveal_backups_btn.setToolTip("Open the backups folder in file manager")

        tb1.addWidget(self._save_btn)
        tb1.addWidget(self._save_as_btn)
        tb1.addWidget(self._load_btn)
        tb1.addWidget(self._autosave_label)
        tb1.addWidget(self._reveal_project_btn)
        tb1.addSeparator()
        tb1.addWidget(self._theme_btn)
        tb1.addWidget(self._settings_btn)
        tb1.addWidget(self._export_debug_btn)
        tb1.addWidget(self._export_training_btn)

        tb1.addSeparator()

        tb1.addWidget(QLabel("  Render Mode: "))
        self._render_combo = QComboBox()
        self._render_combo.setToolTip("Select the render engine mode for audio generation")
        self._render_combo.addItems([
            "A Convert (Guide \u2192 Voice)",
            "B Synthesize (Text/Notes)",
            "C AI Assist (placeholder)",
            "D Live Convert (placeholder)",
        ])
        self._render_combo.setMinimumWidth(200)
        tb1.addWidget(self._render_combo)

        tb1.addSeparator()

        tb1.addWidget(QLabel("  Quality: "))
        self._quality_combo = QComboBox()
        self._quality_combo.setToolTip("Fast: fewer harmonics for real-time editing; High: full quality preview")
        self._quality_combo.addItems(["Fast", "High"])
        tb1.addWidget(self._quality_combo)

        self._preview_btn = QPushButton("Play Preview")
        self._preview_btn.setToolTip("Render and play audio preview for the current token, scope, and mode")
        tb1.addWidget(self._preview_btn)

        self._replay_btn = QPushButton("Replay Last")
        self._replay_btn.setToolTip("Replay the last rendered preview audio")

        tb2 = QToolBar("Singer Toolbar")
        tb2.setMovable(False)
        self.addToolBarBreak()
        self.addToolBar(tb2)

        tb2.addWidget(QLabel("  Singer: "))
        self._singer_combo = QComboBox()
        self._singer_combo.setToolTip("Select the active voice profile for synthesis")
        self._singer_combo.addItems(self._voice_manager.profile_names())
        tb2.addWidget(self._singer_combo)

        tb2.addWidget(QLabel("  Personality: "))
        self._personality_combo = QComboBox()
        self._personality_combo.setToolTip("Vocal personality character applied to the singer")
        self._personality_combo.addItems(["Neutral", "Warm", "Edgy", "Smooth"])
        tb2.addWidget(self._personality_combo)

        tb2.addWidget(QLabel("  Mix: "))
        self._mix_slider = QSlider(Qt.Orientation.Horizontal)
        self._mix_slider.setToolTip("Blend personality with base voice (0% = base only, 100% = full personality)")
        self._mix_slider.setRange(0, 100)
        self._mix_slider.setValue(50)
        self._mix_slider.setFixedWidth(100)
        tb2.addWidget(self._mix_slider)
        self._mix_readout = QLabel("50%")
        self._mix_readout.setFixedWidth(36)
        tb2.addWidget(self._mix_readout)

        tb2.addSeparator()
        self._auto_preview_cb = QCheckBox("Auto Preview")
        self._auto_preview_cb.setToolTip("Automatically play preview when sliders are released")
        tb2.addWidget(self._auto_preview_cb)

        tb2.addSeparator()
        tb2.addWidget(self._export_fixpack_btn)
        tb2.addWidget(self._import_fixpack_btn)
        tb2.addSeparator()
        tb2.addWidget(self._reveal_autosave_btn)
        tb2.addWidget(self._reveal_backups_btn)

        tb3 = QToolBar("Preview Scope")
        tb3.setMovable(False)
        self.addToolBarBreak()
        self.addToolBar(tb3)

        tb3.addWidget(QLabel("  Scope: "))
        self._scope_group = QButtonGroup(self)
        self._scope_group.setExclusive(True)
        self._scope_btns: dict[str, QPushButton] = {}
        for label in ["Word", "From Word", "Line", "Section"]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            if label == "Section":
                btn.setEnabled(False)
                btn.setToolTip("Select a range of tokens to enable Section scope")
            self._scope_btns[label] = btn
            self._scope_group.addButton(btn)
            tb3.addWidget(btn)
        self._scope_btns["Word"].setChecked(True)

        tb3.addSeparator()

        tb3.addWidget(QLabel("  Pre-Roll: "))
        self._preroll_slider = QSlider(Qt.Orientation.Horizontal)
        self._preroll_slider.setToolTip("Silence or context tokens added before the preview (0-2000ms)")
        self._preroll_slider.setRange(0, 2000)
        self._preroll_slider.setValue(500)
        self._preroll_slider.setFixedWidth(100)
        tb3.addWidget(self._preroll_slider)
        self._preroll_readout = QLabel("500ms")
        self._preroll_readout.setFixedWidth(48)
        tb3.addWidget(self._preroll_readout)

        tb3.addWidget(QLabel("  Post-Roll: "))
        self._postroll_slider = QSlider(Qt.Orientation.Horizontal)
        self._postroll_slider.setToolTip("Silence or context tokens added after the preview (0-2000ms)")
        self._postroll_slider.setRange(0, 2000)
        self._postroll_slider.setValue(250)
        self._postroll_slider.setFixedWidth(100)
        tb3.addWidget(self._postroll_slider)
        self._postroll_readout = QLabel("250ms")
        self._postroll_readout.setFixedWidth(48)
        tb3.addWidget(self._postroll_readout)

        tb3.addSeparator()
        self._snap_cb = QCheckBox("Snap to words")
        self._snap_cb.setToolTip("Snap scope boundaries to the nearest word edges")
        self._snap_cb.setChecked(True)
        tb3.addWidget(self._snap_cb)

        tb3.addSeparator()
        tb3.addWidget(QLabel("  Mode: "))
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._mode_btns: dict[str, QPushButton] = {}
        for label in ["Single", "Forward", "Assist (Later)"]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            if label == "Assist (Later)":
                btn.setEnabled(False)
                btn.setToolTip("AI-assisted preview — coming later")
            self._mode_btns[label] = btn
            self._mode_group.addButton(btn)
            tb3.addWidget(btn)
        self._mode_btns["Single"].setChecked(True)

        tb3.addSeparator()
        tb3.addWidget(self._replay_btn)

        tb3.addSeparator()
        tb3.addWidget(QLabel("  Instrument: "))
        self._instrument_combo = QComboBox()
        self._instrument_combo.setToolTip("Select an instrument patch to override voice-type synthesis")
        self._instrument_combo.addItem("(None — use Voice Type)")
        for name in self._instrument_store.list_names():
            self._instrument_combo.addItem(name)
        self._instrument_combo.setMinimumWidth(160)
        tb3.addWidget(self._instrument_combo)
        self._inst_edit_btn = QPushButton("Edit\u2026")
        self._inst_edit_btn.setToolTip("Open the Instrument Editor to adjust envelope, timbre, noise, and token defaults")
        self._inst_saveas_btn = QPushButton("Save As\u2026")
        self._inst_saveas_btn.setToolTip("Save current instrument settings as a new named instrument")
        self._inst_dup_btn = QPushButton("Duplicate")
        self._inst_dup_btn.setToolTip("Clone the selected instrument")
        self._inst_del_btn = QPushButton("Delete")
        self._inst_del_btn.setToolTip("Remove a user-created instrument (built-in presets cannot be deleted)")
        tb3.addWidget(self._inst_edit_btn)
        tb3.addWidget(self._inst_saveas_btn)
        tb3.addWidget(self._inst_dup_btn)
        tb3.addWidget(self._inst_del_btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb1.addWidget(spacer)
        self._world_btn = QPushButton("\U0001f310 World")
        self._world_btn.setToolTip("Open World Navigator globe overlay to switch workspaces visually")
        self._world_btn.setStyleSheet("padding: 4px 10px; font-weight: bold;")
        tb1.addWidget(self._world_btn)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Help")
        docs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs",
        )
        manual_action = QAction("User Manual", self)
        manual_action.triggered.connect(
            lambda: self._open_doc(os.path.join(docs_dir, "user_manual.md")),
        )
        help_menu.addAction(manual_action)
        quick_action = QAction("Quick Start Guide", self)
        quick_action.triggered.connect(
            lambda: self._open_doc(os.path.join(docs_dir, "quick_start.md")),
        )
        help_menu.addAction(quick_action)
        help_menu.addSeparator()
        trouble_action = QAction("Troubleshooting", self)
        trouble_action.triggered.connect(
            lambda: self._open_doc(os.path.join(docs_dir, "troubleshooting.md")),
        )
        help_menu.addAction(trouble_action)
        arch_action = QAction("Architecture Overview", self)
        arch_action.triggered.connect(
            lambda: self._open_doc(os.path.join(docs_dir, "architecture.md")),
        )
        help_menu.addAction(arch_action)
        workflows_action = QAction("Composer Workflows", self)
        workflows_action.triggered.connect(
            lambda: self._open_doc(os.path.join(docs_dir, "composer_workflows.md")),
        )
        help_menu.addAction(workflows_action)

    def _open_doc(self, path: str) -> None:
        if not os.path.isfile(path):
            self._console.log(f"Doc not found: {path}")
            return
        try:
            if sys.platform == "darwin":
                _subprocess.Popen(["open", path])
            elif sys.platform.startswith("linux"):
                _subprocess.Popen(["xdg-open", path])
            else:
                os.startfile(path)
        except Exception:
            _webbrowser.open(f"file://{path}")
        self._console.log(f"Opened doc: {os.path.basename(path)}")

    def _build_central(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._mode_d_panel = self._build_mode_d_panel()
        self._mode_d_panel.setVisible(False)
        main_layout.addWidget(self._mode_d_panel)

        splitter_v = QSplitter(Qt.Orientation.Vertical)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._book_list = QListWidget()
        self._book_list.setFixedWidth(180)
        self._book_list.setStyleSheet(
            "QListWidget { background: #1a1a2e; border: none; font-size: 13px; }"
            "QListWidget::item { padding: 10px 12px; color: #ccc; }"
            "QListWidget::item:selected { background: #16213e; color: #00d4ff; font-weight: bold; border-left: 3px solid #00d4ff; }"
            "QListWidget::item:hover { background: #1f2b47; }"
        )

        self._book_names = [
            "Composition",
            "Performance",
            "Tracks",
            "Reference",
            "Import",
            "Rendering",
            "Wisdom",
        ]
        self._book_labels = [
            "Book of Composition",
            "Book of Performance",
            "Book of Tracks",
            "Book of Reference",
            "Book of Import",
            "Book of Rendering",
            "Book of Wisdom",
        ]
        for label in self._book_labels:
            item = QListWidgetItem(label)
            self._book_list.addItem(item)
        self._book_list.setCurrentRow(0)

        body_layout.addWidget(self._book_list)

        self._book_stack = QStackedWidget()
        self._book_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._lyrics_panel = LyricsPanel()
        self._inspector_panel = InspectorPanel()
        self._global_controls = GlobalControlsPanel()
        self._capture_panel = CapturePanel()
        self._tracks_panel = TracksPanel()
        self._render_panel = RenderPanel()
        self._import_panel = ImportPanel()
        self._reference_panel = ReferencePanelUI()

        self._book_stack.addWidget(self._build_book_composition())
        self._book_stack.addWidget(self._build_book_performance())
        self._book_stack.addWidget(self._build_book_tracks())
        self._book_stack.addWidget(self._build_book_reference())
        self._book_stack.addWidget(self._build_book_import())
        self._book_stack.addWidget(self._build_book_rendering())
        self._book_stack.addWidget(self._build_book_wisdom())

        body_layout.addWidget(self._book_stack)

        splitter_v.addWidget(body)

        self._console = ConsolePanel()
        self._console.setMaximumHeight(180)
        splitter_v.addWidget(self._console)
        splitter_v.setStretchFactor(0, 4)
        splitter_v.setStretchFactor(1, 1)

        main_layout.addWidget(splitter_v)

    def _wrap_in_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        return scroll

    def _build_book_composition(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._lyrics_panel, "Lyrics & Tokens")
        tabs.addTab(self._wrap_in_scroll(self._inspector_panel), "Inspector")
        tabs.addTab(self._wrap_in_scroll(self._global_controls), "Global Controls")
        return tabs

    def _build_book_performance(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._wrap_in_scroll(self._capture_panel), "Capture & Analyze")
        preset_label = QLabel(
            "Use the Capture & Analyze tab to record/import audio, run DSP analysis, "
            "review mapping, and match against existing presets."
        )
        preset_label.setWordWrap(True)
        preset_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        preset_label.setContentsMargins(16, 16, 16, 16)
        tabs.addTab(preset_label, "Preset Matching")
        return tabs

    def _build_book_tracks(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._wrap_in_scroll(self._tracks_panel), "Track List & Assignments")
        stems_label = QLabel(
            "Use the Track List tab to assign tokens and click Export Stems."
        )
        stems_label.setWordWrap(True)
        stems_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        stems_label.setContentsMargins(16, 16, 16, 16)
        tabs.addTab(stems_label, "Export Stems")
        return tabs

    def _build_book_reference(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._wrap_in_scroll(self._reference_panel), "Templates & Families")
        return tabs

    def _build_book_import(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._wrap_in_scroll(self._import_panel), "Song Audio & Alignment")
        return tabs

    def _build_book_rendering(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._wrap_in_scroll(self._render_panel), "Render Queue & Script Export")

        export_w = QWidget()
        export_lay = QVBoxLayout(export_w)
        export_lay.setContentsMargins(16, 16, 16, 16)
        export_lay.addWidget(QLabel("Training Pack & Debug Bundle exports are available from the main toolbar."))
        export_lay.addStretch()
        tabs.addTab(export_w, "Training Pack & Debug")
        return tabs

    def _build_book_wisdom(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        docs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs",
        )
        doc_files = [
            ("User Manual", "user_manual.md"),
            ("Quick Start", "quick_start.md"),
            ("Troubleshooting", "troubleshooting.md"),
            ("Composer Workflows", "composer_workflows.md"),
            ("Architecture", "architecture.md"),
        ]
        for title, filename in doc_files:
            path = os.path.join(docs_dir, filename)
            text_widget = QTextEdit()
            text_widget.setReadOnly(True)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    text_widget.setPlainText(f.read())
            else:
                text_widget.setPlainText(f"{filename} not found.")
            tabs.addTab(text_widget, title)
        return tabs

    def _on_book_changed(self, row: int) -> None:
        if 0 <= row < self._book_stack.count():
            self._book_stack.setCurrentIndex(row)
            self._project.active_book = self._book_names[row]
            self._console.log(f"Opened: {self._book_labels[row]}")

    def _switch_to_book(self, index: int) -> None:
        if 0 <= index < len(self._book_names):
            self._book_list.setCurrentRow(index)

    def _build_mode_d_panel(self) -> QGroupBox:
        group = QGroupBox("Mode D \u2013 Live Convert")
        lay = QVBoxLayout(group)

        notice = QLabel("Live conversion engine not yet implemented")
        notice.setStyleSheet("color: #ffc107; font-weight: bold; padding: 6px;")
        notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(notice)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Input Device:"))
        inp = QComboBox()
        inp.addItem("(none)")
        inp.setEnabled(False)
        row1.addWidget(inp)
        row1.addWidget(QLabel("Output Device:"))
        out = QComboBox()
        out.addItem("(none)")
        out.setEnabled(False)
        row1.addWidget(out)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Singer:"))
        self._d_singer = QComboBox()
        self._d_singer.addItems(["Default Singer", "Singer A", "Singer B", "Singer C"])
        row2.addWidget(self._d_singer)
        row2.addWidget(QLabel("Personality:"))
        self._d_personality = QComboBox()
        self._d_personality.addItems(["Neutral", "Warm", "Edgy", "Smooth"])
        row2.addWidget(self._d_personality)
        row2.addWidget(QLabel("Mix:"))
        self._d_mix = QSlider(Qt.Orientation.Horizontal)
        self._d_mix.setRange(0, 100)
        self._d_mix.setValue(50)
        self._d_mix.setFixedWidth(100)
        row2.addWidget(self._d_mix)
        self._d_mix_readout = QLabel("50%")
        row2.addWidget(self._d_mix_readout)
        lay.addLayout(row2)

        self._d_mix.valueChanged.connect(
            lambda v: self._d_mix_readout.setText(f"{v}%")
        )

        start_btn = QPushButton("Start Live")
        start_btn.setEnabled(False)
        lay.addWidget(start_btn)

        return group

    def _connect_signals(self) -> None:
        self._book_list.currentRowChanged.connect(self._on_book_changed)

        for i in range(len(self._book_names)):
            act = QAction(self)
            act.setShortcut(QKeySequence(f"Ctrl+{i + 1}"))
            idx = i
            act.triggered.connect(lambda checked=False, x=idx: self._switch_to_book(x))
            self.addAction(act)

        self._save_btn.clicked.connect(self._on_save)
        self._save_as_btn.clicked.connect(self._on_save_as)
        self._load_btn.clicked.connect(self._on_load)
        self._reveal_autosave_btn.clicked.connect(self._on_reveal_autosave)
        self._reveal_backups_btn.clicked.connect(self._on_reveal_backups)
        self._reveal_project_btn.clicked.connect(self._on_reveal_project)
        self._theme_btn.clicked.connect(self._on_toggle_theme)
        self._export_debug_btn.clicked.connect(self._on_export_debug)
        self._export_fixpack_btn.clicked.connect(self._on_export_fixpack)
        self._import_fixpack_btn.clicked.connect(self._on_import_fixpack)
        self._export_training_btn.clicked.connect(self._on_export_training_pack)
        self._render_combo.currentTextChanged.connect(self._on_render_mode)
        self._quality_combo.currentTextChanged.connect(self._on_quality)
        self._preview_btn.clicked.connect(self._on_preview)
        self._auto_preview_cb.toggled.connect(self._on_auto_preview)
        self._singer_combo.currentTextChanged.connect(self._on_singer)
        self._personality_combo.currentTextChanged.connect(self._on_personality)
        self._mix_slider.valueChanged.connect(self._on_mix)

        self._lyrics_panel.lyrics_changed.connect(self._on_tokenize)
        self._lyrics_panel.token_selected.connect(self._on_token_selected)
        self._lyrics_panel.range_selected.connect(self._on_range_selected)
        self._lyrics_panel.selection_cleared.connect(self._on_selection_cleared)

        esc_action = QAction(self)
        esc_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        esc_action.triggered.connect(self._on_esc)
        self.addAction(esc_action)

        self._replay_btn.clicked.connect(self._on_replay)

        self._inspector_panel.duration_changed.connect(self._on_duration)
        self._inspector_panel.loudness_changed.connect(self._on_loudness)
        self._inspector_panel.intensity_changed.connect(self._on_intensity)
        self._inspector_panel.pitch_offset_changed.connect(self._on_pitch_offset)
        self._inspector_panel.slider_released.connect(self._on_slider_release)
        self._inspector_panel.delivery_changed.connect(self._on_delivery)
        self._inspector_panel.bravado_subtype_changed.connect(self._on_bravado_sub)

        self._global_controls.tempo_changed.connect(self._on_tempo)
        self._global_controls.key_changed.connect(self._on_key)
        self._global_controls.voice_type_changed.connect(self._on_voice_type)

        self._scope_group.buttonClicked.connect(self._on_scope_changed)
        self._mode_group.buttonClicked.connect(self._on_mode_changed)
        self._preroll_slider.valueChanged.connect(self._on_preroll)
        self._postroll_slider.valueChanged.connect(self._on_postroll)

        self._capture_panel.record_requested.connect(self._on_capture_record)
        self._capture_panel.stop_requested.connect(self._on_capture_stop)
        self._capture_panel.import_requested.connect(self._on_capture_import)
        self._capture_panel.analyze_requested.connect(self._on_capture_analyze)
        self._capture_panel.apply_to_tokens.connect(self._on_capture_apply)
        self._capture_panel.preview_apply_requested.connect(self._on_preview_apply)
        self._capture_panel.commit_apply_requested.connect(self._on_commit_apply)
        self._capture_panel.revert_preview_requested.connect(self._on_revert_preview)
        self._capture_panel.preset_created.connect(self._on_capture_preset_create)
        self._capture_panel.session_preset_accepted.connect(self._on_session_preset_accept)
        self._capture_panel.session_preset_renamed.connect(self._on_session_preset_rename)
        self._capture_panel.use_preset_requested.connect(self._on_use_preset)
        self._capture_panel.create_new_preset_requested.connect(self._on_create_new_preset)
        self._capture_panel.compare_details_requested.connect(self._on_compare_details)
        self._capture_panel.session_finished.connect(
            lambda: self._console.log("Style Capture Session ended")
        )

        self._inspector_panel.ok_clicked.connect(self._on_ok)
        self._inspector_panel.cancel_clicked.connect(self._on_cancel)
        self._inspector_panel.next_clicked.connect(self._on_next_token)
        self._inspector_panel.prev_clicked.connect(self._on_prev_token)

        self._tracks_panel.track_selected.connect(self._on_track_selected)
        self._tracks_panel.assign_requested.connect(self._on_assign_to_track)
        self._tracks_panel.export_stems_requested.connect(self._on_export_stems)

        self._import_panel.import_audio.connect(self._on_import_audio)
        self._import_panel.run_alignment.connect(self._on_run_alignment)
        self._import_panel.auto_fill_tokens.connect(self._on_auto_fill_tokens)

        self._reference_panel.import_reference.connect(self._on_import_reference)
        self._reference_panel.import_vocal_stem.connect(self._on_import_vocal_stem)
        self._reference_panel.extract_template.connect(self._on_extract_template)
        self._reference_panel.apply_template.connect(self._on_apply_template)
        self._reference_panel.reapply_to_selection.connect(self._on_reapply_template)
        self._reference_panel.switch_tone.connect(self._on_switch_tone)
        self._reference_panel.create_from_template.connect(self._on_create_from_template)
        self._reference_panel.create_from_family.connect(self._on_create_from_family)
        self._reference_panel.manage_families_requested.connect(self._on_manage_families)

        self._render_panel.export_script.connect(self._on_export_script)
        self._render_panel.add_master_job.connect(self._on_add_master_render_job)
        self._render_panel.add_track_job.connect(self._on_add_track_render_job)
        self._render_panel.run_selected.connect(self._on_run_render_job)
        self._render_panel.run_all.connect(self._on_run_all_render_jobs)
        self._render_panel.cancel_job.connect(self._on_cancel_render_job)

        undo_action = QAction(self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self._on_undo)
        self.addAction(undo_action)

        redo_action = QAction(self)
        redo_action.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        redo_action.triggered.connect(self._on_redo)
        self.addAction(redo_action)

        next_token_action = QAction(self)
        next_token_action.setShortcut(QKeySequence("Ctrl+Right"))
        next_token_action.triggered.connect(self._on_next_token)
        self.addAction(next_token_action)

        prev_token_action = QAction(self)
        prev_token_action.setShortcut(QKeySequence("Ctrl+Left"))
        prev_token_action.triggered.connect(self._on_prev_token)
        self.addAction(prev_token_action)

        self._world_btn.clicked.connect(self._on_world_navigator)
        self._instrument_combo.currentTextChanged.connect(self._on_instrument_changed)
        self._inst_edit_btn.clicked.connect(self._on_instrument_edit)
        self._inst_saveas_btn.clicked.connect(self._on_instrument_save_as)
        self._inst_dup_btn.clicked.connect(self._on_instrument_duplicate)
        self._inst_del_btn.clicked.connect(self._on_instrument_delete)

    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self._theme.stylesheet())

    def _push_undo(self) -> None:
        self._undo.push(self._project.to_dict())

    def _update_autosave_label(self) -> None:
        ts = _time.strftime("%H:%M:%S")
        self._autosave_label.setText(f"Saved \u2713 {ts}")
        self._autosave_label.setStyleSheet(
            "color: #4caf50; font-size: 11px; font-weight: bold; padding: 0 6px;"
        )

    def _on_autosave(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._autosave_path), exist_ok=True)
            self._sync_project()
            self._project.save(self._autosave_path)
            self._write_timestamped_backup()
            self._update_autosave_label()
            self._log.info("Auto-saved session")
        except Exception as exc:
            self._log.warning(f"Auto-save failed: {exc}")

    def _write_timestamped_backup(self) -> None:
        try:
            os.makedirs(self._backups_dir, exist_ok=True)
            ts = _time.strftime("%Y-%m-%d_%H%M%S")
            backup_path = os.path.join(self._backups_dir, f"backup_{ts}.json")
            self._project.save(backup_path)
            self._prune_old_backups(max_keep=50)
        except Exception as exc:
            self._log.warning(f"Backup write failed: {exc}")

    def _prune_old_backups(self, max_keep: int = 50) -> None:
        try:
            files = sorted(
                (f for f in os.listdir(self._backups_dir) if f.startswith("backup_") and f.endswith(".json")),
            )
            while len(files) > max_keep:
                oldest = files.pop(0)
                os.remove(os.path.join(self._backups_dir, oldest))
        except Exception:
            pass

    def _try_restore_session(self) -> bool:
        if os.path.isfile(self._autosave_path):
            try:
                self._project = ProjectModel.load(self._autosave_path)
                self._restore_from_project()
                self._log.info("Restored session from autosave")
                return True
            except Exception as exc:
                self._log.warning(f"Failed to restore session: {exc}")
        return False

    def _on_reveal_autosave(self) -> None:
        folder = os.path.dirname(self._autosave_path)
        os.makedirs(folder, exist_ok=True)
        if sys.platform == "darwin":
            _subprocess.Popen(["open", folder])
        elif sys.platform.startswith("linux"):
            _subprocess.Popen(["xdg-open", folder])
        else:
            _subprocess.Popen(["explorer", folder])
        self._console.log(f"Revealed autosave folder: {folder}")

    def _on_reveal_backups(self) -> None:
        os.makedirs(self._backups_dir, exist_ok=True)
        if sys.platform == "darwin":
            _subprocess.Popen(["open", self._backups_dir])
        elif sys.platform.startswith("linux"):
            _subprocess.Popen(["xdg-open", self._backups_dir])
        else:
            _subprocess.Popen(["explorer", self._backups_dir])
        self._console.log(f"Revealed backups folder: {self._backups_dir}")

    def _on_reveal_project(self) -> None:
        folder = self._project.project_folder
        if not folder or not os.path.isdir(folder):
            self._console.log("No project folder set")
            return
        if sys.platform == "darwin":
            _subprocess.Popen(["open", folder])
        elif sys.platform.startswith("linux"):
            _subprocess.Popen(["xdg-open", folder])
        else:
            _subprocess.Popen(["explorer", folder])
        self._console.log(f"Revealed project folder: {folder}")

    def _on_settings(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        dlg.setMinimumWidth(350)
        layout = QVBoxLayout(dlg)
        folder_cb = QCheckBox("Use Folder-Based Projects")
        folder_cb.setChecked(self._project.folder_based)
        layout.addWidget(folder_cb)
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._project.folder_based = folder_cb.isChecked()
            state = "ON" if self._project.folder_based else "OFF"
            self._console.log(f"Folder-based projects: {state}")

    def _on_save(self) -> None:
        self._sync_project()
        if self._project.project_folder and self._project.folder_based:
            save_path = os.path.join(self._project.project_folder, "project.json")
            self._project.save(save_path)
            self._write_timestamped_backup()
            self._update_autosave_label()
            self._console.log(f"Project saved to {save_path}")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "JSON Files (*.json)"
        )
        if path:
            self._project.save(path)
            self._write_timestamped_backup()
            self._update_autosave_label()
            self._console.log(f"Project saved to {path}")

    def _on_save_as(self) -> None:
        self._sync_project()
        if self._project.folder_based:
            name, ok = QInputDialog.getText(
                self, "Save Project As\u2026",
                "Project name:", QLineEdit.EchoMode.Normal, ""
            )
            if ok and name.strip():
                name = name.strip()
                folder = ProjectModel.create_project_folder(self._projects_base, name)
                self._project.project_folder = folder
                save_path = os.path.join(folder, "project.json")
                self._project.save(save_path)
                self._write_timestamped_backup()
                self._update_autosave_label()
                self._reveal_project_btn.setEnabled(True)
                self._console.log(f"Project folder created: {folder}")
        else:
            home = os.path.expanduser("~")
            downloads = os.path.join(home, "Downloads")
            default_dir = downloads if os.path.isdir(downloads) else home
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Project As\u2026", default_dir, "JSON Files (*.json)"
            )
            if path:
                self._project.save(path)
                self._write_timestamped_backup()
                self._console.log(f"Project exported to {path}")

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "JSON Files (*.json)"
        )
        if path:
            self._project = ProjectModel.load(path)
            self._restore_from_project()
            self._console.log(f"Project loaded from {path}")

    def _on_toggle_theme(self) -> None:
        new = self._theme.toggle()
        self._project.theme = new
        self._apply_theme()
        self._console.log(f"Theme switched to {new}")

    def _on_render_mode(self, mode: str) -> None:
        self._project.render_mode = mode
        is_d = mode.startswith("D")
        self._mode_d_panel.setVisible(is_d)
        self._console.log(f"Render mode: {mode}")

    def _on_quality(self, quality: str) -> None:
        self._project.engine_quality = quality
        self._singer_router.set_quality(quality)
        self._console.log(f"Engine quality: {quality}")

    def _get_scope(self) -> str:
        checked = self._scope_group.checkedButton()
        if checked:
            return checked.text()
        return "Word"

    def _get_line_tokens(self, token_idx: int) -> list[int]:
        if not (0 <= token_idx < len(self._project.tokens)):
            return []
        line = self._project.tokens[token_idx].line_index
        return [i for i, t in enumerate(self._project.tokens) if t.line_index == line]

    def _collect_preroll_tokens(self, anchor: int, max_ms: int, snap: bool) -> list[int]:
        if max_ms <= 0 or anchor <= 0:
            return []
        accumulated = 0
        result: list[int] = []
        for i in range(anchor - 1, -1, -1):
            dur = self._project.tokens[i].duration_ms
            if snap:
                if accumulated + dur > max_ms:
                    break
                accumulated += dur
                result.insert(0, i)
            else:
                accumulated += dur
                result.insert(0, i)
                if accumulated >= max_ms:
                    break
        return result

    def _collect_postroll_tokens(self, anchor: int, max_ms: int, snap: bool) -> list[int]:
        if max_ms <= 0 or anchor >= len(self._project.tokens) - 1:
            return []
        accumulated = 0
        result: list[int] = []
        for i in range(anchor + 1, len(self._project.tokens)):
            dur = self._project.tokens[i].duration_ms
            if snap:
                if accumulated + dur > max_ms:
                    break
                accumulated += dur
                result.append(i)
            else:
                accumulated += dur
                result.append(i)
                if accumulated >= max_ms:
                    break
        return result

    def _get_preview_mode(self) -> str:
        checked = self._mode_group.checkedButton()
        if checked:
            return checked.text()
        return "Single"

    def _build_preview_sequence(self) -> list[int]:
        scope = self._get_scope()
        mode = self._get_preview_mode()

        idx = self._selected_token_idx
        tokens = self._project.tokens
        if not (0 <= idx < len(tokens)):
            if self._selection_range:
                idx = self._selection_range[0]
                self._selected_token_idx = idx
            else:
                return []

        preroll_ms = self._preroll_slider.value()
        postroll_ms = self._postroll_slider.value()
        snap = self._snap_cb.isChecked()
        pre = self._collect_preroll_tokens(idx, preroll_ms, snap)
        line_indices = self._get_line_tokens(idx)

        if mode == "Single":
            return pre + [idx] + self._collect_postroll_tokens(idx, postroll_ms, snap)

        if scope == "Word":
            if mode == "Forward":
                end_of_line = [i for i in line_indices if i >= idx] if line_indices else [idx]
                post_budget = self._collect_postroll_tokens(end_of_line[-1], postroll_ms, snap)
                return pre + end_of_line + post_budget
            return pre + [idx] + self._collect_postroll_tokens(idx, postroll_ms, snap)

        if scope == "From Word":
            if mode == "Forward":
                if self._selection_range:
                    _, sel_end = self._selection_range
                    rng = list(range(idx, min(sel_end + 1, len(tokens))))
                else:
                    rng = [i for i in line_indices if i >= idx] if line_indices else [idx]
                post = self._collect_postroll_tokens(rng[-1], postroll_ms, snap)
                return pre + rng + post
            return pre + [idx] + self._collect_postroll_tokens(idx, postroll_ms, snap)

        if scope == "Line":
            if mode == "Forward":
                forward_in_line = [i for i in line_indices if i >= idx] if line_indices else [idx]
                return pre + forward_in_line
            return pre + [idx] + self._collect_postroll_tokens(idx, postroll_ms, snap)

        if scope == "Section":
            if self._selection_range:
                lo, hi = self._selection_range
                if mode == "Forward":
                    rng = list(range(idx, min(hi + 1, len(tokens))))
                    return pre + rng
                return pre + [idx] + self._collect_postroll_tokens(idx, postroll_ms, snap)
            return pre + [idx] + self._collect_postroll_tokens(idx, postroll_ms, snap)

        return [idx]

    def _on_preview(self) -> None:
        if not self._project.tokens:
            QMessageBox.warning(self, "No Tokens", "No tokens to preview. Enter lyrics and click Tokenize first.")
            return
        if not (0 <= self._selected_token_idx < len(self._project.tokens)):
            QMessageBox.warning(self, "No Token Selected", "Select a token before previewing.")
            return

        sequence = self._build_preview_sequence()
        sequence = self._filter_sequence_by_track(sequence)
        if not sequence:
            self._console.log("Preview: empty sequence")
            return

        scope = self._get_scope()
        token_dicts = [self._project.tokens[i].to_dict() for i in sequence]

        self._console.log("Rendering preview")

        if len(token_dicts) == 1:
            preview_result = self._preview_engine.preview_token(token_dicts[0])
        else:
            preview_result = self._preview_engine.preview_phrase(token_dicts)

        if preview_result.audio_data:
            self._audio_player.play_bytes(preview_result.audio_data)
            sel_word = self._project.tokens[self._selected_token_idx].word
            self._console.log(
                f"Preview generated [{scope}]: \"{sel_word}\" ("
                f"{len(sequence)} tokens, {preview_result.duration_ms}ms)"
            )
        else:
            self._console.log("Preview: no audio generated")

    def _on_replay(self) -> None:
        if self._audio_player.replay_last():
            self._console.log("Replaying last preview")
        else:
            self._console.log("No previous preview to replay")

    def _on_slider_release(self) -> None:
        self._on_preview()

    def _on_auto_preview(self, checked: bool) -> None:
        self._project.auto_preview = checked
        self._console.log(f"Auto preview: {'ON' if checked else 'OFF'}")

    def _on_singer(self, singer: str) -> None:
        self._project.singer = singer
        self._singer_router.set_singer_by_name(singer)
        self._console.log(f"Singer: {singer} (profile: {self._voice_manager.active_id})")

    def _on_personality(self, personality: str) -> None:
        self._project.personality = personality
        self._singer_router.set_personality(personality)
        self._console.log(f"Personality: {personality}")

    def _on_mix(self, val: int) -> None:
        self._mix_readout.setText(f"{val}%")
        self._project.personality_mix = val
        self._singer_router.set_personality_mix(val)
        self._console.log(f"Personality mix: {val}%")

    def _on_tokenize(self, text: str) -> None:
        self._project.lyrics = text
        self._project.tokens = Tokenizer.tokenize(text)
        Tokenizer.apply_repeat_inheritance(self._project.tokens)
        words = [t.word for t in self._project.tokens]
        self._lyrics_panel.display_tokens(words)
        self._inspector_panel.clear_display()
        self._selected_token_idx = -1
        self._push_undo()
        self._console.log(f"Tokenized {len(words)} words")

    def _on_token_selected(self, index: int) -> None:
        self._selected_token_idx = index
        self._selection_range = None
        self._scope_btns["Section"].setEnabled(False)
        if self._popover and self._popover.isVisible():
            self._popover.close()
        if 0 <= index < len(self._project.tokens):
            t = self._project.tokens[index]
            self._inspector_panel.display_token(
                t.word, t.duration_ms, t.loudness_pct,
                t.intensity, t.pitch_offset,
                t.delivery.value, t.bravado_subtype.value,
            )
            self._console.log(f"Selected token [{index}]: \"{t.word}\"")

    def _on_duration(self, val: int) -> None:
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            self._project.tokens[self._selected_token_idx].duration_ms = val

    def _on_loudness(self, val: int) -> None:
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            self._project.tokens[self._selected_token_idx].loudness_pct = val

    def _on_intensity(self, val: int) -> None:
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            self._project.tokens[self._selected_token_idx].intensity = val

    def _on_pitch_offset(self, val: int) -> None:
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            self._project.tokens[self._selected_token_idx].pitch_offset = val

    def _on_delivery(self, mode: str) -> None:
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            self._project.tokens[self._selected_token_idx].delivery = DeliveryMode(mode)
            self._console.log(f"Delivery: {mode}")
            self._on_preview()

    def _on_bravado_sub(self, sub: str) -> None:
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            self._project.tokens[self._selected_token_idx].bravado_subtype = BravadoSubtype(sub)
            self._console.log(f"Bravado subtype: {sub}")

    def _on_ok(self) -> None:
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            t = self._project.tokens[self._selected_token_idx]
            t.locked = True
            self._lyrics_panel.set_token_locked(self._selected_token_idx, True)
            Tokenizer.apply_repeat_inheritance(self._project.tokens)
            self._push_undo()
            self._console.log(f"Locked token [{self._selected_token_idx}]: \"{t.word}\"")

    def _on_cancel(self) -> None:
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            state = self._undo.undo()
            if state:
                self._restore_state(state)
                self._console.log("Cancel: reverted last change")

    def _on_next_token(self) -> None:
        count = self._lyrics_panel.token_count()
        if count == 0:
            return
        idx = self._selected_token_idx + 1
        if idx >= count:
            idx = 0
        self._lyrics_panel.select_token(idx)
        self._on_token_selected(idx)

    def _on_prev_token(self) -> None:
        count = self._lyrics_panel.token_count()
        if count == 0:
            return
        idx = self._selected_token_idx - 1
        if idx < 0:
            idx = count - 1
        self._lyrics_panel.select_token(idx)
        self._on_token_selected(idx)

    def _on_undo(self) -> None:
        state = self._undo.undo()
        if state:
            self._restore_state(state)
            self._console.log("Undo")

    def _on_redo(self) -> None:
        state = self._undo.redo()
        if state:
            self._restore_state(state)
            self._console.log("Redo")

    def _sync_project(self) -> None:
        self._project.render_mode = self._render_combo.currentText()
        self._project.engine_quality = self._quality_combo.currentText()
        self._project.auto_preview = self._auto_preview_cb.isChecked()
        self._project.singer = self._singer_combo.currentText()
        self._project.personality = self._personality_combo.currentText()
        self._project.personality_mix = self._mix_slider.value()
        self._project.theme = self._theme.current
        self._reveal_project_btn.setEnabled(bool(self._project.project_folder))
        self._project.tracks = self._tracks_panel._tracks
        row = self._book_list.currentRow()
        if 0 <= row < len(self._book_names):
            self._project.active_book = self._book_names[row]

    def _restore_from_project(self) -> None:
        self._render_combo.setCurrentText(self._project.render_mode)
        self._quality_combo.setCurrentText(self._project.engine_quality)
        self._auto_preview_cb.setChecked(self._project.auto_preview)
        self._singer_combo.setCurrentText(self._project.singer)
        self._personality_combo.setCurrentText(self._project.personality)
        self._mix_slider.setValue(self._project.personality_mix)
        self._mix_readout.setText(f"{self._project.personality_mix}%")
        self._theme.set_theme(self._project.theme)
        self._apply_theme()

        self._lyrics_panel.set_lyrics_text(self._project.lyrics)
        words = [t.word for t in self._project.tokens]
        self._lyrics_panel.display_tokens(words)
        for i, t in enumerate(self._project.tokens):
            if t.locked:
                self._lyrics_panel.set_token_locked(i, True)
        self._inspector_panel.clear_display()
        self._global_controls.set_tempo(self._project.tempo)
        self._global_controls.set_key(self._project.key)
        mode_btn = self._mode_btns.get(self._project.preview_mode)
        if mode_btn:
            mode_btn.setChecked(True)
        self._preview_mode = self._project.preview_mode
        self._selected_token_idx = -1
        self._tracks_panel.set_tracks(self._project.tracks)
        if self._project.active_book in self._book_names:
            idx = self._book_names.index(self._project.active_book)
            self._book_list.setCurrentRow(idx)
        self._push_undo()

    def _on_tempo(self, val: int) -> None:
        self._project.tempo = val
        self._console.log(f"Tempo: {val} BPM")

    def _on_key(self, key: str) -> None:
        self._project.key = key
        self._console.log(f"Key: {key}")

    def _on_voice_type(self, vtype: str) -> None:
        self._audio_synth.set_voice_type(vtype)
        self._console.log(f"Voice type: {vtype}")
        self._on_preview()

    def _on_range_selected(self, start: int, end: int) -> None:
        self._selection_range = (start, end)
        self._selected_token_idx = start
        self._scope_btns["Section"].setEnabled(True)
        count = end - start + 1
        words = [self._project.tokens[i].word for i in range(start, end + 1)
                 if i < len(self._project.tokens)]
        preview_text = " ".join(words[:4])
        if len(words) > 4:
            preview_text += "..."
        self._console.log(
            f"Range selected: [{start}..{end}] ({count} tokens) \"{preview_text}\""
        )
        if 0 <= start < len(self._project.tokens):
            t = self._project.tokens[start]
            self._inspector_panel.display_token(
                f"[{count} tokens]", t.duration_ms, t.loudness_pct,
                t.intensity, t.pitch_offset,
                t.delivery.value, t.bravado_subtype.value,
            )
        self._capture_panel.set_default_target(True)
        self._tracks_panel.set_assign_enabled(True)
        self._show_popover()

    def _on_selection_cleared(self) -> None:
        self._selection_range = None
        self._scope_btns["Section"].setEnabled(False)
        if self._popover and self._popover.isVisible():
            self._popover.close()
        self._inspector_panel.clear_display()
        self._selected_token_idx = -1
        self._tracks_panel.set_assign_enabled(False)
        self._console.log("Selection cleared")

    def _on_esc(self) -> None:
        if self._popover and self._popover.isVisible():
            self._popover.close()
            return
        if self._selection_range or self._selected_token_idx >= 0:
            self._lyrics_panel.clear_selection()

    def _show_popover(self) -> None:
        if not self._popover:
            self._popover = SelectionPopover()
            self._popover.apply_clicked.connect(self._on_popover_apply)
            self._popover.cancel_clicked.connect(self._on_popover_cancel)
            self._popover.scope_changed.connect(self._on_popover_scope)
            self._popover.mode_changed.connect(self._on_popover_mode)
            self._popover.preview_requested.connect(self._on_preview)

        scope = self._get_scope()
        self._popover.set_scope(scope if scope != "Section" else "Section")
        self._popover.set_mode(self._get_preview_mode())

        rng_rect = self._lyrics_panel.get_range_global_rect()
        if rng_rect:
            anchor = rng_rect.topLeft()
            self._popover.show_at(anchor, rng_rect.height())
        else:
            tok_rect = self._lyrics_panel.get_token_global_rect(self._selected_token_idx)
            if tok_rect:
                self._popover.show_at(tok_rect.topLeft(), tok_rect.height())

    def _on_popover_apply(self, params: dict) -> None:
        if not self._selection_range:
            return
        lo, hi = self._selection_range
        self._push_undo()
        applied: list[str] = []
        for i in range(lo, hi + 1):
            if not (0 <= i < len(self._project.tokens)):
                continue
            t = self._project.tokens[i]
            if "duration_ms" in params:
                t.duration_ms = params["duration_ms"]
            if "loudness_pct" in params:
                t.loudness_pct = params["loudness_pct"]
            if "intensity" in params:
                t.intensity = params["intensity"]
            if "pitch_offset" in params:
                t.pitch_offset = params["pitch_offset"]
            if "delivery" in params:
                t.delivery = DeliveryMode(params["delivery"])
            t.locked = True
            self._lyrics_panel.set_token_locked(i, True)
        if params:
            applied = list(params.keys())
        self._push_undo()
        self._console.log(
            f"Applied to range [{lo}..{hi}]: {', '.join(applied) if applied else 'lock only'}"
        )
        if self._popover:
            self._popover.close()

    def _on_popover_cancel(self) -> None:
        self._console.log("Popover cancelled")

    def _on_popover_scope(self, scope: str) -> None:
        btn = self._scope_btns.get(scope)
        if btn and btn.isEnabled():
            btn.setChecked(True)
        self._console.log(f"Popover scope: {scope}")

    def _on_popover_mode(self, mode: str) -> None:
        btn = self._mode_btns.get(mode)
        if btn and btn.isEnabled():
            btn.setChecked(True)
        self._preview_mode = mode
        self._project.preview_mode = mode
        self._console.log(f"Popover mode: {mode}")

    def _on_scope_changed(self, *args) -> None:
        self._console.log(f"Preview scope: {self._get_scope()}")

    def _on_mode_changed(self, *args) -> None:
        mode = self._get_preview_mode()
        self._preview_mode = mode
        self._project.preview_mode = mode
        self._console.log(f"Preview mode: {mode}")
        if mode == "Forward":
            self._on_preview()

    def _on_preroll(self, val: int) -> None:
        self._preroll_readout.setText(f"{val}ms")

    def _on_postroll(self, val: int) -> None:
        self._postroll_readout.setText(f"{val}ms")

    def _restore_state(self, state: dict) -> None:
        self._project = ProjectModel.from_dict(state)
        self._restore_from_project()

    def _on_capture_record(self) -> None:
        self._audio_recorder.max_duration_s = self._capture_panel.max_duration_s
        if self._audio_recorder.start_recording():
            self._capture_panel.set_recording(True)
            self._capture_panel.set_status("Recording...")
            self._console.log(
                f"Recording started (max {self._audio_recorder.max_duration_s}s)"
            )
            max_ms = int(self._audio_recorder.max_duration_s * 1000) + 500
            QTimer.singleShot(max_ms, self._auto_stop_recording)
        else:
            self._console.log("Recording failed to start")

    def _auto_stop_recording(self) -> None:
        if self._audio_recorder.is_recording:
            self._on_capture_stop()

    def _on_capture_stop(self) -> None:
        path = self._audio_recorder.stop_recording()
        self._capture_panel.set_recording(False)
        if path:
            self._last_capture_wav = path
            self._capture_panel.set_status(f"Captured: {os.path.basename(path)}")
            self._console.log(f"Recording saved: {path}")
            if self._audio_recorder.last_error:
                self._console.log(f"Note: {self._audio_recorder.last_error}")
        else:
            self._capture_panel.set_status("No audio captured")
            self._console.log(
                f"Recording failed: {self._audio_recorder.last_error or 'unknown error'}"
            )

    def _on_capture_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Audio File", "", "Audio Files (*.wav *.WAV)"
        )
        if path:
            dest = AudioRecorder.import_wav(path)
            if dest:
                self._last_capture_wav = dest
                self._capture_panel.set_status(f"Imported: {os.path.basename(path)}")
                self._console.log(f"Audio imported: {path} -> {dest}")
            else:
                self._console.log(f"Import failed: {path}")

    def _on_capture_analyze(self) -> None:
        if not self._last_capture_wav:
            self._console.log("No audio to analyze")
            self._capture_panel.set_status("No audio file loaded")
            return

        self._capture_panel.set_status("Analyzing...")
        self._console.log(f"Analyzing: {self._last_capture_wav}")
        self._log.info(f"Analyze started: {self._last_capture_wav}")

        try:
            result = self._dsp_analyzer.analyze_wav_file(self._last_capture_wav)
            analysis_dict = result.to_dict()
            self._last_analysis_dict = analysis_dict
            self._capture_panel.display_analysis(analysis_dict)

            params = self._param_mapper.map_to_params(result)
            self._capture_panel.display_mapped_params(params)

            self._capture_panel.set_status("Analysis complete")
            self._console.log(
                f"Analysis: pitch={result.pitch_hz:.1f}Hz, "
                f"RMS={result.rms_loudness:.4f}, "
                f"delivery={params.get('delivery', '?')}"
            )
            self._log.info(f"Analysis complete: pitch={result.pitch_hz:.1f}Hz")

            merged = dict(analysis_dict)
            merged["delivery"] = params.get("delivery", "Normal")
            feat_vec = compute_feature_vector(merged)
            confidence = {
                "pitch_confidence": analysis_dict.get("pitch_confidence", 1.0),
                "vibrato_confidence": analysis_dict.get("vibrato_confidence", 1.0),
            }
            matches = self._preset_store.find_closest(feat_vec, confidence, top_n=3)
            self._capture_panel.display_closest_matches(matches)
            if matches and matches[0][1] >= 0.80:
                self._console.log(f"Likely preset match: {matches[0][0]} ({matches[0][1]:.2f})")
            elif matches and matches[0][1] >= 0.60:
                self._console.log(f"Possible preset match: {matches[0][0]} ({matches[0][1]:.2f})")
            else:
                self._console.log("No close preset match found")

            if self._capture_panel.is_session_active:
                name = self._preset_store.generate_name()
                preset = StylePreset.from_mapped_params(name, params, analysis_dict)
                self._preset_store.add(preset)
                self._capture_panel.add_session_preset(name)
                self._console.log(f"Session preset created: {name}")
        except Exception:
            import sys, traceback
            exc_type, exc_value, exc_tb = sys.exc_info()
            self._log.error("Analyze failed", exc_info=True)
            self._console.log(f"Analysis failed: {exc_value}")
            self._capture_panel.set_status("Analysis failed")
            app_state = self._gather_app_state("Analyze")
            _path, fingerprint = write_crash_report(exc_type, exc_value, exc_tb, action="Analyze", app_state=app_state)
            case_folder = write_solution_folder(
                exc_type, exc_value, exc_tb, action="Analyze",
                app_state=app_state,
                analysis_results=self._last_analysis_dict,
                project_dict=self._project.to_dict(),
                selection_info=self._gather_selection_info(),
                ui_mode_info=self._gather_ui_mode_info(),
            )
            self._check_known_issue(fingerprint, case_folder)

    def _resolve_target_indices(self, target: str) -> list[int]:
        tokens = self._project.tokens
        if target == "Selected Range" and self._selection_range:
            lo, hi = self._selection_range
            return [i for i in range(lo, hi + 1) if 0 <= i < len(tokens)]
        elif target == "Forward" and 0 <= self._selected_token_idx < len(tokens):
            line_idx = tokens[self._selected_token_idx].line_index
            return [i for i in range(self._selected_token_idx, len(tokens))
                    if tokens[i].line_index == line_idx]
        elif 0 <= self._selected_token_idx < len(tokens):
            return [self._selected_token_idx]
        return []

    def _apply_params_to_indices(self, params: dict, indices: list[int]) -> None:
        for i in indices:
            t = self._project.tokens[i]
            if "loudness_pct" in params:
                t.loudness_pct = params["loudness_pct"]
            if "intensity" in params:
                t.intensity = params["intensity"]
            if "pitch_offset" in params:
                t.pitch_offset = params["pitch_offset"]
            if "duration_ms" in params:
                t.duration_ms = params["duration_ms"]
            if "delivery" in params:
                t.delivery = DeliveryMode(params["delivery"])

    def _on_preview_apply(self, params: dict, target: str) -> None:
        indices = self._resolve_target_indices(target)
        if not indices:
            self._console.log("No tokens to preview-apply")
            return
        self._preview_apply_backup = []
        for i in indices:
            t = self._project.tokens[i]
            self._preview_apply_backup.append({
                "idx": i,
                "loudness_pct": t.loudness_pct,
                "intensity": t.intensity,
                "pitch_offset": t.pitch_offset,
                "duration_ms": t.duration_ms,
                "delivery": t.delivery.value,
            })
        self._preview_apply_indices = indices
        self._apply_params_to_indices(params, indices)
        self._lyrics_panel.highlight_tokens(indices, "#ffc107")
        self._capture_panel.set_preview_active(True)
        self._console.log(f"Preview applied to {len(indices)} token(s) [{target}]")
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            t = self._project.tokens[self._selected_token_idx]
            self._inspector_panel.display_token(
                t.word, t.duration_ms, t.loudness_pct,
                t.intensity, t.pitch_offset,
                t.delivery.value, t.bravado_subtype.value,
            )

    def _on_commit_apply(self, params: dict, target: str) -> None:
        if self._preview_apply_backup is not None:
            self._push_undo()
            self._preview_apply_backup = None
            self._preview_apply_indices = []
            self._lyrics_panel.clear_highlight()
            self._capture_panel.set_preview_active(False)
            self._console.log("Preview committed (undo step created)")
        else:
            indices = self._resolve_target_indices(target)
            if not indices:
                self._console.log("No tokens to apply")
                return
            self._push_undo()
            self._apply_params_to_indices(params, indices)
            self._push_undo()
            self._console.log(f"Applied to {len(indices)} token(s) [{target}]")
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            t = self._project.tokens[self._selected_token_idx]
            self._inspector_panel.display_token(
                t.word, t.duration_ms, t.loudness_pct,
                t.intensity, t.pitch_offset,
                t.delivery.value, t.bravado_subtype.value,
            )

    def _on_revert_preview(self) -> None:
        if self._preview_apply_backup is None:
            return
        for snap in self._preview_apply_backup:
            i = snap["idx"]
            if 0 <= i < len(self._project.tokens):
                t = self._project.tokens[i]
                t.loudness_pct = snap["loudness_pct"]
                t.intensity = snap["intensity"]
                t.pitch_offset = snap["pitch_offset"]
                t.duration_ms = snap["duration_ms"]
                t.delivery = DeliveryMode(snap["delivery"])
        self._preview_apply_backup = None
        self._preview_apply_indices = []
        self._lyrics_panel.clear_highlight()
        self._capture_panel.set_preview_active(False)
        self._console.log("Preview reverted")
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            t = self._project.tokens[self._selected_token_idx]
            self._inspector_panel.display_token(
                t.word, t.duration_ms, t.loudness_pct,
                t.intensity, t.pitch_offset,
                t.delivery.value, t.bravado_subtype.value,
            )

    def _on_capture_apply(self, params: dict) -> None:
        if self._selection_range:
            lo, hi = self._selection_range
            self._push_undo()
            for i in range(lo, hi + 1):
                if 0 <= i < len(self._project.tokens):
                    t = self._project.tokens[i]
                    if "loudness_pct" in params:
                        t.loudness_pct = params["loudness_pct"]
                    if "intensity" in params:
                        t.intensity = params["intensity"]
                    if "pitch_offset" in params:
                        t.pitch_offset = params["pitch_offset"]
                    if "duration_ms" in params:
                        t.duration_ms = params["duration_ms"]
                    if "delivery" in params:
                        t.delivery = DeliveryMode(params["delivery"])
            self._push_undo()
            self._console.log(f"Capture params applied to range [{lo}..{hi}]")
        elif 0 <= self._selected_token_idx < len(self._project.tokens):
            idx = self._selected_token_idx
            self._push_undo()
            t = self._project.tokens[idx]
            if "loudness_pct" in params:
                t.loudness_pct = params["loudness_pct"]
            if "intensity" in params:
                t.intensity = params["intensity"]
            if "pitch_offset" in params:
                t.pitch_offset = params["pitch_offset"]
            if "duration_ms" in params:
                t.duration_ms = params["duration_ms"]
            if "delivery" in params:
                t.delivery = DeliveryMode(params["delivery"])
            self._push_undo()
            self._console.log(f"Capture params applied to token [{idx}]")
            self._inspector_panel.display_token(
                t.word, t.duration_ms, t.loudness_pct,
                t.intensity, t.pitch_offset,
                t.delivery.value, t.bravado_subtype.value,
            )
        else:
            self._console.log("No tokens selected to apply capture params")

    def _on_capture_preset_create(self, name: str, params: dict) -> None:
        if not name:
            name = self._preset_store.generate_name()
        preset = StylePreset.from_mapped_params(name, params, self._last_analysis_dict)
        self._preset_store.add(preset)
        self._console.log(f"Style preset saved: {name}")
        self._capture_panel.set_status(f"Preset saved: {name}")

    def _on_session_preset_accept(self, name: str) -> None:
        preset = self._preset_store.get(name)
        if preset:
            self._console.log(f"Session preset accepted: {name}")
        else:
            self._console.log(f"Preset not found: {name}")

    def _on_session_preset_rename(self, old_name: str, new_name: str) -> None:
        self._preset_store.rename(old_name, new_name)
        self._console.log(f"Preset renamed: {old_name} -> {new_name}")

    def _on_use_preset(self, name: str) -> None:
        preset = self._preset_store.get(name)
        if not preset:
            self._console.log(f"Preset not found: {name}")
            return
        params = {
            "loudness_pct": preset.loudness_pct,
            "intensity": preset.intensity,
            "pitch_offset": preset.pitch_offset,
            "duration_ms": preset.duration_ms,
            "delivery": preset.delivery,
        }
        target = self._capture_panel.get_apply_target()
        indices = self._resolve_target_indices(target)
        if not indices:
            self._console.log("No tokens selected for preset application")
            return
        self._push_undo()
        self._apply_params_to_indices(params, indices)
        self._console.log(f"Applied preset '{name}' to {len(indices)} token(s) [{target}]")
        if 0 <= self._selected_token_idx < len(self._project.tokens):
            t = self._project.tokens[self._selected_token_idx]
            self._inspector_panel.display_token(
                t.word, t.duration_ms, t.loudness_pct,
                t.intensity, t.pitch_offset,
                t.delivery.value, t.bravado_subtype.value,
            )

    def _on_create_new_preset(self) -> None:
        self._capture_panel._create_preset_cb.setChecked(True)
        self._capture_panel._preset_name_edit.setFocus()
        self._console.log("Creating new preset (fill name and click Save Preset)")

    def _on_compare_details(self, name: str) -> None:
        preset = self._preset_store.get(name)
        if not preset or not self._last_analysis_dict:
            self._console.log("Cannot compare — missing analysis or preset")
            return
        merged = dict(self._last_analysis_dict)
        mapped = self._param_mapper.map_to_params(
            self._dsp_analyzer.analyze_wav_file(self._last_capture_wav)
        ) if self._last_capture_wav else {}
        merged["delivery"] = mapped.get("delivery", "Normal")
        current_vec = compute_feature_vector(merged)
        preset_vec = preset.feature_vector
        if not preset_vec:
            self._console.log(f"Preset '{name}' has no feature vector")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Compare: Current vs {name}")
        dlg.setMinimumSize(450, 350)
        layout = QVBoxLayout(dlg)
        detail = QTextEdit()
        detail.setReadOnly(True)
        lines = [f"Feature comparison: Current analysis vs preset '{name}'", ""]
        lines.append(f"{'Feature':<22} {'Current':>8} {'Preset':>8} {'Delta':>8}")
        lines.append("-" * 50)
        for key in FEATURE_KEYS:
            c = current_vec.get(key, 0.0)
            p = preset_vec.get(key, 0.0)
            d = abs(c - p)
            marker = " ***" if d > 0.2 else ""
            lines.append(f"{key:<22} {c:>8.3f} {p:>8.3f} {d:>8.3f}{marker}")
        lines.append("")
        lines.append("*** = large delta (>0.2), likely driving score difference")
        detail.setPlainText("\n".join(lines))
        layout.addWidget(detail)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

    def _gather_app_state(self, action: str) -> dict:
        return {
            "action": action,
            "voice_type": self._audio_synth._voice_type if hasattr(self._audio_synth, "_voice_type") else "unknown",
            "preview_mode": self._preview_mode,
            "scope": self._get_scope(),
            "selected_token_idx": self._selected_token_idx,
            "render_mode": self._project.render_mode,
            "engine_quality": self._project.engine_quality,
            "singer": self._project.singer,
            "tempo": self._project.tempo,
            "key": self._project.key,
        }

    def _gather_selection_info(self) -> dict:
        info: dict = {
            "selected_token_idx": self._selected_token_idx,
            "selection_range": None,
        }
        if self._selection_range:
            lo, hi = self._selection_range
            info["selection_range"] = [lo, hi]
            words = [
                self._project.tokens[i].word
                for i in range(lo, min(hi + 1, len(self._project.tokens)))
            ]
            info["selected_words"] = words
        elif 0 <= self._selected_token_idx < len(self._project.tokens):
            info["selected_words"] = [self._project.tokens[self._selected_token_idx].word]
        return info

    def _gather_ui_mode_info(self) -> dict:
        return {
            "preview_mode": self._preview_mode,
            "scope": self._get_scope(),
            "preroll_ms": self._preroll_slider.value(),
            "postroll_ms": self._postroll_slider.value(),
            "snap_to_words": self._snap_cb.isChecked(),
            "auto_preview": self._auto_preview_cb.isChecked(),
            "theme": self._theme.current,
        }

    def _on_export_debug(self) -> None:
        self._log.info("Export Debug Bundle requested")
        try:
            path = export_debug_bundle()
            self._console.log(f"Debug bundle exported: {path}")
            self._log.info(f"Debug bundle exported: {path}")
        except Exception:
            import sys as _sys
            exc_type, exc_value, exc_tb = _sys.exc_info()
            self._log.error("Export debug bundle failed", exc_info=True)
            self._console.log(f"Export failed: {exc_value}")

    def _on_export_fixpack(self) -> None:
        self._log.info("Export Fix Pack requested")
        try:
            path = export_fix_pack()
            self._console.log(f"Fix pack exported: {path}")
            self._log.info(f"Fix pack exported: {path}")
            QMessageBox.information(self, "Export Fix Pack", f"Fix pack saved to:\n{path}")
        except Exception:
            import sys as _sys
            self._log.error("Export fix pack failed", exc_info=True)
            self._console.log(f"Export fix pack failed: {_sys.exc_info()[1]}")

    def _on_import_fixpack(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Fix Pack", "", "Zip Files (*.zip)"
        )
        if not path:
            return
        self._log.info(f"Import Fix Pack: {path}")
        try:
            count = import_fix_pack(path)
            self._console.log(f"Fix pack imported: {count} new/updated fixes")
            self._log.info(f"Fix pack imported: {count} fixes from {path}")
            QMessageBox.information(
                self, "Import Fix Pack",
                f"Imported {count} new/updated fix(es) from:\n{path}",
            )
        except Exception:
            import sys as _sys
            self._log.error("Import fix pack failed", exc_info=True)
            self._console.log(f"Import fix pack failed: {_sys.exc_info()[1]}")
            QMessageBox.warning(self, "Import Failed", str(_sys.exc_info()[1]))

    def _check_known_issue(self, fingerprint: str, case_folder: str) -> None:
        fix = lookup_fix(fingerprint)
        if fix and fix.get("title"):
            self._log.info(f"Known issue detected: {fix['title']} [fp={fingerprint}]")
            self._console.log(f"Known issue: {fix['title']}")
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Known Issue Detected")
            dlg.setIcon(QMessageBox.Icon.Information)
            text = (
                f"<b>{fix['title']}</b><br><br>"
                f"<b>Root cause:</b> {fix.get('root_cause', '(none)')}<br>"
                f"<b>Fix steps:</b> {fix.get('fix_steps', '(none)')}<br>"
                f"<b>Verification:</b> {fix.get('verification', '(none)')}"
            )
            dlg.setText(text)
            view_btn = dlg.addButton("View Fix", QMessageBox.ButtonRole.AcceptRole)
            if fix.get("auto_fix_script"):
                apply_btn = dlg.addButton("Apply Fix", QMessageBox.ButtonRole.ActionRole)
            else:
                apply_btn = None
            dlg.addButton("Dismiss", QMessageBox.ButtonRole.RejectRole)
            dlg.exec()
            clicked = dlg.clickedButton()
            if clicked == view_btn:
                self._show_fix_detail(fix)
            elif apply_btn and clicked == apply_btn:
                confirm = QMessageBox.question(
                    self, "Confirm Apply Fix",
                    f"Run auto-fix script?\n{fix['auto_fix_script']}",
                )
                if confirm == QMessageBox.StandardButton.Yes:
                    self._console.log(f"Auto-fix applied: {fix['auto_fix_script']}")
                    self._log.info(f"Auto-fix applied: {fix['auto_fix_script']}")
        else:
            self._console.log(f"New issue recorded [fp={fingerprint}]")
            self._show_save_fix_dialog(fingerprint, case_folder)

    def _show_fix_detail(self, fix: dict) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Fix: {fix.get('title', 'Unknown')}")
        dlg.setMinimumSize(500, 350)
        layout = QVBoxLayout(dlg)
        detail = QTextEdit()
        detail.setReadOnly(True)
        lines = [
            f"Title: {fix.get('title', '')}",
            f"Fingerprint: {fix.get('fingerprint', '')}",
            f"Created: {fix.get('created', '')}",
            "",
            f"Root Cause:\n{fix.get('root_cause', '')}",
            "",
            f"Fix Steps:\n{fix.get('fix_steps', '')}",
            "",
            f"Verification:\n{fix.get('verification', '')}",
        ]
        if fix.get("auto_fix_script"):
            lines.append(f"\nAuto-fix script: {fix['auto_fix_script']}")
        detail.setPlainText("\n".join(lines))
        layout.addWidget(detail)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

    def _show_save_fix_dialog(self, fingerprint: str, case_folder: str) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Save Fix for This Issue")
        dlg.setMinimumSize(450, 400)
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel(f"Fingerprint: {fingerprint}"))
        layout.addWidget(QLabel(f"Case folder: {case_folder}"))

        form = QFormLayout()
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("Short description of the fix")
        form.addRow("Title:", title_edit)

        root_cause_edit = QTextEdit()
        root_cause_edit.setPlaceholderText("What caused the issue?")
        root_cause_edit.setMaximumHeight(80)
        form.addRow("Root Cause:", root_cause_edit)

        fix_steps_edit = QTextEdit()
        fix_steps_edit.setPlaceholderText("Steps taken to fix it")
        fix_steps_edit.setMaximumHeight(80)
        form.addRow("Fix Steps:", fix_steps_edit)

        verification_edit = QTextEdit()
        verification_edit.setPlaceholderText("How to verify the fix works")
        verification_edit.setMaximumHeight(80)
        form.addRow("Verification:", verification_edit)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            title = title_edit.text().strip()
            if not title:
                self._console.log("Fix not saved — title is required")
                return
            save_fix(
                fingerprint=fingerprint,
                case_folder=case_folder,
                title=title,
                root_cause=root_cause_edit.toPlainText().strip(),
                fix_steps=fix_steps_edit.toPlainText().strip(),
                verification=verification_edit.toPlainText().strip(),
            )
            self._console.log(f"Fix saved: {title} [fp={fingerprint}]")
            self._log.info(f"Fix saved: {title} [fp={fingerprint}]")

    def _on_track_selected(self, track_id: str) -> None:
        self._update_track_outlines()
        for t in self._project.tracks:
            if t.id == track_id:
                self._console.log(f"Track selected: {t.name}")
                return

    def _on_assign_to_track(self, track_id: str) -> None:
        if not self._selection_range:
            self._console.log("No range selected for track assignment")
            return
        lo, hi = self._selection_range
        assignment = TrackAssignment(track_id, lo, hi)
        self._project.track_assignments.append(assignment)
        track_name = ""
        for t in self._project.tracks:
            if t.id == track_id:
                track_name = t.name
                break
        self._console.log(f"Assigned tokens {lo}\u2013{hi} to {track_name}")
        self._log.info(f"Track assignment: tokens [{lo},{hi}] -> {track_name}")
        self._update_track_outlines()

    def _get_track_token_indices(self, track_id: str) -> set[int]:
        indices: set[int] = set()
        for a in self._project.track_assignments:
            if a.track_id == track_id:
                for i in range(a.start_index, a.end_index + 1):
                    indices.add(i)
        return indices

    def _get_audible_indices(self) -> set[int] | None:
        tracks = self._project.tracks
        soloed = [t for t in tracks if t.solo and t.track_type != TrackType.MASTER]
        if soloed:
            indices: set[int] = set()
            for t in soloed:
                indices |= self._get_track_token_indices(t.id)
            return indices
        muted_ids = {t.id for t in tracks if not t.enabled and t.track_type != TrackType.MASTER}
        if not muted_ids:
            return None
        excluded: set[int] = set()
        for a in self._project.track_assignments:
            if a.track_id in muted_ids:
                for i in range(a.start_index, a.end_index + 1):
                    excluded.add(i)
        if not excluded:
            return None
        all_indices = set(range(len(self._project.tokens)))
        return all_indices - excluded

    def _filter_sequence_by_track(self, sequence: list[int]) -> list[int]:
        scope = self._tracks_panel.get_playback_scope()
        if scope == "current":
            track_id = self._tracks_panel.get_selected_track_id()
            if track_id:
                allowed = self._get_track_token_indices(track_id)
                if allowed:
                    return [i for i in sequence if i in allowed]
            return sequence
        audible = self._get_audible_indices()
        if audible is None:
            return sequence
        return [i for i in sequence if i in audible]

    def _update_track_outlines(self) -> None:
        self._lyrics_panel.clear_highlight()
        track_id = self._tracks_panel.get_selected_track_id()
        if not track_id:
            return
        indices = self._get_track_token_indices(track_id)
        if not indices:
            return
        color = "#4fc3f7"
        for t in self._project.tracks:
            if t.id == track_id and t.color:
                color = t.color
                break
        multi_track: set[int] = set()
        for idx in indices:
            count = 0
            for a in self._project.track_assignments:
                if a.start_index <= idx <= a.end_index:
                    count += 1
            if count > 1:
                multi_track.add(idx)
        outline_indices = [i for i in sorted(indices) if i not in multi_track]
        multi_indices = sorted(multi_track)
        if outline_indices:
            for i in outline_indices:
                if 0 <= i < self._lyrics_panel.token_count():
                    btn = self._lyrics_panel._token_buttons[i]
                    current = btn.styleSheet()
                    if "ffc107" not in current:
                        btn.setStyleSheet(
                            f"QPushButton {{ font-size: 12px; "
                            f"border: 2px solid {color}; border-radius: 4px; "
                            f"padding: 3px 6px; background: transparent; }}"
                            f"QPushButton:hover {{ border-color: #00bcd4; background: #3a4a4a; }}"
                        )
        if multi_indices:
            for i in multi_indices:
                if 0 <= i < self._lyrics_panel.token_count():
                    btn = self._lyrics_panel._token_buttons[i]
                    current = btn.styleSheet()
                    if "ffc107" not in current:
                        btn.setStyleSheet(
                            "QPushButton { font-size: 12px; "
                            "border: 2px dashed #ff9800; border-radius: 4px; "
                            "padding: 3px 6px; background: transparent; }"
                            "QPushButton:hover { border-color: #00bcd4; background: #3a4a4a; }"
                        )

    def _on_export_stems(self) -> None:
        self._sync_project()
        if not self._project.project_folder:
            self._console.log("Export Stems: no project folder set. Use Save As first.")
            return
        stems_dir = os.path.join(self._project.project_folder, "stems")
        os.makedirs(stems_dir, exist_ok=True)
        tokens = self._project.tokens
        if not tokens:
            self._console.log("Export Stems: no tokens to export")
            return
        exported: list[str] = []
        master_samples: list[float] = []
        from engines.audio_synth import _synthesize_vocal, _write_wav, SAMPLE_RATE
        from engines.preview_engine import PreviewQuality
        voice_id = self._voice_manager.active_id
        voice_type = self._audio_synth.voice_type
        quality = PreviewQuality.HIGH
        for track in self._project.tracks:
            if track.track_type == TrackType.MASTER:
                continue
            if not track.enabled:
                continue
            track_indices = self._get_track_token_indices(track.id)
            if not track_indices:
                continue
            track_samples: list[float] = []
            for idx in sorted(track_indices):
                if idx >= len(tokens):
                    continue
                t = tokens[idx]
                samples = _synthesize_vocal(
                    t.word, t.duration_ms, t.loudness_pct,
                    t.intensity, t.pitch_offset,
                    t.delivery.value, voice_id, voice_type, quality,
                )
                track_samples.extend(samples)
                gap = int(0.05 * SAMPLE_RATE)
                track_samples.extend([0.0] * gap)
            if not track_samples:
                continue
            safe_name = track.name.lower().replace(" ", "_")
            wav_path = os.path.join(stems_dir, f"{safe_name}.wav")
            wav_data = _write_wav(track_samples)
            with open(wav_path, "wb") as f:
                f.write(wav_data)
            exported.append(wav_path)
            self._log.info(f"Exported stem: {wav_path}")
            while len(master_samples) < len(track_samples):
                master_samples.append(0.0)
            for i, s in enumerate(track_samples):
                master_samples[i] += s
        if master_samples:
            peak = max(abs(s) for s in master_samples) or 1.0
            if peak > 1.0:
                master_samples = [s / peak for s in master_samples]
            master_path = os.path.join(stems_dir, "master.wav")
            wav_data = _write_wav(master_samples)
            with open(master_path, "wb") as f:
                f.write(wav_data)
            exported.append(master_path)
            self._log.info(f"Exported master: {master_path}")
        for p in exported:
            self._console.log(f"Exported: {p}")
        self._console.log(f"Stem export complete: {len(exported)} files to {stems_dir}")

    def _build_performance_script(self) -> dict:
        import json as _json
        self._sync_project()
        tokens = self._project.tokens
        voice_type = self._audio_synth.voice_type
        script: dict = {
            "version": "1.0",
            "project": {
                "name": os.path.basename(self._project.project_folder) if self._project.project_folder else "Untitled",
                "tempo": self._project.tempo,
                "key": self._project.key,
            },
            "preview_settings": {
                "mode": self._preview_mode,
                "scope": self._get_scope(),
            },
            "tracks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.track_type.value,
                    "muted": not t.enabled,
                    "solo": t.solo,
                    "voice_profile_id": t.voice_profile_id,
                }
                for t in self._project.tracks
            ],
            "track_assignments": [a.to_dict() for a in self._project.track_assignments],
            "tokens": [],
        }
        vowel_map = {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U"}
        for i, tok in enumerate(tokens):
            first_vowel = ""
            for ch in tok.word.lower():
                if ch in vowel_map:
                    first_vowel = vowel_map[ch]
                    break
            script["tokens"].append({
                "text": tok.word,
                "index": tok.index,
                "duration_ms": tok.duration_ms,
                "loudness": tok.loudness_pct,
                "intensity": tok.intensity,
                "pitch_offset": tok.pitch_offset,
                "delivery": tok.delivery.value,
                "vowel": first_vowel or "A",
                "voice_type": voice_type,
                "line_index": tok.line_index,
            })
        return script

    def _on_export_script(self) -> None:
        import json as _json
        self._sync_project()
        if not self._project.project_folder:
            self._console.log("Export Script: no project folder. Use Save As first.")
            return
        exports_dir = os.path.join(self._project.project_folder, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        script = self._build_performance_script()
        out_path = os.path.join(exports_dir, "performance_script.json")
        with open(out_path, "w", encoding="utf-8") as f:
            _json.dump(script, f, indent=2)
        self._log.info(f"Performance script exported: {out_path}")
        self._console.log(f"Performance script exported: {out_path}")

    def _on_add_master_render_job(self) -> None:
        tokens = self._project.tokens
        if not tokens:
            self._console.log("Render: no tokens")
            return
        start = 0
        end = len(tokens) - 1
        if self._selection_range:
            start, end = self._selection_range
        renders_dir = os.path.join(self._project.project_folder, "audio", "renders") if self._project.project_folder else ""
        job = RenderJob(
            target=RenderTarget.MASTER,
            track_name="Master",
            token_start=start,
            token_end=end,
            output_path=os.path.join(renders_dir, f"master_{start}_{end}.wav") if renders_dir else "",
        )
        self._render_jobs.append(job)
        self._render_panel.set_jobs(self._render_jobs)
        self._console.log(f"Render job added: {job.label()}")

    def _on_add_track_render_job(self) -> None:
        track_id = self._tracks_panel.get_selected_track_id()
        if not track_id:
            self._console.log("Render: no track selected")
            return
        track = None
        for t in self._project.tracks:
            if t.id == track_id:
                track = t
                break
        if not track:
            return
        indices = self._get_track_token_indices(track_id)
        if not indices:
            self._console.log(f"Render: no tokens assigned to {track.name}")
            return
        start = min(indices)
        end = max(indices)
        renders_dir = os.path.join(self._project.project_folder, "audio", "renders") if self._project.project_folder else ""
        safe_name = track.name.lower().replace(" ", "_")
        job = RenderJob(
            target=RenderTarget.TRACK,
            track_id=track_id,
            track_name=track.name,
            token_start=start,
            token_end=end,
            output_path=os.path.join(renders_dir, f"{safe_name}_{start}_{end}.wav") if renders_dir else "",
        )
        self._render_jobs.append(job)
        self._render_panel.set_jobs(self._render_jobs)
        self._console.log(f"Render job added: {job.label()}")

    def _execute_render_job(self, job: RenderJob) -> None:
        from engines.audio_synth import _synthesize_vocal, _write_wav, SAMPLE_RATE
        from engines.preview_engine import PreviewQuality
        tokens = self._project.tokens
        if not tokens:
            job.status = RenderStatus.FAILED
            job.error = "No tokens"
            return
        job.status = RenderStatus.RUNNING
        self._render_panel.refresh()
        voice_id = self._voice_manager.active_id
        voice_type = self._audio_synth.voice_type
        quality = PreviewQuality.HIGH
        try:
            if job.target == RenderTarget.MASTER:
                indices = list(range(job.token_start, min(job.token_end + 1, len(tokens))))
            else:
                track_indices = self._get_track_token_indices(job.track_id)
                indices = sorted(i for i in track_indices if job.token_start <= i <= job.token_end)
            if not indices:
                job.status = RenderStatus.FAILED
                job.error = "No matching tokens"
                return
            samples: list[float] = []
            for idx in indices:
                if idx >= len(tokens):
                    continue
                t = tokens[idx]
                seg = _synthesize_vocal(
                    t.word, t.duration_ms, t.loudness_pct,
                    t.intensity, t.pitch_offset,
                    t.delivery.value, voice_id, voice_type, quality,
                )
                samples.extend(seg)
                gap = int(0.05 * SAMPLE_RATE)
                samples.extend([0.0] * gap)
            if not samples:
                job.status = RenderStatus.FAILED
                job.error = "Empty render"
                return
            if job.output_path:
                os.makedirs(os.path.dirname(job.output_path), exist_ok=True)
                wav_data = _write_wav(samples)
                with open(job.output_path, "wb") as f:
                    f.write(wav_data)
            job.status = RenderStatus.DONE
            self._log.info(f"Render complete: {job.output_path}")
            self._console.log(f"Render done: {job.label()} -> {job.output_path}")
        except Exception as exc:
            job.status = RenderStatus.FAILED
            job.error = str(exc)
            self._console.log(f"Render failed: {job.label()} — {exc}")

    def _on_run_render_job(self, job_id: str) -> None:
        for job in self._render_jobs:
            if job.id == job_id and job.status in (RenderStatus.PENDING, RenderStatus.FAILED):
                self._execute_render_job(job)
                break
        self._render_panel.refresh()

    def _on_run_all_render_jobs(self) -> None:
        for job in self._render_jobs:
            if job.status in (RenderStatus.PENDING, RenderStatus.FAILED):
                self._execute_render_job(job)
        self._render_panel.refresh()
        self._console.log(f"Render queue complete: {len(self._render_jobs)} jobs processed")

    def _on_cancel_render_job(self, job_id: str) -> None:
        for job in self._render_jobs:
            if job.id == job_id and job.status == RenderStatus.PENDING:
                job.status = RenderStatus.CANCELLED
                self._console.log(f"Render cancelled: {job.label()}")
                break
        self._render_panel.refresh()

    def _on_import_audio(self) -> None:
        if not self._project.project_folder:
            self._console.log("Import: no project folder. Use Save As first.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Song Audio", "",
            "Audio Files (*.wav *.mp3 *.m4a);;All Files (*)",
        )
        if not path:
            return
        imports_dir = os.path.join(self._project.project_folder, "audio", "imports")
        os.makedirs(imports_dir, exist_ok=True)
        dest = os.path.join(imports_dir, os.path.basename(path))
        shutil.copy2(path, dest)
        self._imported_audio_path = dest
        self._import_panel.set_audio_label(os.path.basename(dest))
        self._console.log(f"Audio imported: {dest}")
        self._log.info(f"Audio imported: {dest}")
        lyrics = self._lyrics_panel.get_lyrics_text()
        if lyrics:
            self._import_panel.set_lyrics_text(lyrics)

    def _on_run_alignment(self) -> None:
        import json as _json
        if not self._imported_audio_path:
            self._console.log("Align: no audio imported")
            return
        lyrics_text = self._import_panel.get_lyrics_text()
        if not lyrics_text:
            self._console.log("Align: no lyrics provided")
            return
        words = lyrics_text.split()
        self._console.log(f"Running alignment on {len(words)} words...")
        alignment = self._alignment_engine.forced_align(self._imported_audio_path, words)
        self._last_alignment = alignment
        word_dicts = [w.to_dict() for w in alignment.words]
        self._import_panel.set_alignment_words(word_dicts)
        if self._project.project_folder:
            exports_dir = os.path.join(self._project.project_folder, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            align_path = os.path.join(exports_dir, "alignment.json")
            with open(align_path, "w", encoding="utf-8") as f:
                _json.dump(alignment.to_dict(), f, indent=2)
            self._console.log(f"Alignment saved: {align_path}")
        self._console.log(f"Alignment complete: {len(alignment.words)} words, method={alignment.method}")

    def _on_auto_fill_tokens(self) -> None:
        if not self._last_alignment:
            self._console.log("Auto-fill: run alignment first")
            return
        if not self._imported_audio_path:
            self._console.log("Auto-fill: no audio imported")
            return
        alignment = self._last_alignment
        lyrics_text = self._import_panel.get_lyrics_text()
        if not lyrics_text:
            self._console.log("Auto-fill: no lyrics")
            return
        if not self._project.tokens:
            self._lyrics_panel.set_lyrics_text(lyrics_text)
            self._on_tokenize(lyrics_text)
        self._sync_project()
        tokens = self._project.tokens
        if not tokens:
            self._console.log("Auto-fill: no tokens after tokenize")
            return
        self._push_undo()
        word_analyses = self._alignment_engine.analyze_word_segments(
            self._imported_audio_path, alignment,
        )
        mapper = TokenParameterMapper()
        matched = 0
        low_conf = 0
        for i, tok in enumerate(tokens):
            best_idx = -1
            best_score = -1.0
            tok_lower = tok.word.lower().strip(".,!?;:'\"()-")
            for j, (aw, _analysis) in enumerate(word_analyses):
                aw_lower = aw.word.lower().strip(".,!?;:'\"()-")
                if tok_lower == aw_lower:
                    score = 2.0
                    if abs(i - j) < 3:
                        score += 1.0
                    if score > best_score:
                        best_score = score
                        best_idx = j
            if best_idx < 0 and i < len(word_analyses):
                best_idx = i
                best_score = 0.5
            if best_idx >= 0:
                aw, analysis = word_analyses[best_idx]
                tok.duration_ms = max(50, min(2000, int(aw.duration_ms)))
                if analysis.rms_loudness > 0:
                    params = mapper.map_to_params(analysis)
                    tok.loudness_pct = params["loudness_pct"]
                    tok.intensity = params["intensity"]
                    if analysis.pitch_confidence > 0.5:
                        tok.pitch_offset = params["pitch_offset"]
                    tok.delivery = DeliveryMode(params["delivery"])
                matched += 1
                if aw.confidence < 0.6:
                    low_conf += 1
        self._lyrics_panel.display_tokens([t.word for t in tokens])
        if self._selected_token_idx >= 0 and self._selected_token_idx < len(tokens):
            self._on_token_selected(self._selected_token_idx)
        target_name = self._import_panel.get_selected_track()
        target_track = None
        for t in self._project.tracks:
            if t.name == target_name:
                target_track = t
                break
        if target_track and tokens:
            assignment = TrackAssignment(
                track_id=target_track.id,
                start_index=0,
                end_index=len(tokens) - 1,
                notes=f"Auto-filled from {os.path.basename(self._imported_audio_path)}",
            )
            self._project.track_assignments.append(assignment)
            self._update_track_outlines()
            self._console.log(f"Assigned tokens [0-{len(tokens)-1}] to {target_track.name}")
        self._on_export_script()
        status = f"Auto-fill: {matched}/{len(tokens)} tokens mapped"
        if low_conf > 0:
            status += f", {low_conf} low confidence"
        self._import_panel.set_status(status)
        self._console.log(status)
        self._log.info(status)

    def _on_import_reference(self) -> None:
        if not self._project.project_folder:
            self._console.log("Reference: no project folder. Use Save As first.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Reference Song", "",
            "Audio Files (*.wav *.mp3 *.m4a);;All Files (*)",
        )
        if not path:
            return
        ref_dir = os.path.join(self._project.project_folder, "audio", "reference")
        os.makedirs(ref_dir, exist_ok=True)
        dest = os.path.join(ref_dir, os.path.basename(path))
        shutil.copy2(path, dest)
        self._ref_audio_path = dest
        self._reference_panel.set_reference_label(os.path.basename(dest))
        self._console.log(f"Reference imported: {dest}")
        self._log.info(f"Reference imported: {dest}")

    def _on_import_vocal_stem(self) -> None:
        if not self._project.project_folder:
            self._console.log("Reference: no project folder. Use Save As first.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Vocal Stem", "",
            "Audio Files (*.wav *.mp3 *.m4a);;All Files (*)",
        )
        if not path:
            return
        ref_dir = os.path.join(self._project.project_folder, "audio", "reference")
        os.makedirs(ref_dir, exist_ok=True)
        dest = os.path.join(ref_dir, "stem_" + os.path.basename(path))
        shutil.copy2(path, dest)
        self._ref_stem_path = dest
        self._reference_panel.set_stem_label(f"Stem: {os.path.basename(path)}")
        self._console.log(f"Vocal stem imported: {dest}")

    def _on_extract_template(self) -> None:
        ref_mode = self._reference_panel.get_reference_mode()
        if ref_mode == "Vocal Stem" and self._ref_stem_path:
            audio_path = self._ref_stem_path
        elif ref_mode == "Dual" and self._ref_stem_path:
            audio_path = self._ref_stem_path
        elif self._ref_audio_path:
            audio_path = self._ref_audio_path
        else:
            self._console.log("Extract: no reference audio loaded")
            return
        lyrics_text = self._lyrics_panel.get_lyrics_text()
        if not lyrics_text:
            lyrics_text = self._import_panel.get_lyrics_text()
        if not lyrics_text:
            self._console.log("Extract: no lyrics available. Paste lyrics first.")
            return
        words = lyrics_text.split()
        tone = self._reference_panel.get_emotional_tone()
        if tone and tone not in self._template_store.all_tones():
            self._template_store.add_custom_tone(tone)
            self._reference_panel.set_tones(self._template_store.all_tones())
        name, ok = QInputDialog.getText(self, "Template Name", "Name for this template:")
        if not ok or not name.strip():
            return
        name = name.strip()
        self._console.log(f"Extracting template '{name}' from {len(words)} words...")
        tpl = self._template_extractor.extract(
            audio_path, words, name=name,
            reference_mode=ref_mode, emotional_tone=tone,
        )
        self._template_store.add_template(tpl)
        self._reference_panel.set_templates(self._template_store.list_template_names())
        if self._project.project_folder:
            import json as _json
            exports_dir = os.path.join(self._project.project_folder, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            tpl_path = os.path.join(exports_dir, "reference_template.json")
            with open(tpl_path, "w", encoding="utf-8") as f:
                _json.dump(tpl.to_dict(), f, indent=2)
            self._console.log(f"Template saved: {tpl_path}")
        self._reference_panel.set_status(
            f"Extracted: tempo={tpl.tempo_estimate} BPM, "
            f"{tpl.word_count} words, tone={tpl.emotional_tone}"
        )
        self._console.log(f"Template '{name}' extracted: {tpl.word_count} words, "
                          f"tempo={tpl.tempo_estimate}, tone={tpl.emotional_tone}")

    def _apply_template_to_tokens(self, tpl: ReferenceTemplate) -> int:
        tokens = self._project.tokens
        if not tokens:
            return 0
        self._push_undo()
        defaults = tpl.token_defaults
        count = 0
        for tok in tokens:
            tok.duration_ms = defaults.get("duration_ms", 500)
            tok.loudness_pct = defaults.get("loudness_pct", 100)
            tok.intensity = defaults.get("intensity", 50)
            tok.pitch_offset = defaults.get("pitch_offset", 0)
            delivery_str = defaults.get("delivery", "Normal")
            tok.delivery = DeliveryMode(delivery_str)
            count += 1
        self._lyrics_panel.display_tokens([t.word for t in tokens])
        if self._selected_token_idx >= 0 and self._selected_token_idx < len(tokens):
            self._on_token_selected(self._selected_token_idx)
        return count

    def _on_apply_template(self, name: str) -> None:
        tpl = self._template_store.get_template(name)
        if not tpl:
            self._console.log(f"Template '{name}' not found")
            return
        count = self._apply_template_to_tokens(tpl)
        self._reference_panel.set_status(f"Applied '{name}' to {count} tokens")
        self._console.log(f"Template '{name}' applied to {count} tokens")

    def _on_reapply_template(self, name: str) -> None:
        tpl = self._template_store.get_template(name)
        if not tpl:
            self._console.log(f"Template '{name}' not found")
            return
        tokens = self._project.tokens
        if not tokens:
            self._console.log("Reapply: no tokens")
            return
        if self._selection_range:
            start, end = self._selection_range
        elif self._selected_token_idx >= 0:
            start = end = self._selected_token_idx
        else:
            self._console.log("Reapply: select a token or range first")
            return
        self._push_undo()
        defaults = tpl.token_defaults
        count = 0
        for i in range(start, min(end + 1, len(tokens))):
            tok = tokens[i]
            tok.duration_ms = defaults.get("duration_ms", 500)
            tok.loudness_pct = defaults.get("loudness_pct", 100)
            tok.intensity = defaults.get("intensity", 50)
            tok.pitch_offset = defaults.get("pitch_offset", 0)
            tok.delivery = DeliveryMode(defaults.get("delivery", "Normal"))
            count += 1
        self._lyrics_panel.display_tokens([t.word for t in tokens])
        if self._selected_token_idx >= 0 and self._selected_token_idx < len(tokens):
            self._on_token_selected(self._selected_token_idx)
        self._reference_panel.set_status(f"Reapplied '{name}' to {count} tokens [{start}-{end}]")
        self._console.log(f"Template '{name}' reapplied to tokens [{start}-{end}]")

    def _on_switch_tone(self, template_name: str, new_tone: str) -> None:
        tpl = self._template_store.get_template(template_name)
        if not tpl:
            self._console.log(f"Template '{template_name}' not found")
            return
        old_tone = tpl.emotional_tone
        tpl.emotional_tone = new_tone
        if new_tone not in self._template_store.all_tones():
            self._template_store.add_custom_tone(new_tone)
            self._reference_panel.set_tones(self._template_store.all_tones())
        tone_modifiers = {
            "loving": {"intensity": -10, "loudness_pct": -10, "delivery": "Normal"},
            "compassionate": {"intensity": -5, "loudness_pct": 0, "delivery": "Normal"},
            "reverent": {"intensity": -15, "loudness_pct": -15, "delivery": "Whisper"},
            "sorrowful": {"intensity": -20, "loudness_pct": -20, "delivery": "Whisper"},
            "joyful": {"intensity": 10, "loudness_pct": 10, "delivery": "Normal"},
            "triumphant": {"intensity": 20, "loudness_pct": 15, "delivery": "Bravado"},
            "warlike": {"intensity": 25, "loudness_pct": 20, "delivery": "Yell"},
            "prophetic": {"intensity": 15, "loudness_pct": 5, "delivery": "Bravado"},
        }
        mod = tone_modifiers.get(new_tone, {})
        if mod:
            defaults = tpl.token_defaults
            base_intensity = defaults.get("intensity", 50)
            base_loudness = defaults.get("loudness_pct", 100)
            defaults["intensity"] = max(0, min(100, base_intensity + mod.get("intensity", 0)))
            defaults["loudness_pct"] = max(0, min(200, base_loudness + mod.get("loudness_pct", 0)))
            if "delivery" in mod:
                defaults["delivery"] = mod["delivery"]
        self._template_store.add_template(tpl)
        self._reference_panel.set_status(f"Tone: {old_tone} -> {new_tone}")
        self._console.log(f"Template '{template_name}' tone switched: {old_tone} -> {new_tone}")

    def _on_create_from_template(self, name: str) -> None:
        tpl = self._template_store.get_template(name)
        if not tpl:
            self._console.log(f"Template '{name}' not found")
            return
        lyrics, ok = QInputDialog.getMultiLineText(
            self, "New Song Lyrics",
            f"Enter lyrics for new song (template: {name}):",
        )
        if not ok or not lyrics.strip():
            return
        self._push_undo()
        self._lyrics_panel.set_lyrics_text(lyrics)
        self._on_tokenize(lyrics)
        self._sync_project()
        count = self._apply_template_to_tokens(tpl)
        self._project.tempo = int(tpl.tempo_estimate)
        self._global_controls.set_tempo(int(tpl.tempo_estimate))
        self._reference_panel.set_status(f"New song from '{name}': {count} tokens")
        self._console.log(f"New song created from template '{name}': {count} tokens, "
                          f"tempo={tpl.tempo_estimate}")

    def _on_create_from_family(self, template_name: str) -> None:
        tpl = self._template_store.get_template(template_name)
        if not tpl or not tpl.template_family:
            self._console.log("Select a template that belongs to a family")
            return
        family_name = tpl.template_family
        summary = self._template_store.get_family_summary(family_name)
        if not summary:
            self._console.log(f"Family '{family_name}' has no data")
            return
        lyrics, ok = QInputDialog.getMultiLineText(
            self, "New Song Lyrics",
            f"Enter lyrics for new song (family: {family_name}):",
        )
        if not ok or not lyrics.strip():
            return
        self._push_undo()
        self._lyrics_panel.set_lyrics_text(lyrics)
        self._on_tokenize(lyrics)
        self._sync_project()
        tokens = self._project.tokens
        if not tokens:
            return
        tempo_mean = summary.get("tempo_range", {}).get("mean", 120.0)
        intensity_mean = summary.get("intensity_distribution", {}).get("mean", 50.0)
        delivery_avg = summary.get("delivery_tendencies", {})
        best_delivery = "Normal"
        best_ratio = 0.0
        for d, ratio in delivery_avg.items():
            if ratio > best_ratio:
                best_ratio = ratio
                best_delivery = d
        count = 0
        for tok in tokens:
            tok.duration_ms = tpl.token_defaults.get("duration_ms", 500)
            tok.loudness_pct = tpl.token_defaults.get("loudness_pct", 100)
            tok.intensity = int(intensity_mean)
            tok.pitch_offset = tpl.token_defaults.get("pitch_offset", 0)
            tok.delivery = DeliveryMode(best_delivery)
            count += 1
        self._lyrics_panel.display_tokens([t.word for t in tokens])
        self._project.tempo = int(tempo_mean)
        self._global_controls.set_tempo(int(tempo_mean))
        self._reference_panel.set_status(f"New song from family '{family_name}': {count} tokens")
        self._console.log(f"New song from family '{family_name}': {count} tokens, "
                          f"tempo={tempo_mean:.0f}")

    def _on_manage_families(self) -> None:
        families_data = []
        for fam in self._template_store.all_families():
            summary = self._template_store.get_family_summary(fam.name)
            families_data.append({"name": fam.name, "summary": summary})
        tpl_names = self._template_store.list_template_names()
        dlg = FamilyManagerDialog(families_data, tpl_names, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            action = dlg.result_action
            if action == "create":
                fam = TemplateFamily(dlg.result_new_name)
                self._template_store.add_family(fam)
                self._console.log(f"Family created: {fam.name}")
            elif action == "delete":
                self._template_store.remove_family(dlg.result_family_name)
                self._console.log(f"Family deleted: {dlg.result_family_name}")
            elif action == "rename":
                old_fam = self._template_store.get_family(dlg.result_family_name)
                if old_fam:
                    self._template_store.remove_family(dlg.result_family_name)
                    old_fam.name = dlg.result_new_name
                    self._template_store.add_family(old_fam)
                    self._console.log(f"Family renamed: {dlg.result_family_name} -> {dlg.result_new_name}")
            elif action == "assign":
                self._template_store.assign_to_family(
                    dlg.result_template_name, dlg.result_family_name,
                )
                self._console.log(f"Assigned '{dlg.result_template_name}' to family '{dlg.result_family_name}'")
            self._reference_panel.set_templates(self._template_store.list_template_names())

    def _on_export_training_pack(self) -> None:
        import json as _json
        self._sync_project()
        if not self._project.project_folder:
            self._console.log("Training Pack: no project folder. Use Save As first.")
            return
        pack_dir = os.path.join(self._project.project_folder, "exports", "training_pack")

        vocal_path = ""
        if self._ref_stem_path and os.path.isfile(self._ref_stem_path):
            vocal_path = self._ref_stem_path
        elif self._ref_audio_path and os.path.isfile(self._ref_audio_path):
            vocal_path = self._ref_audio_path
        elif self._imported_audio_path and os.path.isfile(self._imported_audio_path):
            vocal_path = self._imported_audio_path

        items = ["none", "line", "phrase"]
        seg, ok = QInputDialog.getItem(
            self, "Segmentation", "Segment audio by:", items, 0, False,
        )
        if not ok:
            return

        performer, ok2 = QInputDialog.getText(
            self, "Performer", "Performer name (optional):",
        )
        if not ok2:
            performer = ""

        notes, ok3 = QInputDialog.getText(
            self, "Notes", "Export notes (optional):",
        )
        if not ok3:
            notes = ""

        script = self._build_performance_script()

        ref_tpl_dict: dict | None = None
        selected_tpl = self._reference_panel.get_selected_template()
        if selected_tpl:
            tpl_obj = self._template_store.get_template(selected_tpl)
            if tpl_obj:
                ref_tpl_dict = tpl_obj.to_dict()
        if ref_tpl_dict is None and self._project.project_folder:
            tpl_path = os.path.join(self._project.project_folder, "exports", "reference_template.json")
            if os.path.isfile(tpl_path):
                with open(tpl_path, "r", encoding="utf-8") as f:
                    ref_tpl_dict = _json.load(f)

        self._console.log(f"Exporting training pack to {pack_dir}...")
        manifest = self._training_exporter.export(
            output_dir=pack_dir,
            vocal_path=vocal_path,
            alignment=self._last_alignment,
            performance_script=script,
            reference_template=ref_tpl_dict,
            performer_name=performer.strip(),
            notes=notes.strip(),
            segmentation=seg,
        )
        file_count = manifest.get("file_count", 0)
        self._log.info(f"Training pack exported: {pack_dir} ({file_count} files)")
        self._console.log(f"Training pack exported: {file_count} files to {pack_dir}")

    def _on_world_navigator(self) -> None:
        dlg = WorldNavigatorDialog(self)
        dlg.workspace_selected.connect(self._on_world_workspace_selected)
        dlg.exec()

    def _on_world_workspace_selected(self, workspace_id: str) -> None:
        book_idx = WORKSPACE_BOOK_MAP.get(workspace_id, 0)
        self._switch_to_book(book_idx)
        self._console.log(f"Navigator: switched to {workspace_id}")

    def _on_instrument_changed(self, text: str) -> None:
        if text.startswith("(None"):
            self._active_instrument = None
            self._audio_synth.set_instrument_patch(None)
            self._preview_engine.invalidate_cache()
            self._console.log("Instrument: None (using Voice Type)")
            return
        inst = self._instrument_store.get(text)
        if inst:
            self._active_instrument = inst
            self._audio_synth.set_instrument_patch(inst.to_dict())
            self._preview_engine.invalidate_cache()
            self._console.log(f"Instrument: {inst.name}")

    def _on_instrument_edit(self) -> None:
        inst = self._active_instrument
        if not inst:
            QMessageBox.information(self, "No Instrument", "Select an instrument first.")
            return
        dlg = InstrumentEditorDialog(inst, self)
        dlg.audition_requested.connect(self._on_instrument_audition)
        if dlg.exec() == InstrumentEditorDialog.DialogCode.Accepted:
            updated = dlg.get_patch()
            self._instrument_store.add(updated)
            self._active_instrument = updated
            self._audio_synth.set_instrument_patch(updated.to_dict())
            self._refresh_instrument_combo(updated.name)
            self._console.log(f"Instrument updated: {updated.name}")

    def _on_instrument_audition(self, patch_dict: dict) -> None:
        self._audio_synth.set_instrument_patch(patch_dict)
        if self._project.tokens and 0 <= self._selected_token_idx < len(self._project.tokens):
            token_dict = self._project.tokens[self._selected_token_idx].to_dict()
            result = self._preview_engine.preview_token(token_dict)
            if result.audio_data:
                self._audio_player.play_bytes(result.audio_data)
        if self._active_instrument:
            self._audio_synth.set_instrument_patch(self._active_instrument.to_dict())
        else:
            self._audio_synth.set_instrument_patch(None)

    def _on_instrument_save_as(self) -> None:
        src = self._active_instrument
        if not src:
            src = InstrumentPatch("New Instrument")
        dlg = InstrumentEditorDialog(src, self)
        dlg.audition_requested.connect(self._on_instrument_audition)
        if dlg.exec() == InstrumentEditorDialog.DialogCode.Accepted:
            new_patch = dlg.get_patch()
            self._instrument_store.add(new_patch)
            self._active_instrument = new_patch
            self._audio_synth.set_instrument_patch(new_patch.to_dict())
            self._refresh_instrument_combo(new_patch.name)
            self._console.log(f"Instrument saved: {new_patch.name}")

    def _on_instrument_duplicate(self) -> None:
        if not self._active_instrument:
            QMessageBox.information(self, "No Instrument", "Select an instrument first.")
            return
        clone = self._active_instrument.clone()
        self._instrument_store.add(clone)
        self._refresh_instrument_combo(clone.name)
        self._console.log(f"Instrument duplicated: {clone.name}")

    def _on_instrument_delete(self) -> None:
        if not self._active_instrument:
            return
        name = self._active_instrument.name
        from models.instrument_patch import BUILTIN_INSTRUMENTS
        if name in {bi.name for bi in BUILTIN_INSTRUMENTS}:
            QMessageBox.warning(self, "Cannot Delete", "Built-in instruments cannot be deleted.")
            return
        self._instrument_store.remove(name)
        self._active_instrument = None
        self._audio_synth.set_instrument_patch(None)
        self._refresh_instrument_combo("")
        self._console.log(f"Instrument deleted: {name}")

    def _refresh_instrument_combo(self, select_name: str) -> None:
        self._instrument_combo.blockSignals(True)
        self._instrument_combo.clear()
        self._instrument_combo.addItem("(None \u2014 use Voice Type)")
        for n in self._instrument_store.list_names():
            self._instrument_combo.addItem(n)
        if select_name:
            idx = self._instrument_combo.findText(select_name)
            if idx >= 0:
                self._instrument_combo.setCurrentIndex(idx)
        self._instrument_combo.blockSignals(False)
