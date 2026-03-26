# Kingdom Digital Systems - Lyric Performance Engine: Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [File & Folder Structure](#file--folder-structure)
3. [Module Dependency Map](#module-dependency-map)
4. [Audio Engine Signal Flow](#audio-engine-signal-flow)
5. [Data Models](#data-models)
6. [Engine Components](#engine-components)
7. [UI Components](#ui-components)
8. [Core Services](#core-services)
9. [Persistence Layer](#persistence-layer)
10. [Extension Points](#extension-points)

---

## System Overview

The Lyric Performance Engine is a modular desktop application built on PySide6. It follows a layered architecture:

```
┌─────────────────────────────────────────────────┐
│                   UI Layer                       │
│  (main_window, panels, dialogs, popover)        │
├─────────────────────────────────────────────────┤
│                Engine Layer                       │
│  (preview_engine, audio_synth, dsp_analyzer,    │
│   alignment_engine, template_extractor,          │
│   training_pack_exporter)                        │
├─────────────────────────────────────────────────┤
│                Model Layer                        │
│  (token_model, project_model, voice_profile,    │
│   style_preset, track_model, render_job,         │
│   reference_template, instrument_patch)           │
├─────────────────────────────────────────────────┤
│                Core Layer                         │
│  (tokenizer, undo_manager, singer_router,       │
│   logger, fix_registry)                          │
└─────────────────────────────────────────────────┘
```

**Key Principles:**
- No external audio/ML dependencies (PySide6 only)
- All synthesis is real-time, sample-by-sample
- JSON-based persistence everywhere
- Engines are stateless functions; state lives in models
- UI is additive-only (never removes existing panels)

---

## File & Folder Structure

```
lyric-performance-engine/
│
├── main.py                          # Application entry point
│
├── core/                            # Core services (no UI, no engine deps)
│   ├── tokenizer.py                 # Lyrics text -> TokenModel list
│   ├── undo_manager.py              # Undo/redo stack for project state
│   ├── singer_router.py             # Routes voice profile to preview engine
│   ├── logger.py                    # Central logging, crash reports, debug bundles
│   └── fix_registry.py              # Error fingerprinting, fix lookup, fix packs
│
├── models/                          # Data models (serializable, no side effects)
│   ├── __init__.py
│   ├── token_model.py               # TokenModel, DeliveryMode, BravadoSubtype, BoundaryMarker
│   ├── project_model.py             # ProjectModel (top-level project state)
│   ├── voice_profile.py             # VoiceProfile, VoiceModelManager
│   ├── style_preset.py              # StylePreset, StylePresetStore, feature vectors
│   ├── track_model.py               # TrackModel, TrackAssignment, TrackType
│   ├── render_job.py                # RenderJob, RenderTarget, RenderStatus
│   ├── reference_template.py        # ReferenceTemplate, TemplateFamily, TemplateFamilyStore
│   └── instrument_patch.py          # InstrumentPatch, InstrumentStore
│
├── engines/                         # Audio processing engines
│   ├── __init__.py
│   ├── preview_engine.py            # PreviewEngine, PreviewSynthesizer (ABC), PreviewCache
│   ├── audio_synth.py               # AudioPreviewSynthesizer, vocal/piano/instrument synthesis
│   ├── audio_player.py              # WAV playback via QMediaPlayer
│   ├── audio_recorder.py            # Microphone recording to WAV
│   ├── dsp_analyzer.py              # DSPAnalyzer, TokenParameterMapper
│   ├── alignment_engine.py          # Energy-based forced alignment
│   ├── template_extractor.py        # Extract ReferenceTemplate from alignment + DSP
│   └── training_pack_exporter.py    # Export aligned audio + lyrics for training
│
├── ui/                              # UI components (PySide6 widgets)
│   ├── theme.py                     # ThemeManager (dark/light CSS)
│   ├── lyrics_panel.py              # LyricsPanel (text input + token list)
│   ├── inspector_panel.py           # InspectorPanel (token parameter sliders)
│   ├── console_panel.py             # ConsolePanel (scrollable log output)
│   ├── global_controls_panel.py     # GlobalControlsPanel (tempo, key, voice type)
│   ├── selection_popover.py         # SelectionPopover (range edit controls)
│   ├── capture_panel.py             # CapturePanel (record, import, analyze, apply)
│   ├── tracks_panel.py              # TracksPanel (track list + routing)
│   ├── render_panel.py              # RenderPanel (job queue + controls)
│   ├── import_panel.py              # ImportPanel (audio import + alignment)
│   ├── reference_panel.py           # ReferencePanelUI, FamilyManagerDialog
│   ├── world_navigator.py           # SphereWidget, WorldNavigatorDialog
│   ├── instrument_editor.py         # InstrumentEditorDialog
│   └── main_window.py               # MainWindow (top-level orchestrator, ~2900 lines)
│
├── docs/                            # Documentation
│   ├── USER_MANUAL.md
│   ├── ARCHITECTURE.md
│   ├── QUICK_START.md
│   ├── user_manual.md               # (legacy)
│   ├── quick_start.md               # (legacy)
│   ├── composer_workflows.md
│   ├── troubleshooting.md
│   └── architecture.md              # (legacy)
│
├── logs/                            # Runtime logs (gitignored)
│   ├── app.log
│   └── crashes/
│
├── solutions_and_learning/          # Fix registry + solution folders (runtime)
│   └── fix_registry.json
│
├── exports/                         # Debug bundles, fix packs (runtime)
│
└── live/                            # Live session data (runtime)
```

---

## Module Dependency Map

```
main.py
  └── ui/main_window.py (MainWindow)
        ├── core/tokenizer.py
        ├── core/undo_manager.py
        ├── core/singer_router.py
        ├── core/logger.py
        ├── core/fix_registry.py
        │
        ├── models/project_model.py
        │     ├── models/token_model.py
        │     └── models/track_model.py
        ├── models/voice_profile.py
        ├── models/style_preset.py
        ├── models/render_job.py
        ├── models/reference_template.py
        ├── models/instrument_patch.py
        │
        ├── engines/preview_engine.py
        │     └── (defines PreviewSynthesizer ABC)
        ├── engines/audio_synth.py
        │     └── (implements PreviewSynthesizer)
        ├── engines/audio_player.py
        ├── engines/audio_recorder.py
        ├── engines/dsp_analyzer.py
        ├── engines/alignment_engine.py
        │     └── engines/dsp_analyzer.py
        ├── engines/template_extractor.py
        │     └── engines/dsp_analyzer.py
        ├── engines/training_pack_exporter.py
        │
        ├── ui/lyrics_panel.py
        ├── ui/inspector_panel.py
        ├── ui/console_panel.py
        ├── ui/global_controls_panel.py
        ├── ui/selection_popover.py
        ├── ui/capture_panel.py
        ├── ui/tracks_panel.py
        ├── ui/render_panel.py
        ├── ui/import_panel.py
        ├── ui/reference_panel.py
        ├── ui/world_navigator.py
        └── ui/instrument_editor.py
```

---

## Audio Engine Signal Flow

### Token-to-Audio Pipeline

```
                    ┌──────────────┐
                    │  User Action │
                    │ (click Play  │
                    │  or slider)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ MainWindow   │
                    │ _on_preview()│
                    └──────┬───────┘
                           │
          ┌────────────────▼────────────────┐
          │     _build_preview_sequence()    │
          │                                  │
          │  Inputs:                         │
          │  - selected token index          │
          │  - scope (Word/From/Line/Sect)   │
          │  - mode (Single/Forward)         │
          │  - pre-roll / post-roll          │
          │                                  │
          │  Output: list[token_dict]        │
          └────────────────┬────────────────┘
                           │
          ┌────────────────▼────────────────┐
          │        PreviewEngine             │
          │                                  │
          │  preview_token() or              │
          │  preview_phrase()                 │
          │                                  │
          │  ┌──────────────────────────┐    │
          │  │     PreviewCache         │    │
          │  │  key: index:voice:qual:  │    │
          │  │       params_hash        │    │
          │  │  Hit? Return cached      │    │
          │  └──────────┬───────────────┘    │
          │             │ Miss               │
          └─────────────┼───────────────────┘
                        │
          ┌─────────────▼───────────────────┐
          │   AudioPreviewSynthesizer       │
          │                                  │
          │   Priority chain:                │
          │   1. InstrumentPatch set?        │
          │      → _synthesize_instrument()  │
          │   2. Voice = Muted Piano?        │
          │      → _synthesize_muted_piano() │
          │   3. Otherwise                   │
          │      → _synthesize_vocal()       │
          └─────────────┬───────────────────┘
                        │
          ┌─────────────▼───────────────────┐
          │     Synthesis Functions          │
          │                                  │
          │  Per-sample loop:                │
          │  ┌─────────────────────────┐     │
          │  │  1. ADSR Envelope       │     │
          │  │  2. Harmonic Oscillator │     │
          │  │     Bank (sin waves)    │     │
          │  │  3. Formant Filter      │     │
          │  │     (vocal only)        │     │
          │  │  4. Vibrato Modulation  │     │
          │  │  5. Noise Mix           │     │
          │  │  6. Lowpass Filter      │     │
          │  │  7. Transient Click     │     │
          │  │     (instrument only)   │     │
          │  │  8. Amplitude Scaling   │     │
          │  └─────────────────────────┘     │
          │                                  │
          │  Output: list[float] samples     │
          └─────────────┬───────────────────┘
                        │
          ┌─────────────▼───────────────────┐
          │        _write_wav()              │
          │  Converts float samples to       │
          │  16-bit PCM WAV bytes            │
          │  (44100 Hz, mono)                │
          └─────────────┬───────────────────┘
                        │
          ┌─────────────▼───────────────────┐
          │     PreviewResult                │
          │  .audio_data = WAV bytes         │
          │  .duration_ms                    │
          │  .quality                        │
          │  .cached = False                 │
          └─────────────┬───────────────────┘
                        │
          ┌─────────────▼───────────────────┐
          │       AudioPlayer                │
          │  Writes WAV to temp file         │
          │  Plays via QMediaPlayer          │
          └─────────────────────────────────┘
```

### Vocal Synthesis Detail

```
Token Parameters ──────────────────────────────────┐
  word, duration_ms, loudness_pct,                 │
  intensity, pitch_offset, delivery                │
                                                    │
Voice Context ─────────────────────────────────────┤
  voice_type (Male/Female/Robot/FamilyBathroom)    │
  voice_profile_id (default/singer_a/b/c)          │
                                                    ▼
┌──────────────────────────────────────────────────────┐
│                 _synthesize_vocal()                    │
│                                                        │
│  1. Base frequency = VOICE_TYPE_BASE_FREQ[type]       │
│     + SINGER_FREQ_OFFSETS[profile]                    │
│     * 2^(pitch_offset/12)                             │
│     * word_hash_variation (+-0.8%)                    │
│                                                        │
│  2. Detect vowel from word text → formant set         │
│     FORMANTS[voice_type][vowel] →                     │
│     [(freq, bandwidth, amplitude), ...]               │
│                                                        │
│  3. Delivery params → amplitude, noise_mix,           │
│     harmonic_count, harmonic_decay                    │
│                                                        │
│  4. Per-harmonic gain = rolloff * formant_gain        │
│     formant_gain = Gaussian(harmonic_freq, formant)   │
│                                                        │
│  5. Per-sample:                                       │
│     envelope = attack/sustain/release trapezoid       │
│     vibrato = 1 + depth * sin(2pi * rate * t)        │
│     sample = SUM(sin(phase[h]) * gain[h])             │
│     + filtered_noise * noise_mix                      │
│     * envelope * amplitude                            │
│                                                        │
│  6. Robot voice: square wave blend + soft clipping    │
│                                                        │
│  Output: list[float] (44100 samples/sec)              │
└──────────────────────────────────────────────────────┘
```

### Instrument Synthesis Detail

```
Token Parameters + InstrumentPatch ────────────────┐
  word, duration_ms, loudness_pct,                 │
  intensity, pitch_offset                           │
  + patch_dict (17 parameters)                      │
                                                    ▼
┌──────────────────────────────────────────────────────┐
│              _synthesize_instrument()                  │
│                                                        │
│  1. ADSR Envelope (from patch):                       │
│     attack_ms → linear ramp                           │
│     decay_ms → linear decay to sustain_level          │
│     sustain_level → held level                        │
│     release_ms → linear fade to 0                     │
│                                                        │
│  2. Harmonic oscillator bank:                         │
│     Per-harmonic gain =                               │
│       harmonics_level^h * brightness_cut * damp_cut   │
│     damp_cut = exp(-h * damping * 0.3)                │
│                                                        │
│  3. Vibrato (if default_vibrato_on):                  │
│     freq *= 1 + 0.005 * sin(2pi * 5 * t)             │
│                                                        │
│  4. Transient click (first 5ms):                      │
│     noise * transient_click * click_envelope * 2      │
│                                                        │
│  5. Noise layer:                                      │
│     sample = sample * (1 - noise_amount)              │
│            + pseudo_noise * noise_amount               │
│                                                        │
│  6. Envelope-controlled lowpass filter:               │
│     cutoff starts at lowpass_hz                        │
│     decays to lowpass_hz * 0.15                       │
│     decay rate = decay_ms * (1 + damping)             │
│     One-pole IIR: y[n] = y[n-1] + alpha*(x-y[n-1])  │
│                                                        │
│  7. Final: sample * envelope * amplitude              │
│                                                        │
│  Output: list[float] (44100 samples/sec)              │
└──────────────────────────────────────────────────────┘
```

### DSP Analysis Pipeline

```
WAV File ──→ _read_wav_mono() ──→ float samples
                                       │
                    ┌──────────────────┘
                    ▼
          DSPAnalyzer.analyze_samples()
                    │
    ┌───────────────┼───────────────────────────┐
    │               │                           │
    ▼               ▼                           ▼
 _compute_rms   _estimate_pitch         _spectral_centroid
 _compute_peak  _with_confidence        _spectral_rolloff
                    │                   _envelope_duration
                    ▼
            _estimate_vibrato
            _with_confidence
                    │
                    ▼
          DSPAnalysisResult
          (12 fields + 3 confidence scores)
                    │
                    ▼
          TokenParameterMapper.map_to_params()
                    │
                    ▼
          {loudness_pct, intensity, pitch_offset,
           duration_ms, delivery}
```

---

## Data Models

### TokenModel

The atomic unit. Each word in the lyrics becomes a TokenModel.

```
TokenModel
├── word: str              # The word text
├── index: int             # Position in lyrics
├── duration_ms: int       # 50-5000, default 500
├── loudness_pct: int      # 0-200, default 100
├── intensity: int         # 0-100, default 50
├── pitch_offset: int      # -24 to +24 semitones
├── delivery: DeliveryMode # Whisper/Normal/Yell/Scream/Bravado
├── bravado_subtype        # Confident/Aggressive/Triumphant/Defiant
├── boundary_after         # Normal/Hard Stop/Powerful Start
├── locked: bool           # Whether params are committed
└── line_index: int        # Which lyrics line this belongs to
```

### ProjectModel

Top-level container for all session state.

```
ProjectModel
├── lyrics: str
├── tokens: list[TokenModel]
├── render_mode, engine_quality, auto_preview
├── singer, personality, personality_mix
├── tempo, key, theme
├── preview_mode
├── project_folder, folder_based
├── active_book
├── tracks: list[TrackModel]
└── track_assignments: list[TrackAssignment]
```

### InstrumentPatch

Reusable synthesis parameter set.

```
InstrumentPatch
├── name: str
├── created_at: float
├── Envelope: attack_ms, decay_ms, sustain_level, release_ms
├── Timbre: damping, harmonics_level, lowpass_hz, brightness
├── Noise: noise_amount, transient_click
└── Token Defaults: duration_ms_min/max, intensity, delivery_mode, vibrato_on
```

### TrackModel

DAW-style track for separating singers/instruments.

```
TrackModel
├── id: str (UUID hex)
├── name: str
├── track_type: TrackType (VOCAL/INSTRUMENT/MASTER)
├── voice_profile_id: str
├── enabled: bool
├── solo: bool
└── color: str
```

---

## Engine Components

### PreviewEngine

Central coordinator. Holds a synthesizer reference, a cache, quality setting, and voice profile ID.

- `preview_token(token_data)` - Single token render with caching
- `preview_phrase(tokens)` - Multi-token render (no caching)
- `invalidate_cache()` - Clears all cached results

### AudioPreviewSynthesizer

Implements `PreviewSynthesizer` ABC. Contains the synthesis priority chain:

1. If `_instrument_patch` is set -> `_synthesize_instrument()`
2. Else if voice type is "Muted Percussive Piano" -> `_synthesize_muted_piano()`
3. Else -> `_synthesize_vocal()` with formant filtering

### DSPAnalyzer

Pure DSP analysis from WAV samples:
- Autocorrelation pitch detection with confidence scoring
- Vibrato detection via pitch-track zero-crossing analysis
- DFT-based spectral centroid and rolloff
- Energy envelope duration measurement

### AlignmentEngine

Energy-based forced alignment:
1. Compute energy envelope (10ms hop)
2. Find energy boundaries (15% threshold)
3. Map words to energy regions (proportional if fewer regions than words)
4. Fallback: uniform distribution if no energy detected

---

## UI Components

### MainWindow (~2900 lines)

The orchestrator. Contains:
- All toolbar construction
- All signal connections (~130 connections)
- All handler methods (~100 methods)
- Book/chapter navigation
- Auto-save timer

### Panel Architecture

Each panel is a self-contained QWidget:

| Panel | Signals Out | Slots In |
|-------|-------------|----------|
| LyricsPanel | token_selected, range_selected, selection_cleared | set_tokens, set_token_locked |
| InspectorPanel | (value changes via MainWindow) | set_token_data |
| CapturePanel | record, stop, import, analyze, apply signals | set_recording, set_analysis, set_status |
| TracksPanel | track_selected | set_tracks |
| RenderPanel | run_selected, run_all, cancel | set_jobs, update_job_status |
| ImportPanel | import_audio, run_alignment, auto_fill | set_tracks |
| ReferencePanelUI | various template/family signals | set_templates, set_families |

### WorldNavigatorDialog

Modal dialog with:
- `SphereWidget` - Custom QPainter widget rendering a shaded circle with lat/lon grid
- Mouse drag rotates via `lon_offset` and `lat_offset`
- 5 workspace hotspots projected from 3D (lon,lat) to 2D screen coordinates
- Search QLineEdit filters workspace buttons
- Signal: `workspace_selected(str)` emits workspace ID

### InstrumentEditorDialog

Form dialog with:
- QSlider controls for all 17 InstrumentPatch parameters
- Live readout labels
- Audition button (signal: `audition_requested(dict)`)
- OK/Cancel via QDialogButtonBox

---

## Core Services

### Tokenizer

Stateless. Splits text into `TokenModel` list. Assigns `line_index` based on newlines.

`apply_repeat_inheritance()` - When a word appears multiple times and the first occurrence is locked, later occurrences copy its parameters.

### UndoManager

Stack-based undo/redo. Stores project state dicts. Used by MainWindow after every parameter change.

### SingerRouter

Bridges `VoiceModelManager` and `PreviewEngine`. When singer changes, updates the voice profile ID on the engine.

### Logger

- Rotating file handler (2MB, 5 backups) at `logs/app.log`
- Console handler (INFO level)
- `write_crash_report()` - Captures exception + system info + app state
- `write_solution_folder()` - Creates structured issue folder
- `export_debug_bundle()` - Zips logs + crashes + solutions

### Fix Registry

- `compute_fingerprint()` - SHA-256 of normalized error type + message + top 3 stack frames
- `lookup_fix()` / `save_fix()` - JSON-based known-issue database
- `export_fix_pack()` / `import_fix_pack()` - Portable fix sharing via zip

---

## Persistence Layer

All persistence uses JSON. No database.

| Data | Format | Location |
|------|--------|----------|
| Project state | Single JSON file | User-chosen path or `~/.kds_lpe/autosave.json` |
| Style presets | One JSON per preset | `~/.kds_lpe/style_presets/` |
| Instruments (global) | One JSON per instrument | `~/.kds_lpe/instruments/` |
| Instruments (project) | One JSON per instrument | `<project>/instruments/` |
| Reference templates | One JSON per template | `~/.kds_lpe/reference_templates/templates/` |
| Template families | One JSON per family | `~/.kds_lpe/reference_templates/families/` |
| Fix registry | Single JSON file | `solutions_and_learning/fix_registry.json` |
| Logs | Rotating text files | `logs/` |
| Crash reports | Text files | `logs/crashes/` |
| Backups | Timestamped JSON copies | `~/.kds_lpe/backups/` |

---

## Extension Points

### Pluggable Synthesizer

`PreviewSynthesizer` is an abstract base class. To add a new synthesis backend:

1. Subclass `PreviewSynthesizer`
2. Implement `synthesize_token()`, `synthesize_phrase()`, `supports_quality()`
3. Call `preview_engine.set_synthesizer(your_synth)`

### Pluggable Alignment

`AlignmentEngine.forced_align()` currently uses energy-based alignment. To add ML alignment (e.g., Whisper):

1. Subclass or modify `AlignmentEngine`
2. Implement `forced_align()` with the same return type (`AlignmentResult`)
3. The UI handler in MainWindow calls the same interface

### Custom Voice Types

Add entries to `FORMANTS`, `VOICE_TYPE_BASE_FREQ`, and `VOICE_TYPES` in `engines/audio_synth.py`. Add to the dropdown in `ui/global_controls_panel.py`.

### Custom Instruments

Create a JSON file in `~/.kds_lpe/instruments/` with the InstrumentPatch format (see USER_MANUAL.md). It will appear in the Instrument dropdown on next launch.

### Custom Emotional Tones

Add via the Reference Templates UI or directly to `~/.kds_lpe/reference_templates/custom_tones.json`.
