# Kingdom Digital Systems — Lyric Performance Engine

A cross-platform desktop application for composing, editing, and previewing vocal and instrumental performances from lyric text. Built with Python and PySide6 (Qt), it runs fully offline with no external dependencies beyond PySide6.

## Features

- **Lyric Tokenizer** — Break lyric text into word-level tokens with per-word duration, loudness, intensity, pitch, and delivery controls
- **Voice Model System** — Male, Female, Robot, and Family Bathroom voice types with harmonic oscillator + formant filtering synthesis
- **Audio Preview** — Real-time vocal-like audio preview with DAW-style controls (scope, context, pre/post-roll)
- **Performance Capture** — Record live performances with microphone, analyze with DSP, and auto-extract token parameters
- **Style Presets** — Save and match performance parameter sets with confidence scoring
- **Track-Based Song Builder** — Multi-singer tracks (Vocal, Instrument, Master) with mute/solo routing
- **Reference Templates** — Import reference audio, extract DSP-based templates with 8 emotional tones (loving, compassionate, reverent, sorrowful, joyful, triumphant, warlike, prophetic)
- **Instrument System** — Muted Piano and custom instrument patches with ADSR envelope, damping, harmonics, and noise controls
- **World Navigator** — Visual globe workspace switcher
- **Render Queue** — Export performance scripts and render audio
- **Import & Alignment** — Import songs, align lyrics to audio using energy-based forced alignment
- **Voice Training Export** — Export aligned audio + lyrics datasets for voice model training
- **Project Management** — Auto-save (60s), session restore, Save As with timestamped backups, folder-based projects
- **Fix Registry** — Error fingerprinting, known-issue detection, and fix database
- **Debug Tools** — Crash reporting, debug bundle export, solution learning folders

## Quick Start

### Prerequisites

- Python 3.10 or later
- PySide6

### Install & Run

```bash
pip install -r requirements.txt
python main.py
```

The main window opens with the Composition book active. See [docs/quick_start.md](docs/quick_start.md) for a 5-minute walkthrough.

## Project Structure

```
kingdom-digital-systems/
├── main.py                  # Entry point + global exception handler
├── core/                    # Core services
│   ├── tokenizer.py         # Lyric text → token list
│   ├── undo_manager.py      # Undo/redo state stack
│   ├── logger.py            # Logging, crash reports, debug bundles
│   ├── fix_registry.py      # Error fingerprinting + fix database
│   └── singer_router.py     # Singer/voice profile routing
├── engines/                 # Audio & analysis engines
│   ├── base_engine.py       # Abstract engine interface
│   ├── preview_engine.py    # Preview synthesis orchestration
│   ├── audio_synth.py       # Harmonic oscillator + formant filtering
│   ├── audio_player.py      # Cross-platform WAV playback
│   ├── audio_recorder.py    # Microphone capture
│   ├── dsp_analyzer.py      # RMS, pitch, vibrato, spectral analysis
│   ├── alignment_engine.py  # Energy-based forced alignment
│   ├── template_extractor.py# Reference template extraction
│   ├── training_pack_exporter.py # Voice training dataset export
│   ├── live_engine.py       # Live performance engine
│   ├── convert_engine.py    # Format conversion
│   ├── synthesis_engine.py  # Full synthesis pipeline
│   └── assist_engine.py     # AI-assist engine
├── models/                  # Data models
│   ├── token_model.py       # Token (duration, loudness, delivery, etc.)
│   ├── project_model.py     # Full project state + JSON persistence
│   ├── voice_profile.py     # VoiceProfile + VoiceModelManager
│   ├── style_preset.py      # StylePreset + StylePresetStore
│   ├── track_model.py       # TrackModel, TrackAssignment, TrackType
│   ├── render_job.py        # RenderJob, RenderTarget, RenderStatus
│   ├── reference_template.py# ReferenceTemplate + TemplateFamily
│   └── instrument_patch.py  # Instrument patch editor data model
├── ui/                      # PySide6 UI panels
│   ├── main_window.py       # Main window orchestration
│   ├── lyrics_panel.py      # Lyrics input + FlowLayout token display
│   ├── inspector_panel.py   # Duration/Loudness/Intensity/Pitch sliders
│   ├── console_panel.py     # Collapsible log panel
│   ├── global_controls_panel.py # Tempo, Key, Voice Type, Instruments
│   ├── selection_popover.py # Range selection popover
│   ├── capture_panel.py     # Record/Import/Analyze/Preset creation
│   ├── tracks_panel.py      # Track list, mute/solo, export stems
│   ├── render_panel.py      # Render queue UI
│   ├── import_panel.py      # Import audio + alignment + auto-fill
│   ├── reference_panel.py   # Reference import + template extraction
│   ├── theme.py             # Dark/Light theme stylesheets
│   ├── instrument_editor.py # Instrument patch editor UI
│   └── world_navigator.py   # Globe workspace navigator
├── live/                    # Live performance module
├── docs/                    # Documentation
│   ├── architecture.md      # System architecture
│   ├── user_manual.md       # Full user manual
│   ├── quick_start.md       # 5-minute beginner guide
│   ├── composer_workflows.md# Multi-song set workflows
│   ├── troubleshooting.md   # Common issues and fixes
│   └── tooltips.md          # UI tooltip reference
└── requirements.txt         # Python dependencies
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [User Manual](docs/user_manual.md)
- [Quick Start Guide](docs/quick_start.md)
- [Composer Workflows](docs/composer_workflows.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Tooltip Reference](docs/tooltips.md)

## License

Proprietary. All rights reserved.
